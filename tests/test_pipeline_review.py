import pytest
from django.contrib.auth import get_user_model

from src.core.models import KnowledgeBase, PrestudyJob
from src.services import pipeline


User = get_user_model()


@pytest.mark.django_db
def test_run_pipeline_executes_transparent_review_cycle(monkeypatch):
    user = User.objects.create_user(username="reviewer", password="secret123")
    base = KnowledgeBase.objects.create(user=user, name="Physics")
    job = PrestudyJob.objects.create(user=user, knowledge_base=base, source_type="text", source_excerpt="", status="queued")

    monkeypatch.setattr(pipeline, "build_client", lambda settings_map: object())

    def fake_collect_rag_context(*, job, text, top_k=5):
        return {
            "results": [{"text": f"chunk@{top_k}", "refs": [{"doc_id": "doc-1", "chunk_id": f"c{top_k}"}], "title": "sample"}],
            "diagnostics": {
                "enabled": True,
                "backend": "pgvector",
                "hybrid_enabled": True,
                "rerank_enabled": True,
                "search_k": top_k,
                "final_hits": 1 if top_k == 5 else 2,
                "vector_hits": 2,
                "lexical_hits": 1,
                "source_counts": {"vector": 1, "lexical": 1},
            },
        }

    monkeypatch.setattr(pipeline, "_collect_rag_context", fake_collect_rag_context)

    call_log = []

    def fake_orchestrate_pipeline(*, cycle_label, rag_diagnostics, **kwargs):
        call_log.append({"cycle": cycle_label, "search_k": rag_diagnostics.get("search_k")})
        if cycle_label == "initial":
            return {
                "planner_json": {"title": "牛顿三定律预习课"},
                "final_json": {
                    "title": "牛顿三定律预习课",
                    "knowledge_points": [],
                    "quiz": {"items": []},
                    "evaluation": {"scores": {"overall": 61}, "verdict": "review"},
                    "reflection": {
                        "diagnosis": ["检索证据偏少"],
                        "next_actions": ["扩大召回范围"],
                        "should_regenerate": False,
                        "should_expand_retrieval": True,
                        "should_add_multimodal_review": True,
                    },
                },
                "model_trace": [{"step": "evaluator", "cycle": "initial"}],
                "status": "completed",
            }
        return {
            "planner_json": {"title": "牛顿三定律预习课"},
            "final_json": {
                "title": "牛顿三定律预习课",
                "knowledge_points": [],
                "quiz": {"items": []},
                "evaluation": {"scores": {"overall": 79}, "verdict": "pass"},
                "reflection": {
                    "diagnosis": ["当前证据已经够用"],
                    "next_actions": ["继续补错因建模"],
                    "should_regenerate": False,
                    "should_expand_retrieval": False,
                    "should_add_multimodal_review": True,
                },
            },
            "model_trace": [{"step": "evaluator", "cycle": "review_1"}],
            "status": "completed",
        }

    monkeypatch.setattr(pipeline.runtime, "orchestrate_pipeline", fake_orchestrate_pipeline)

    response = pipeline.run_pipeline(job=job, text="请生成一节牛顿三定律预习课")

    review_summary = response["final_json"]["review_summary"]
    assert review_summary["executed_rounds"] == 1
    assert review_summary["initial_overall_score"] == 61
    assert review_summary["final_overall_score"] == 79
    assert review_summary["pending_multimodal_review"] is True
    assert review_summary["cycles"][0]["top_k"] == 10
    assert review_summary["cycles"][0]["score_delta"] == 18
    assert call_log == [
        {"cycle": "initial", "search_k": 5},
        {"cycle": "review_1", "search_k": 10},
    ]
