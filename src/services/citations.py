from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _truncate_text(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def normalize_citation(entry: Dict[str, Any], *, index: int | None = None) -> Dict[str, Any]:
    refs = entry.get("refs") or []
    primary_ref = refs[0] if isinstance(refs, list) and refs else {}
    doc_id = entry.get("doc_id") or primary_ref.get("doc_id") or ""
    chunk_id = entry.get("chunk_id") or primary_ref.get("chunk_id") or ""
    title = entry.get("title") or entry.get("source_title") or ""
    score = entry.get("score")
    citation = {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "title": title,
        "text": _truncate_text(str(entry.get("text", ""))),
    }
    if score is not None:
        citation["score"] = float(score)
    if index is not None:
        citation["label"] = f"[{index}]"
    return citation


def build_citations(entries: Iterable[Dict[str, Any]], *, limit: int = 5) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        citation = normalize_citation(entry, index=len(citations) + 1)
        key = (str(citation.get("doc_id", "")), str(citation.get("chunk_id", "")))
        if key in seen:
            continue
        seen.add(key)
        citations.append(citation)
        if len(citations) >= limit:
            break
    return citations

