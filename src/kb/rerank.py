from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def _tokenize(text: str) -> List[str]:
    raw = (text or "").lower()
    words = re.findall(r"[a-z0-9_]+", raw)
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", raw)
    return words + cjk_chars


def _overlap_ratio(query: str, text: str) -> float:
    query_tokens = _tokenize(query)
    text_tokens = set(_tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    matched = sum(1 for token in query_tokens if token in text_tokens)
    return matched / len(query_tokens)


def rerank_results(
    *,
    query: str,
    results: List[Tuple[float, Dict[str, Any]]],
    top_k: int,
) -> List[Tuple[float, Dict[str, Any]]]:
    rescored: List[Tuple[float, Dict[str, Any]]] = []
    for base_score, metadata in results:
        overlap = _overlap_ratio(query, str(metadata.get("text", "")))
        source_count = len(metadata.get("retrieval_sources", ["vector"]))
        rerank_score = float(base_score) + (0.2 * overlap) + (0.03 * min(source_count, 2))
        rescored.append(
            (
                rerank_score,
                {
                    **metadata,
                    "rerank_score": round(rerank_score, 6),
                    "overlap_score": round(overlap, 6),
                },
            )
        )
    rescored.sort(key=lambda item: item[0], reverse=True)
    return rescored[:top_k]
