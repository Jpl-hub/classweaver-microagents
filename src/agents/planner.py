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

    @field_validator("options", mode="before")
    @classmethod
    def ensure_all_options(cls, value: Any) -> Dict[str, str]:
        if not isinstance(value, dict):
            raise ValueError("Options must be a dictionary.")
        normalized: Dict[str, str] = {}
        for letter in ("A", "B", "C", "D"):
            option_text = value.get(letter)
            if option_text is None or str(option_text).strip() == "":
                option_text = f"{letter} 选项待补全"
            normalized[letter] = str(option_text)
        return normalized

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
    buffer = [
        "请用简体中文输出所有内容，不要出现英文讲解。",
        "根据以下输入生成课程概览、知识点、术语表和测验题：",
        text.strip(),
    ]
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
    _sanitize_quiz_options(parsed)
    try:
        validated = PlannerResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Planner response validation failed: {exc}") from exc
    payload = validated.model_dump()
    if rag_chunks:
        payload.setdefault("rag", {})["refs"] = rag_chunks
    return payload


def _sanitize_quiz_options(payload: Dict[str, Any]) -> None:
    quiz = payload.get("quiz")
    if not isinstance(quiz, dict):
        return
    items = quiz.get("items")
    if not isinstance(items, list):
        return
    normalized_items: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        options = item.get("options")
        if not isinstance(options, dict):
            continue
        sanitized = {}
        for letter in ("A", "B", "C", "D"):
            text_value = options.get(letter)
            if text_value is None or str(text_value).strip() == "":
                text_value = f"{letter} 选项待补全"
            sanitized[letter] = str(text_value)
        item["options"] = sanitized
        normalized_items.append(item)
    quiz["items"] = normalized_items
