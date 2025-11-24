from typing import Any, Dict, List

from django.conf import settings

from src.agents.utils import build_client
from src.core.models import KnowledgeBase, KnowledgeDocument

from .store import get_store


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
    total_entries = len(getattr(store, "metadata", []))
    search_k = min(total_entries or top_k, max(top_k * 3, top_k + len(doc_ids)))
    # Search with a larger candidate set to avoid missing hits after filtering by base/doc ownership.
    results = store.search(vector, search_k)
    allowed_set = {doc_id for doc_id in doc_ids if doc_id}
    if not allowed_set:
        return []
    filtered_results = [
        entry
        for entry in results
        if entry[1].get("doc_id") in allowed_set and str(entry[1].get("base_id")) == str(base.pk)
    ]
    # If nothing hits after filtering, broaden the search to the full index once to avoid empty recall.
    if not filtered_results and total_entries:
        results = store.search(vector, total_entries)
        filtered_results = [
            entry
            for entry in results
            if entry[1].get("doc_id") in allowed_set and str(entry[1].get("base_id")) == str(base.pk)
        ]
    if not filtered_results:
        return []
    filtered_results.sort(key=lambda item: item[0], reverse=True)
    filtered_results = filtered_results[:top_k]
    formatted: List[Dict[str, Any]] = []

    for score, metadata in filtered_results:
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
                "metadata": metadata.get("metadata", {}),
            }
        )
    return formatted
