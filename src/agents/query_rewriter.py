import json
from typing import Any, Dict

from django.conf import settings
from pydantic import BaseModel, ValidationError

from . import prompts
from .utils import parse_agent_json


class QueryRewriteResponse(BaseModel):
    query: str
    rationale: str


def rewrite_review_query(
    *,
    client,
    text: str,
    evaluation: Dict[str, Any],
    reflection: Dict[str, Any],
) -> Dict[str, str]:
    payload = {
        "lesson_request": text,
        "evaluation": {
            "verdict": evaluation.get("verdict"),
            "scores": evaluation.get("scores", {}),
            "risks": evaluation.get("risks", []),
            "missing_evidence": evaluation.get("missing_evidence", []),
        },
        "reflection": reflection or {},
    }
    response = client.chat(
        model=settings.AGENT_SETTINGS["qwen_model"],
        system=prompts.QUERY_REWRITE_SYSTEM_PROMPT,
        user="请将下面的课程请求重写成更适合补检索的查询：\n" + json.dumps(payload, ensure_ascii=False),
        temperature=0.1,
    )
    parsed = parse_agent_json(response)
    try:
        validated = QueryRewriteResponse.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Query rewrite validation failed: {exc}") from exc
    return validated.model_dump()
