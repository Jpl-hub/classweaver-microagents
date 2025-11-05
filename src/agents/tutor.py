import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from pydantic import BaseModel, Field, ValidationError

from . import prompts
from .utils import parse_agent_json


class TutorPracticeItem(BaseModel):
    prompt: str
    answer: str
    reasoning: str = ""
    citations: List[Dict[str, Any]] = Field(default_factory=list)


class TutorSummary(BaseModel):
    recap: str
    key_takeaways: List[str]
    encouragement: str


class TutorResponse(BaseModel):
    summary: TutorSummary
    practice: List[TutorPracticeItem]
    followups: List[str]


def build_tutor_response(
    *,
    client,
    final_quiz: Dict[str, Any],
    answers: Optional[Dict[str, Any]] = None,
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Produce tutor feedback and extra practice items."""
    payload = {
        "quiz": final_quiz.get("quiz", {}),
        "answers": answers or {},
    }
    if rag_chunks:
        payload["context"] = rag_chunks

    response = client.chat(
        model=settings.AGENT_SETTINGS["qwen_model"],
        system=prompts.TUTOR_SYSTEM_PROMPT,
        user=json.dumps(payload, ensure_ascii=False),
        temperature=0.3,
    )

    parsed = parse_agent_json(response)
    try:
        validated = TutorResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Tutor response validation failed: {exc}") from exc
    return validated.model_dump()
