import json
from typing import Any, Dict, List

from django.conf import settings
from pydantic import BaseModel, Field, ValidationError, field_validator

from . import prompts
from .utils import parse_agent_json


class EvaluationScores(BaseModel):
    groundedness: int = Field(ge=0, le=100)
    citation_coverage: int = Field(ge=0, le=100)
    quiz_quality: int = Field(ge=0, le=100)
    tutoring_value: int = Field(ge=0, le=100)
    learner_fit: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)


class LearnerExperience(BaseModel):
    smoothness: str
    cognitive_load: str
    personalization: str


class ReflectionPayload(BaseModel):
    diagnosis: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    should_regenerate: bool = False
    should_expand_retrieval: bool = False
    should_add_multimodal_review: bool = False


class EvaluatorResponse(BaseModel):
    scores: EvaluationScores
    verdict: str
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    learner_experience: LearnerExperience
    reflection: ReflectionPayload

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"pass", "review", "block"}:
            raise ValueError("verdict must be pass, review, or block")
        return normalized


def build_quality_report(
    *,
    client,
    text: str,
    planner_payload: Dict[str, Any],
    final_payload: Dict[str, Any],
    tutor_payload: Dict[str, Any],
    rag_chunks: List[Dict[str, Any]],
    rag_diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    rule_metrics = _compute_rule_metrics(
        planner_payload=planner_payload,
        final_payload=final_payload,
        tutor_payload=tutor_payload,
        rag_chunks=rag_chunks,
        rag_diagnostics=rag_diagnostics,
    )
    user_prompt = _build_user_prompt(
        text=text,
        planner_payload=planner_payload,
        final_payload=final_payload,
        tutor_payload=tutor_payload,
        rule_metrics=rule_metrics,
        rag_diagnostics=rag_diagnostics,
    )
    response = client.chat(
        model=settings.AGENT_SETTINGS["qwen_model"],
        system=prompts.EVALUATOR_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0.1,
    )
    parsed = parse_agent_json(response)
    try:
        validated = EvaluatorResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Evaluator response validation failed: {exc}") from exc

    llm_payload = validated.model_dump()
    return {
        "evaluation": {
            "verdict": llm_payload["verdict"],
            "scores": llm_payload["scores"],
            "rule_metrics": rule_metrics,
            "strengths": llm_payload["strengths"],
            "risks": llm_payload["risks"],
            "missing_evidence": llm_payload["missing_evidence"],
            "learner_experience": llm_payload["learner_experience"],
        },
        "reflection": llm_payload["reflection"],
    }


def _build_user_prompt(
    *,
    text: str,
    planner_payload: Dict[str, Any],
    final_payload: Dict[str, Any],
    tutor_payload: Dict[str, Any],
    rule_metrics: Dict[str, Any],
    rag_diagnostics: Dict[str, Any],
) -> str:
    compact_payload = {
        "lesson_request": text[:1500],
        "planner_title": planner_payload.get("title"),
        "planner_summary": planner_payload.get("summary"),
        "knowledge_points": [
            {
                "title": point.get("title"),
                "summary": point.get("summary"),
                "refs": point.get("refs", []),
            }
            for point in (final_payload.get("knowledge_points") or planner_payload.get("knowledge_points") or [])[:6]
        ],
        "quiz_items": [
            {
                "question": item.get("question"),
                "answer": item.get("answer"),
                "difficulty": item.get("difficulty"),
                "kp_ids": item.get("kp_ids", []),
                "refs": item.get("refs", []),
                "variant_count": len(item.get("variants", []) or []),
            }
            for item in (final_payload.get("quiz", {}).get("items", []) or [])[:6]
        ],
        "tutor": {
            "summary": tutor_payload.get("summary", {}),
            "practice": [
                {
                    "prompt": item.get("prompt"),
                    "reasoning": item.get("reasoning"),
                    "citations": item.get("citations", []),
                }
                for item in (tutor_payload.get("practice") or [])[:4]
            ],
            "followups": (tutor_payload.get("followups") or [])[:5],
        },
        "rule_metrics": rule_metrics,
        "retrieval_diagnostics": rag_diagnostics or {},
    }
    return "请审计以下教学生成结果，重点判断证据充分性、学习丝滑度和下一步系统改进方向：\n" + json.dumps(
        compact_payload, ensure_ascii=False
    )


def _compute_rule_metrics(
    *,
    planner_payload: Dict[str, Any],
    final_payload: Dict[str, Any],
    tutor_payload: Dict[str, Any],
    rag_chunks: List[Dict[str, Any]],
    rag_diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    knowledge_points = final_payload.get("knowledge_points") or planner_payload.get("knowledge_points") or []
    quiz_items = final_payload.get("quiz", {}).get("items", []) or []
    practice_items = tutor_payload.get("practice") or []
    followups = tutor_payload.get("followups") or []
    key_takeaways = tutor_payload.get("summary", {}).get("key_takeaways") or []

    knowledge_ref_count = sum(1 for point in knowledge_points if point.get("refs"))
    quiz_ref_count = sum(1 for item in quiz_items if item.get("refs"))
    quiz_variant_count = sum(1 for item in quiz_items if item.get("variants"))
    practice_citation_count = sum(1 for item in practice_items if item.get("citations"))
    difficulty_mix = len({str(item.get("difficulty", "")).strip() for item in quiz_items if item.get("difficulty")})

    search_k = int(rag_diagnostics.get("search_k", 0) or 0)
    final_hits = int(rag_diagnostics.get("final_hits", 0) or 0)
    vector_hits = int(rag_diagnostics.get("vector_hits", 0) or 0)
    lexical_hits = int(rag_diagnostics.get("lexical_hits", 0) or 0)
    source_counts = rag_diagnostics.get("source_counts") or {}

    knowledge_ref_ratio = _ratio(knowledge_ref_count, len(knowledge_points))
    quiz_ref_ratio = _ratio(quiz_ref_count, len(quiz_items))
    quiz_variant_ratio = _ratio(quiz_variant_count, len(quiz_items))
    practice_citation_ratio = _ratio(practice_citation_count, len(practice_items))
    retrieval_fill_ratio = _ratio(final_hits, search_k) if search_k else 0

    groundedness_score = round(
        0.4 * knowledge_ref_ratio
        + 0.35 * quiz_ref_ratio
        + 0.15 * practice_citation_ratio
        + 0.1 * retrieval_fill_ratio
    )
    citation_coverage_score = round(0.45 * knowledge_ref_ratio + 0.4 * quiz_ref_ratio + 0.15 * practice_citation_ratio)
    quiz_quality_score = round(
        0.5 * _ratio(len(quiz_items), 4)
        + 0.25 * quiz_variant_ratio
        + 0.25 * _ratio(difficulty_mix, 3)
    )
    tutoring_value_score = round(
        0.45 * practice_citation_ratio
        + 0.3 * _ratio(len(followups), 3)
        + 0.25 * _ratio(len(key_takeaways), 3)
    )
    learner_fit_score = round(
        0.35 * _ratio(len(practice_items), 2)
        + 0.35 * _ratio(len(followups), 3)
        + 0.3 * _ratio(len(key_takeaways), 3)
    )
    overall_score = round(
        0.3 * groundedness_score
        + 0.2 * citation_coverage_score
        + 0.2 * quiz_quality_score
        + 0.15 * tutoring_value_score
        + 0.15 * learner_fit_score
    )

    return {
        "counts": {
            "knowledge_points": len(knowledge_points),
            "knowledge_points_with_refs": knowledge_ref_count,
            "quiz_items": len(quiz_items),
            "quiz_items_with_refs": quiz_ref_count,
            "quiz_items_with_variants": quiz_variant_count,
            "practice_items": len(practice_items),
            "practice_items_with_citations": practice_citation_count,
            "followups": len(followups),
            "key_takeaways": len(key_takeaways),
            "rag_chunks": len(rag_chunks),
        },
        "ratios": {
            "knowledge_ref_ratio": knowledge_ref_ratio,
            "quiz_ref_ratio": quiz_ref_ratio,
            "quiz_variant_ratio": quiz_variant_ratio,
            "practice_citation_ratio": practice_citation_ratio,
            "retrieval_fill_ratio": retrieval_fill_ratio,
        },
        "retrieval": {
            "final_hits": final_hits,
            "search_k": search_k,
            "vector_hits": vector_hits,
            "lexical_hits": lexical_hits,
            "hybrid_enabled": bool(rag_diagnostics.get("hybrid_enabled")),
            "rerank_enabled": bool(rag_diagnostics.get("rerank_enabled")),
            "source_counts": {
                "vector": int(source_counts.get("vector", 0) or 0),
                "lexical": int(source_counts.get("lexical", 0) or 0),
            },
        },
        "scorecard": {
            "groundedness": groundedness_score,
            "citation_coverage": citation_coverage_score,
            "quiz_quality": quiz_quality_score,
            "tutoring_value": tutoring_value_score,
            "learner_fit": learner_fit_score,
            "overall": overall_score,
        },
        "gates": {
            "needs_more_references": knowledge_ref_ratio < 70 or quiz_ref_ratio < 70,
            "needs_more_retrieval": bool(rag_diagnostics.get("enabled")) and final_hits < max(1, min(3, search_k)),
            "needs_more_practice": len(practice_items) < 1 or practice_citation_ratio < 60,
        },
    }


def _ratio(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return max(0, min(100, round((numerator / denominator) * 100)))
