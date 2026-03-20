from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model

from src.core.models import KnowledgeBase, KnowledgeDocument
from src.kb import retrieve


@pytest.mark.django_db
def test_retrieve_context_delegates_filtering_to_store(monkeypatch):
    user = get_user_model().objects.create_user(username="bob", password="pw123456")
    base = KnowledgeBase.objects.create(user=user, name="kb")
    KnowledgeDocument.objects.create(user=user, base=base, doc_id="doc-1", title="Doc 1")

    fake_client = SimpleNamespace(embed=lambda **kwargs: [[0.1, 0.2, 0.3]])
    captured = {}

    class FakeStore:
        def count(self, *, base_id=None, doc_ids=None):
            captured["count"] = {"base_id": base_id, "doc_ids": doc_ids}
            return 1

        def search(self, embedding, top_k, *, base_id=None, doc_ids=None):
            captured["search"] = {
                "embedding": embedding,
                "top_k": top_k,
                "base_id": base_id,
                "doc_ids": doc_ids,
            }
            return [
                (
                    0.9,
                    {
                        "text": "chunk body",
                        "doc_id": "doc-1",
                        "chunk_id": "doc-1-0",
                        "title": "Doc 1",
                        "metadata": {"position": 0},
                    },
                )
            ]

        def lexical_search(self, query, top_k, *, base_id=None, doc_ids=None):
            captured["lexical_search"] = {
                "query": query,
                "top_k": top_k,
                "base_id": base_id,
                "doc_ids": doc_ids,
            }
            return []

    monkeypatch.setattr(retrieve, "build_client", lambda settings: fake_client)
    monkeypatch.setattr(retrieve, "get_store", lambda backend: FakeStore())
    monkeypatch.setitem(retrieve.settings.AGENT_SETTINGS, "hybrid_retrieval", False)
    monkeypatch.setitem(retrieve.settings.AGENT_SETTINGS, "rerank_enabled", False)

    result = retrieve.retrieve_context(query="question", top_k=5, base=base)
    payload = retrieve.retrieve_context_with_diagnostics(query="question", top_k=5, base=base)

    assert result[0]["refs"][0]["doc_id"] == "doc-1"
    assert payload["diagnostics"]["vector_hits"] == 1
    assert captured["count"]["base_id"] == base.pk
    assert captured["search"]["base_id"] == base.pk
    assert captured["search"]["doc_ids"] == ["doc-1"]


@pytest.mark.django_db
def test_retrieve_context_fuses_hybrid_results(monkeypatch):
    user = get_user_model().objects.create_user(username="carl", password="pw123456")
    base = KnowledgeBase.objects.create(user=user, name="kb")
    KnowledgeDocument.objects.create(user=user, base=base, doc_id="doc-1", title="Doc 1")

    fake_client = SimpleNamespace(embed=lambda **kwargs: [[0.1, 0.2, 0.3]])

    class FakeStore:
        def count(self, *, base_id=None, doc_ids=None):
            return 3

        def search(self, embedding, top_k, *, base_id=None, doc_ids=None):
            return [
                (0.9, {"text": "vector hit", "doc_id": "doc-1", "chunk_id": "doc-1-1", "title": "Doc 1", "metadata": {}}),
            ]

        def lexical_search(self, query, top_k, *, base_id=None, doc_ids=None):
            return [
                (1.0, {"text": "lexical hit", "doc_id": "doc-1", "chunk_id": "doc-1-2", "title": "Doc 1", "metadata": {}}),
            ]

    monkeypatch.setattr(retrieve, "build_client", lambda settings: fake_client)
    monkeypatch.setattr(retrieve, "get_store", lambda backend: FakeStore())
    monkeypatch.setitem(retrieve.settings.AGENT_SETTINGS, "hybrid_retrieval", True)
    monkeypatch.setitem(retrieve.settings.AGENT_SETTINGS, "rerank_enabled", False)

    payload = retrieve.retrieve_context_with_diagnostics(query="question", top_k=5, base=base)
    result = payload["results"]

    assert len(result) == 2
    fused_sources = sorted(result[0]["metadata"]["retrieval_sources"] + result[1]["metadata"]["retrieval_sources"])
    assert fused_sources == ["lexical", "vector"]
    assert payload["diagnostics"]["hybrid_enabled"] is True
    assert payload["diagnostics"]["lexical_hits"] == 1


@pytest.mark.django_db
def test_retrieve_context_applies_rerank(monkeypatch):
    user = get_user_model().objects.create_user(username="dora", password="pw123456")
    base = KnowledgeBase.objects.create(user=user, name="kb")
    KnowledgeDocument.objects.create(user=user, base=base, doc_id="doc-1", title="Doc 1")

    fake_client = SimpleNamespace(embed=lambda **kwargs: [[0.1, 0.2, 0.3]])

    class FakeStore:
        def count(self, *, base_id=None, doc_ids=None):
            return 2

        def search(self, embedding, top_k, *, base_id=None, doc_ids=None):
            return [
                (0.4, {"text": "完全不相关", "doc_id": "doc-1", "chunk_id": "doc-1-1", "title": "Doc 1", "metadata": {}, "retrieval_sources": ["vector"]}),
                (0.39, {"text": "question 命中", "doc_id": "doc-1", "chunk_id": "doc-1-2", "title": "Doc 1", "metadata": {}, "retrieval_sources": ["vector"]}),
            ]

        def lexical_search(self, query, top_k, *, base_id=None, doc_ids=None):
            return []

    monkeypatch.setattr(retrieve, "build_client", lambda settings: fake_client)
    monkeypatch.setattr(retrieve, "get_store", lambda backend: FakeStore())
    monkeypatch.setitem(retrieve.settings.AGENT_SETTINGS, "hybrid_retrieval", False)
    monkeypatch.setitem(retrieve.settings.AGENT_SETTINGS, "rerank_enabled", True)

    payload = retrieve.retrieve_context_with_diagnostics(query="question", top_k=2, base=base)

    assert payload["results"][0]["refs"][0]["chunk_id"] == "doc-1-2"
    assert payload["diagnostics"]["rerank_enabled"] is True
