from __future__ import annotations

from datetime import timedelta
from time import perf_counter
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from src.agents import evaluator, planner, query_rewriter, rewriter, runtime, tutor
from src.agents.utils import build_client
from src.core.models import LessonEvent, LessonPlan, LlmCallLog, PrestudyJob
from src.kb import retrieve

from . import printable
from .citations import build_citations
from .ppt import extract_text


def _collect_rag_context(
    *,
    job: PrestudyJob,
    text: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    if not settings.AGENT_SETTINGS.get("rag_enabled", True):
        return {"results": [], "diagnostics": {"enabled": False}}

    if not job.knowledge_base_id or not job.user_id:
        return {"results": [], "diagnostics": {"enabled": False}}

    payload = retrieve.retrieve_context_with_diagnostics(
        query=text,
        top_k=top_k,
        base=job.knowledge_base,
    )
    payload["diagnostics"]["enabled"] = True
    return payload


def _score_of(payload: Dict[str, Any]) -> int:
    evaluation = payload.get("evaluation") or {}
    scores = evaluation.get("scores") or {}
    return int(scores.get("overall", 0) or 0)


def _should_run_review_cycle(
    *,
    final_payload: Dict[str, Any],
    settings_map: Dict[str, Any],
    round_index: int,
) -> bool:
    if not settings_map.get("review_enabled", True):
        return False
    if round_index >= max(0, int(settings_map.get("review_max_rounds", 0) or 0)):
        return False
    reflection = final_payload.get("reflection") or {}
    return bool(reflection.get("should_expand_retrieval") or reflection.get("should_regenerate"))


def _build_review_cycle_summary(
    *,
    round_index: int,
    trigger: Dict[str, Any],
    strategy: str,
    query_text: str,
    query_rewrite: Dict[str, Any] | None,
    top_k: int,
    initial_payload: Dict[str, Any],
    revised_payload: Dict[str, Any],
    diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    initial_score = _score_of(initial_payload)
    revised_score = _score_of(revised_payload)
    return {
        "round": round_index,
        "strategy": strategy,
        "query_text": query_text,
        "query_rewrite": query_rewrite or {},
        "top_k": top_k,
        "trigger": trigger,
        "initial_overall_score": initial_score,
        "revised_overall_score": revised_score,
        "score_delta": revised_score - initial_score,
        "retrieval_diagnostics": diagnostics,
        "initial_evaluation": initial_payload.get("evaluation") or {},
        "evaluation": revised_payload.get("evaluation") or {},
        "reflection": revised_payload.get("reflection") or {},
    }


def _select_review_strategy(final_payload: Dict[str, Any], reflection: Dict[str, Any]) -> str:
    if reflection.get("should_expand_retrieval"):
        return "full_pipeline"
    rule_metrics = (final_payload.get("evaluation") or {}).get("rule_metrics") or {}
    gates = rule_metrics.get("gates") or {}
    if gates.get("needs_more_practice") and not gates.get("needs_more_references"):
        return "tutor_only"
    return "full_pipeline"


def run_pipeline(
    *,
    job: PrestudyJob,
    text: Optional[str] = None,
    ppt_file: Any | None = None,
) -> Dict[str, Any]:
    """Execute planner -> rewriter -> tutor pipeline for a prestudy job."""
    if text is None and ppt_file is None:
        raise ValueError("Either text or ppt_file must be provided.")

    if ppt_file is not None:
        extracted_text = extract_text(ppt_file)
        job.source_type = "ppt"
    else:
        extracted_text = (text or "").strip()
        job.source_type = "text"

    if not extracted_text:
        raise ValueError("Failed to obtain content for pipeline execution.")

    job.source_excerpt = extracted_text[:1024]
    job.save(update_fields=["source_type", "source_excerpt"])

    agent_settings = settings.AGENT_SETTINGS
    client = build_client(agent_settings)
    initial_top_k = 5
    rag_payload = _collect_rag_context(job=job, text=extracted_text, top_k=initial_top_k)
    rag_chunks = rag_payload.get("results", [])
    rag_diagnostics = rag_payload.get("diagnostics", {})

    start = perf_counter()
    pipeline_result = runtime.orchestrate_pipeline(
        client=client,
        planner_module=planner,
        rewriter_module=rewriter,
        tutor_module=tutor,
        evaluator_module=evaluator,
        text=extracted_text,
        rag_chunks=rag_chunks,
        settings=agent_settings,
        rag_diagnostics=rag_diagnostics,
        cycle_label="initial",
    )
    review_cycles: List[Dict[str, Any]] = []
    current_rag_payload = rag_payload
    current_result = pipeline_result
    review_multiplier = max(2, int(agent_settings.get("review_top_k_multiplier", 2) or 2))
    for round_index in range(1, max(0, int(agent_settings.get("review_max_rounds", 0) or 0)) + 1):
        current_final = current_result.get("final_json", {}) or {}
        if not _should_run_review_cycle(final_payload=current_final, settings_map=agent_settings, round_index=round_index - 1):
            break
        reflection = current_final.get("reflection") or {}
        strategy = _select_review_strategy(current_final, reflection)
        next_top_k = initial_top_k
        review_query_text = extracted_text
        query_rewrite_payload: Dict[str, Any] | None = None
        if reflection.get("should_expand_retrieval"):
            next_top_k = min(12, max(initial_top_k + 2, initial_top_k * review_multiplier))
            query_rewrite_payload = query_rewriter.rewrite_review_query(
                client=client,
                text=extracted_text,
                evaluation=current_final.get("evaluation") or {},
                reflection=reflection,
            )
            review_query_text = query_rewrite_payload.get("query") or extracted_text
            current_rag_payload = _collect_rag_context(job=job, text=review_query_text, top_k=next_top_k)
        if strategy == "tutor_only":
            revised_result = runtime.run_tutor_evaluation_cycle(
                client=client,
                tutor_module=tutor,
                evaluator_module=evaluator,
                text=extracted_text,
                planner_payload=current_result.get("planner_json", {}) or {},
                final_payload=current_final,
                rag_chunks=current_rag_payload.get("results", []),
                rag_diagnostics=current_rag_payload.get("diagnostics", {}),
                settings=agent_settings,
                cycle_label=f"review_{round_index}_tutor",
            )
        else:
            revised_result = runtime.orchestrate_pipeline(
                client=client,
                planner_module=planner,
                rewriter_module=rewriter,
                tutor_module=tutor,
                evaluator_module=evaluator,
                text=extracted_text,
                rag_chunks=current_rag_payload.get("results", []),
                settings=agent_settings,
                rag_diagnostics=current_rag_payload.get("diagnostics", {}),
                cycle_label=f"review_{round_index}",
            )
        review_cycles.append(
            _build_review_cycle_summary(
                round_index=round_index,
                trigger={
                    "should_expand_retrieval": bool(reflection.get("should_expand_retrieval")),
                    "should_regenerate": bool(reflection.get("should_regenerate")),
                    "should_add_multimodal_review": bool(reflection.get("should_add_multimodal_review")),
                },
                strategy=strategy,
                query_text=review_query_text,
                query_rewrite=query_rewrite_payload,
                top_k=next_top_k,
                initial_payload=current_final,
                revised_payload=revised_result.get("final_json", {}) or {},
                diagnostics=current_rag_payload.get("diagnostics", {}),
            )
        )
        current_result = {
            **revised_result,
            "model_trace": [*(current_result.get("model_trace", []) or []), *(revised_result.get("model_trace", []) or [])],
        }
        initial_top_k = next_top_k

    duration_ms = int((perf_counter() - start) * 1000)
    pipeline_result = current_result
    rag_chunks = current_rag_payload.get("results", [])
    rag_diagnostics = current_rag_payload.get("diagnostics", {})
    source_citations = build_citations(rag_chunks, limit=5)

    planner_payload = pipeline_result.get("planner_json", {}) or {}
    final_payload = pipeline_result.get("final_json", {}) or {}
    if source_citations:
        planner_payload["sources"] = source_citations
        final_payload["sources"] = source_citations
    if rag_diagnostics:
        planner_payload["retrieval_diagnostics"] = rag_diagnostics
        final_payload["retrieval_diagnostics"] = rag_diagnostics
    if review_cycles:
        final_payload["review_summary"] = {
            "executed_rounds": len(review_cycles),
            "cycles": review_cycles,
            "initial_overall_score": review_cycles[0].get("initial_overall_score"),
            "final_overall_score": review_cycles[-1].get("revised_overall_score"),
            "pending_multimodal_review": bool(review_cycles[-1].get("trigger", {}).get("should_add_multimodal_review")),
        }

    job.planner_json = planner_payload
    job.final_json = final_payload
    job.model_trace = pipeline_result.get("model_trace", {})
    job.status = pipeline_result.get("status", "completed")
    job.duration_ms = duration_ms
    job.save(update_fields=["planner_json", "final_json", "model_trace", "status", "duration_ms"])

    printable_payload = pipeline_result.get("printable") or printable.build_printable_payload(job.final_json)
    lesson_plan_snapshot = _ensure_lesson_plan(job)

    _persist_model_trace(job=job, trace=pipeline_result.get("model_trace", []))

    response_payload = {
        "id": str(job.pk),
        "status": job.status,
        "planner_json": job.planner_json,
        "final_json": job.final_json,
        "model_trace": job.model_trace,
        "duration_ms": duration_ms,
        "printable": printable_payload,
        "lesson_plan": lesson_plan_snapshot,
    }
    return response_payload


def _persist_model_trace(*, job: PrestudyJob, trace: List[Dict[str, Any]]) -> None:
    if not trace:
        return
    log_entries: List[LlmCallLog] = []
    for segment in trace:
        log_entries.append(
            LlmCallLog(
                job=job,
                step=str(segment.get("step", ""))[:32],
                provider=str(segment.get("provider", ""))[:32],
                model=str(segment.get("model", ""))[:128],
                base_url=str(segment.get("base_url", ""))[:200],
                latency_ms=int(segment.get("latency_ms", 0) or 0),
                input_chars=int(segment.get("input_chars", 0) or 0),
                output_chars=int(segment.get("output_chars", 0) or 0),
                fallback=bool(segment.get("fallback", False)),
                rag_snapshot=segment.get("rag") or {},
            )
        )
    LlmCallLog.objects.bulk_create(log_entries)


def _ensure_lesson_plan(job: PrestudyJob) -> Dict[str, Any] | None:
    final_payload = job.final_json or {}
    structure = final_payload.get("lesson_plan") or {
        "focus": final_payload.get("knowledge_points", []),
        "quiz": final_payload.get("quiz", {}).get("items", []),
        "glossary": final_payload.get("glossary", []),
    }
    title = final_payload.get("title") or f"课堂计划 #{job.pk}"

    plan, _created = LessonPlan.objects.update_or_create(
        job=job,
        defaults={
            "user": job.user,
            "title": title,
            "structure": structure,
            "notes": final_payload.get("summary", ""),
        },
    )
    _seed_lesson_events(plan=plan, structure=structure)
    return {"id": plan.pk, "title": plan.title, "structure": plan.structure, "notes": plan.notes}


def _seed_lesson_events(*, plan: LessonPlan, structure: Dict[str, Any]) -> None:
    if plan.events.exists():
        return

    events: List[LessonEvent] = []
    timeline = structure or {}
    focus_points = timeline.get("focus") or timeline.get("knowledge_points") or []
    quiz_items: List[Dict[str, Any]] = []
    quiz_block = timeline.get("quiz")
    if isinstance(quiz_block, dict):
        quiz_items = quiz_block.get("items", []) or []

    current_time = timezone.now()

    def enqueue(event_type: str, payload: Dict[str, Any]) -> None:
        nonlocal current_time
        events.append(
            LessonEvent(
                plan=plan,
                event_type=event_type,
                actor="系统",
                payload=payload,
                occurred_at=current_time,
            )
        )
        current_time += timedelta(minutes=5)

    enqueue("课堂准备", {"note": "自动生成课堂节奏"})
    for point in focus_points[:8]:
        enqueue(
            "知识点讲解",
            {"title": point.get("title"), "summary": point.get("summary")},
        )
    for quiz in quiz_items[:5]:
        enqueue(
            "课堂提问",
            {"question": quiz.get("question"), "difficulty": quiz.get("difficulty")},
        )

    if events:
        LessonEvent.objects.bulk_create(events)
