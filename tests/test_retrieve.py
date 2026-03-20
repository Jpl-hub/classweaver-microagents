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

    monkeypatch.setattr(retrieve, "build_client", lambda settings: fake_client)
    monkeypatch.setattr(retrieve, "get_store", lambda backend: FakeStore())

    result = retrieve.retrieve_context(query="question", top_k=5, base=base)

    assert result[0]["refs"][0]["doc_id"] == "doc-1"
    assert captured["count"]["base_id"] == base.pk
    assert captured["search"]["base_id"] == base.pk
    assert captured["search"]["doc_ids"] == ["doc-1"]
