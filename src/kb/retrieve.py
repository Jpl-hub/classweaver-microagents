from typing import Any, Dict, List

from django.conf import settings

from src.agents.utils import build_client
from src.core.models import KnowledgeBase, KnowledgeDocument

from .store import get_store


def _fuse_ranked_results(
    vector_results: List[tuple[float, Dict[str, Any]]],
    lexical_results: List[tuple[float, Dict[str, Any]]],
    *,
    top_k: int,
    rrf_k: int = 60,
) -> List[tuple[float, Dict[str, Any]]]:
    fused: Dict[tuple[str, str], Dict[str, Any]] = {}

    def ingest(results: List[tuple[float, Dict[str, Any]]], source: str) -> None:
        for rank, (_score, metadata) in enumerate(results, start=1):
            key = (str(metadata.get("doc_id", "")), str(metadata.get("chunk_id", "")))
            if key not in fused:
                fused[key] = {"score": 0.0, "metadata": metadata.copy(), "sources": []}
            fused[key]["score"] += 1.0 / (rrf_k + rank)
            fused[key]["sources"].append(source)

    ingest(vector_results, "vector")
    ingest(lexical_results, "lexical")

    ranked = sorted(fused.values(), key=lambda item: item["score"], reverse=True)
    return [
        (
            float(item["score"]),
            {**item["metadata"], "retrieval_sources": item["sources"]},
        )
        for item in ranked[:top_k]
    ]


def retrieve_context(
    *,
    query: str,
    top_k: int = 5,
    base: KnowledgeBase,
) -> List[Dict[str, Any]]:
    """Retrieve top-k knowledge chunks for a given query."""
    if not query.strip():
        return []

    doc_ids = list(
        KnowledgeDocument.objects.filter(base=base, user=base.user).values_list("doc_id", flat=True)
    )
    if not doc_ids:
        return []

    agent_settings = settings.AGENT_SETTINGS
    client = build_client(agent_settings)
    embeddings = client.embed(model=agent_settings["embedding_model"], texts=[query])
    vector = embeddings[0]

    store = get_store(agent_settings["vector_backend"])
    allowed_set = [doc_id for doc_id in doc_ids if doc_id]
    if not allowed_set:
        return []
    total_entries = store.count(base_id=base.pk, doc_ids=allowed_set)
    if total_entries <= 0:
        return []
    search_k = min(total_entries, max(top_k * 3, top_k + len(allowed_set)))
    vector_results = store.search(vector, search_k, base_id=base.pk, doc_ids=allowed_set)
    if agent_settings.get("hybrid_retrieval", False):
        lexical_results = store.lexical_search(query, search_k, base_id=base.pk, doc_ids=allowed_set)
        results = _fuse_ranked_results(vector_results, lexical_results, top_k=search_k)
    else:
        results = vector_results
    if not results:
        return []
    results = results[:top_k]
    formatted: List[Dict[str, Any]] = []

    for score, metadata in results:
        formatted.append(
            {
                "text": metadata.get("text", ""),
                "score": score,
                "refs": [
                    {
                        "doc_id": metadata.get("doc_id"),
                        "chunk_id": metadata.get("chunk_id"),
                    }
                ],
                "title": metadata.get("title"),
                "metadata": {
                    **(metadata.get("metadata", {}) or {}),
                    "retrieval_sources": metadata.get("retrieval_sources", ["vector"]),
                },
            }
        )
    return formatted
