import json
from typing import Any, Dict, List

from django.conf import settings
from pydantic import BaseModel, Field, ValidationError, field_validator

from . import prompts
from .utils import parse_agent_json


class VariantItem(BaseModel):
    text: str = Field(alias="question")
    options: Dict[str, str]

    @field_validator("options")
    def ensure_options(cls, value: Dict[str, str]) -> Dict[str, str]:
        keys = {"A", "B", "C", "D"}
        if set(value.keys()) != keys:
            missing = keys - set(value.keys())
            raise ValueError(f"Options must include A-D. Missing: {', '.join(sorted(missing))}")
        return value


class RewriterQuizItem(BaseModel):
    id: str
    question: str
    options: Dict[str, str]
    answer: str = Field(pattern="^[ABCD]$")
    explain: str = ""
    difficulty: str = "medium"
    kp_ids: List[str] = Field(default_factory=list)
    variants: List[VariantItem] = Field(default_factory=list)


class RewriterQuiz(BaseModel):
    items: List[RewriterQuizItem]


class RewriterResponse(BaseModel):
    quiz: RewriterQuiz


def rewrite_quiz(*, client, planner_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Refine quiz items with variants while preserving answers."""
    planner_quiz = planner_payload.get("quiz", {})
    serialized = {
        "quiz": {
            "items": []
        }
    }
    for item in planner_quiz.get("items", []):
        serialized["quiz"]["items"].append(
            {
                "id": item.get("id"),
                "question": item.get("question"),
                "options": item.get("options"),
                "answer": item.get("answer"),
                "explain": item.get("explain", ""),
                "difficulty": item.get("difficulty", "medium"),
                "kp_ids": item.get("kp_ids", []),
            }
        )

    response = client.chat(
        model=settings.AGENT_SETTINGS["deepseek_model"],
        system=prompts.REWRITER_SYSTEM_PROMPT,
        user="请用简体中文改写以下题目与选项，保持 JSON 结构不变：\n" + json.dumps(serialized, ensure_ascii=False),
        temperature=0.4,
    )

    parsed = parse_agent_json(response)
    try:
        validated = RewriterResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Rewriter response validation failed: {exc}") from exc
    merged = planner_payload.copy()
    merged["quiz"] = validated.model_dump()["quiz"]
    return merged
