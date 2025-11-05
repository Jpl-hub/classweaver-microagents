import json
from typing import Any, Dict, List

from django.conf import settings
from pydantic import BaseModel, Field, ValidationError, field_validator

from . import prompts
from .utils import parse_agent_json


class PlannerQuizOption(BaseModel):
    A: str
    B: str
    C: str
    D: str


class PlannerQuizItem(BaseModel):
    id: str
    question: str
    options: PlannerQuizOption
    answer: str = Field(pattern="^[ABCD]$")
    explain: str = Field(default="")
    difficulty: str = Field(default="medium")
    kp_ids: List[str] = Field(default_factory=list)
    refs: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("refs", mode="before")
    @classmethod
    def normalize_refs(cls, value: Any) -> List[Dict[str, Any]]:
        if not value:
            return []
        normalized: List[Dict[str, Any]] = []
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                ref_id = item.strip()
                if not ref_id:
                    continue
                doc_id, _, _ = ref_id.rpartition("-")
                payload: Dict[str, Any] = {"chunk_id": ref_id}
                if doc_id:
                    payload.setdefault("doc_id", doc_id)
                normalized.append(payload)
            else:
                # Ignore unsupported ref type but keep validation friendly
                continue
        return normalized


class PlannerQuiz(BaseModel):
    items: List[PlannerQuizItem]


class PlannerResponse(BaseModel):
    title: str
    summary: str
    knowledge_points: List[Dict[str, Any]]
    glossary: List[Dict[str, Any]]
    quiz: PlannerQuiz


def _build_user_prompt(text: str, rag_chunks: List[Dict[str, Any]]) -> str:
    buffer = [text.strip()]
    if rag_chunks:
        buffer.append("CONTEXT:")
        for chunk in rag_chunks:
            refs = chunk.get("refs", [])
            ref_str = ", ".join(f"{ref.get('doc_id')}#{ref.get('chunk_id')}" for ref in refs)
            buffer.append(f"- {chunk.get('text', '').strip()} [refs: {ref_str}]")
    return "\n".join(buffer)


def generate_plan(*, client, text: str, rag_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate initial lesson plan and quiz draft."""
    user_prompt = _build_user_prompt(text, rag_chunks)
    response = client.chat(
        model=settings.AGENT_SETTINGS["qwen_model"],
        system=prompts.PLANNER_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0.3,
    )
    parsed = parse_agent_json(response)
    try:
        validated = PlannerResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Planner response validation failed: {exc}") from exc
    payload = validated.model_dump()
    if rag_chunks:
        payload.setdefault("rag", {})["refs"] = rag_chunks
    return payload
