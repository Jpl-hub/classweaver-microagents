from __future__ import annotations

from typing import Any, Dict

from django.conf import settings

from src.agents.utils import build_client
from src.kb import retrieve as kb_retrieve
from src.services.citations import build_citations


def answer_question(*, question: str, base, top_k: int = 4) -> Dict[str, Any]:
    retrieval_payload = kb_retrieve.retrieve_context_with_diagnostics(query=question, top_k=top_k, base=base)
    contexts = retrieval_payload["results"]
    if not contexts:
        return {
            "answer": "知识库中没有找到相关内容。",
            "contexts": [],
            "citations": [],
            "retrieval_diagnostics": retrieval_payload.get("diagnostics", {}),
        }

    client = build_client(settings.AGENT_SETTINGS)
    context_text = "\n\n".join(
        f"[{idx + 1}] {ctx.get('text', '')}" for idx, ctx in enumerate(contexts)
    )
    system_prompt = (
        "你是一个知识库问答助手。根据提供的上下文用中文简洁回答，"
        "如果上下文不足，直接说明无法找到答案，不要编造。"
    )
    user_prompt = (
        f"问题：{question}\n\n可用上下文：\n{context_text}"
        "\n\n请在回答中使用 [1] [2] 这类引用标记引用可用上下文，不要编造来源。"
    )

    answer = client.chat(
        model=settings.AGENT_SETTINGS.get("qwen_model", "Qwen/Qwen2.5-14B-Instruct"),
        system=system_prompt,
        user=user_prompt,
        temperature=0.2,
    )
    citations = build_citations(contexts, limit=top_k)
    return {
        "answer": answer,
        "contexts": contexts,
        "citations": citations,
        "retrieval_diagnostics": retrieval_payload.get("diagnostics", {}),
    }
