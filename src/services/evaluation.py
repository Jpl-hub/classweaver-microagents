from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Sequence

from src.services.citations import extract_citation_markers


def _normalize_ref(ref: Dict[str, Any]) -> tuple[str, str]:
    return (str(ref.get("doc_id", "")), str(ref.get("chunk_id", "")))


def _extract_refs(results: Sequence[Dict[str, Any]]) -> List[tuple[str, str]]:
    refs: List[tuple[str, str]] = []
    for item in results:
        for ref in item.get("refs", []) or []:
            refs.append(_normalize_ref(ref))
    return refs


@dataclass
class RetrievalCaseResult:
    query: str
    expected_refs: List[Dict[str, Any]]
    retrieved_refs: List[Dict[str, Any]]
    hit: bool
    reciprocal_rank: float
    recall_at_k: float
    precision_at_k: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "expected_refs": self.expected_refs,
            "retrieved_refs": self.retrieved_refs,
            "hit": self.hit,
            "reciprocal_rank": self.reciprocal_rank,
            "recall_at_k": self.recall_at_k,
            "precision_at_k": self.precision_at_k,
        }


@dataclass
class CitationCaseResult:
    query: str
    answer: str
    expected_refs: List[Dict[str, Any]]
    cited_refs: List[Dict[str, Any]]
    has_citation_markers: bool
    citation_hit: bool
    citation_recall: float
    citation_precision: float
    valid_marker_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "expected_refs": self.expected_refs,
            "cited_refs": self.cited_refs,
            "has_citation_markers": self.has_citation_markers,
            "citation_hit": self.citation_hit,
            "citation_recall": self.citation_recall,
            "citation_precision": self.citation_precision,
            "valid_marker_rate": self.valid_marker_rate,
        }


def evaluate_retrieval_cases(
    *,
    cases: Iterable[Dict[str, Any]],
    retrieve_fn: Callable[[str, int], List[Dict[str, Any]]],
    top_k: int = 5,
) -> Dict[str, Any]:
    case_results: List[RetrievalCaseResult] = []

    for raw_case in cases:
        query = str(raw_case.get("query", "")).strip()
        expected_refs = raw_case.get("expected_refs") or []
        if not query or not expected_refs:
            continue

        expected_set = {_normalize_ref(ref) for ref in expected_refs}
        retrieved = retrieve_fn(query, top_k)
        retrieved_pairs = _extract_refs(retrieved)
        matched = [pair for pair in retrieved_pairs if pair in expected_set]

        reciprocal_rank = 0.0
        for index, pair in enumerate(retrieved_pairs, start=1):
            if pair in expected_set:
                reciprocal_rank = 1.0 / index
                break

        recall = len(set(matched)) / len(expected_set) if expected_set else 0.0
        precision = len(matched) / len(retrieved_pairs) if retrieved_pairs else 0.0

        case_results.append(
            RetrievalCaseResult(
                query=query,
                expected_refs=list(expected_refs),
                retrieved_refs=[
                    {"doc_id": doc_id, "chunk_id": chunk_id}
                    for doc_id, chunk_id in retrieved_pairs
                ],
                hit=bool(matched),
                reciprocal_rank=round(reciprocal_rank, 4),
                recall_at_k=round(recall, 4),
                precision_at_k=round(precision, 4),
            )
        )

    total = len(case_results)
    if total == 0:
        return {
            "summary": {
                "cases": 0,
                "hit_rate": 0.0,
                "mrr": 0.0,
                "avg_recall_at_k": 0.0,
                "avg_precision_at_k": 0.0,
            },
            "cases": [],
        }

    hit_rate = sum(1 for item in case_results if item.hit) / total
    mrr = sum(item.reciprocal_rank for item in case_results) / total
    avg_recall = sum(item.recall_at_k for item in case_results) / total
    avg_precision = sum(item.precision_at_k for item in case_results) / total

    return {
        "summary": {
            "cases": total,
            "hit_rate": round(hit_rate, 4),
            "mrr": round(mrr, 4),
            "avg_recall_at_k": round(avg_recall, 4),
            "avg_precision_at_k": round(avg_precision, 4),
        },
        "cases": [item.to_dict() for item in case_results],
    }


def evaluate_citation_cases(
    *,
    cases: Iterable[Dict[str, Any]],
    qa_fn: Callable[[str, int], Dict[str, Any]],
    top_k: int = 4,
) -> Dict[str, Any]:
    case_results: List[CitationCaseResult] = []

    for raw_case in cases:
        query = str(raw_case.get("query", "")).strip()
        expected_refs = raw_case.get("expected_refs") or []
        if not query or not expected_refs:
            continue

        payload = qa_fn(query, top_k)
        answer = str(payload.get("answer", ""))
        citations = payload.get("citations") or []
        markers = extract_citation_markers(answer)
        cited_refs = [
            {
                "doc_id": citation.get("doc_id", ""),
                "chunk_id": citation.get("chunk_id", ""),
            }
            for citation in citations
        ]

        expected_set = {_normalize_ref(ref) for ref in expected_refs}
        cited_set = {_normalize_ref(ref) for ref in cited_refs}
        matched = expected_set & cited_set

        valid_markers = [marker for marker in markers if 1 <= marker <= len(citations)]
        marker_rate = len(valid_markers) / len(markers) if markers else 0.0
        recall = len(matched) / len(expected_set) if expected_set else 0.0
        precision = len(matched) / len(cited_set) if cited_set else 0.0

        case_results.append(
            CitationCaseResult(
                query=query,
                answer=answer,
                expected_refs=list(expected_refs),
                cited_refs=cited_refs,
                has_citation_markers=bool(markers),
                citation_hit=bool(matched),
                citation_recall=round(recall, 4),
                citation_precision=round(precision, 4),
                valid_marker_rate=round(marker_rate, 4),
            )
        )

    total = len(case_results)
    if total == 0:
        return {
            "summary": {
                "cases": 0,
                "citation_hit_rate": 0.0,
                "citation_marker_rate": 0.0,
                "avg_citation_recall": 0.0,
                "avg_citation_precision": 0.0,
                "avg_valid_marker_rate": 0.0,
            },
            "cases": [],
        }

    return {
        "summary": {
            "cases": total,
            "citation_hit_rate": round(sum(1 for item in case_results if item.citation_hit) / total, 4),
            "citation_marker_rate": round(sum(1 for item in case_results if item.has_citation_markers) / total, 4),
            "avg_citation_recall": round(sum(item.citation_recall for item in case_results) / total, 4),
            "avg_citation_precision": round(sum(item.citation_precision for item in case_results) / total, 4),
            "avg_valid_marker_rate": round(sum(item.valid_marker_rate for item in case_results) / total, 4),
        },
        "cases": [item.to_dict() for item in case_results],
    }
