from __future__ import annotations

from typing import Any, Dict, List

from django.conf import settings

from src.agents.utils import build_client
from src.kb import retrieve as kb_retrieve
from src.services.citations import build_citations, extract_citation_markers


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _confidence_payload(*, answer: str, citations: List[Dict[str, Any]], diagnostics: Dict[str, Any], top_k: int) -> Dict[str, Any]:
    citation_count = len(citations)
    final_hits = int(diagnostics.get("final_hits") or 0)
    marker_count = len(extract_citation_markers(answer))

    score = 0.35
    score += min(citation_count, 3) * 0.12
    score += min(final_hits, top_k) / max(top_k, 1) * 0.18
    if marker_count:
        score += 0.1
    if diagnostics.get("hybrid_enabled"):
        score += 0.05
    if diagnostics.get("rerank_enabled"):
        score += 0.04
    score = round(_clamp(score, lower=0.12, upper=0.95), 2)

    if score >= 0.8:
        label = "高把握"
    elif score >= 0.65:
        label = "中高把握"
    elif score >= 0.5:
        label = "中等把握"
    else:
        label = "谨慎参考"

    rationale_parts = []
    if citation_count:
        rationale_parts.append(f"命中 {citation_count} 条可引用证据")
    if final_hits:
        rationale_parts.append(f"最终保留 {final_hits} 条候选")
    if marker_count:
        rationale_parts.append("回答内已标出引用位置")
    if diagnostics.get("hybrid_enabled"):
        rationale_parts.append("采用了多路召回")
    if diagnostics.get("rerank_enabled"):
        rationale_parts.append("结果经过了重排")

    return {
        "score": score,
        "label": label,
        "rationale": "，".join(rationale_parts) if rationale_parts else "当前回答缺少足够证据支撑，需要谨慎参考。",
    }


def _build_evidence_summary(*, citations: List[Dict[str, Any]], diagnostics: Dict[str, Any]) -> str:
    if not citations:
        return "这次回答没有命中到可直接引用的资料片段。"

    titles: List[str] = []
    for citation in citations[:3]:
        title = str(citation.get("title") or citation.get("doc_id") or "").strip()
        if title and title not in titles:
            titles.append(title)

    final_hits = int(diagnostics.get("final_hits") or len(citations))
    source_mix = diagnostics.get("source_counts") or {}
    source_bits = [f"{key} {value}" for key, value in source_mix.items() if value]

    summary = f"这次回答主要依据 {', '.join(titles) if titles else '当前命中的资料'} 中的 {final_hits} 条片段。"
    if source_bits:
        summary += f" 召回来源里包含 {' / '.join(source_bits)}。"
    return summary


def _build_next_steps(*, question: str, citations: List[Dict[str, Any]], diagnostics: Dict[str, Any]) -> List[str]:
    final_hits = int(diagnostics.get("final_hits") or 0)
    if not citations or not final_hits:
        return [
            "把问题再缩小一点，只问一个定义、一个公式或一个步骤。",
            "如果这部分很关键，先补一份更直接相关的讲义、题解或课堂笔记。",
            "换一种问法再问一次，尽量带上章节名、概念名或题型。",
        ]

    steps = [
        "如果你想继续学，可以让我把这个问题压缩成 3 句话的课堂讲解。",
        "如果你想确认自己有没有真的懂，可以直接让我基于这个问题出 2 道小测。",
    ]
    if len(citations) >= 2:
        steps.append("如果你想看资料怎么支撑这个结论，可以继续追问“这几个来源分别说明了什么”。")
    else:
        steps.append("如果你想讲得更稳，可以继续追问“这个结论对应的原始依据是什么”。")
    return steps


def _build_suggested_questions(*, question: str, citations: List[Dict[str, Any]]) -> List[str]:
    stem = question.strip().rstrip("？?。")
    if not citations:
        return [
            f"{stem}对应的是哪个章节或知识点？",
            f"{stem}有没有更基础的前置概念？",
            f"如果我给你更多资料，你建议我补什么？",
        ]

    title = str(citations[0].get("title") or citations[0].get("doc_id") or "").strip()
    title_hint = f"结合《{title}》" if title else "结合当前资料"
    return [
        f"{title_hint}，把“{stem}”讲成一段 1 分钟口语化解释。",
        f"围绕“{stem}”出 2 道从易到难的小测。",
        f"“{stem}”最容易混淆的地方是什么？",
    ]


def _build_followup(*, question: str, answer: str, citations: List[Dict[str, Any]], diagnostics: Dict[str, Any], top_k: int) -> Dict[str, Any]:
    return {
        "confidence": _confidence_payload(answer=answer, citations=citations, diagnostics=diagnostics, top_k=top_k),
        "evidence_summary": _build_evidence_summary(citations=citations, diagnostics=diagnostics),
        "next_steps": _build_next_steps(question=question, citations=citations, diagnostics=diagnostics),
        "suggested_questions": _build_suggested_questions(question=question, citations=citations),
    }


def answer_question(*, question: str, base, top_k: int = 4) -> Dict[str, Any]:
    retrieval_payload = kb_retrieve.retrieve_context_with_diagnostics(query=question, top_k=top_k, base=base)
    contexts = retrieval_payload["results"]
    diagnostics = retrieval_payload.get("diagnostics", {})
    if not contexts:
        answer = "知识库中没有找到相关内容。"
        return {
            "answer": answer,
            "contexts": [],
            "citations": [],
            "retrieval_diagnostics": diagnostics,
            "followup": _build_followup(
                question=question,
                answer=answer,
                citations=[],
                diagnostics=diagnostics,
                top_k=top_k,
            ),
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
        "retrieval_diagnostics": diagnostics,
        "followup": _build_followup(
            question=question,
            answer=answer,
            citations=citations,
            diagnostics=diagnostics,
            top_k=top_k,
        ),
    }
