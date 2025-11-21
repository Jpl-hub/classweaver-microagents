from typing import Any, Dict, List, Optional

from django.conf import settings

from src.agents.utils import build_client

from .store import get_store


def retrieve_context(*, query: str, top_k: int = 5, doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Retrieve top-k knowledge chunks for a given query."""
    if not query.strip():
        return []

    agent_settings = settings.AGENT_SETTINGS
    client = build_client(agent_settings)
    embeddings = client.embed(model=agent_settings["embedding_model"], texts=[query])
    vector = embeddings[0]

    store = get_store(agent_settings["vector_backend"])
    results = store.search(vector, top_k)
    allowed = {doc_id for doc_id in (doc_ids or []) if doc_id}
    formatted: List[Dict[str, Any]] = []
    filtered_results = results
    if allowed:
        filtered = [entry for entry in results if entry[1].get("doc_id") in allowed]
        if filtered:
            filtered_results = filtered

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
