from types import SimpleNamespace

from src.services import qa


def test_answer_question_builds_followup(monkeypatch):
    monkeypatch.setattr(
        qa.kb_retrieve,
        "retrieve_context_with_diagnostics",
        lambda **kwargs: {
            "results": [
                {
                    "text": "牛顿第一定律说明物体在不受外力时保持静止或匀速直线运动。",
                    "title": "sample-physics",
                    "score": 0.92,
                    "refs": [{"doc_id": "doc-1", "chunk_id": "doc-1-0"}],
                }
            ],
            "diagnostics": {
                "final_hits": 1,
                "hybrid_enabled": True,
                "rerank_enabled": True,
                "source_counts": {"vector": 1, "lexical": 1},
            },
        },
    )
    monkeypatch.setattr(qa, "build_client", lambda config: SimpleNamespace(chat=lambda **kwargs: "惯性描述了保持原有运动状态的趋势[1]。"))

    payload = qa.answer_question(question="什么是惯性", base=object(), top_k=4)

    assert payload["followup"]["confidence"]["label"] in {"中等把握", "中高把握", "高把握"}
    assert "sample-physics" in payload["followup"]["evidence_summary"]
    assert len(payload["followup"]["next_steps"]) == 3
    assert any("小测" in item for item in payload["followup"]["suggested_questions"])


def test_answer_question_returns_careful_followup_when_no_context(monkeypatch):
    monkeypatch.setattr(
        qa.kb_retrieve,
        "retrieve_context_with_diagnostics",
        lambda **kwargs: {
            "results": [],
            "diagnostics": {"final_hits": 0, "hybrid_enabled": True},
        },
    )

    payload = qa.answer_question(question="什么是冲量定理", base=object(), top_k=4)

    assert payload["answer"] == "知识库中没有找到相关内容。"
    assert payload["followup"]["confidence"]["label"] == "谨慎参考"
    assert "没有命中" in payload["followup"]["evidence_summary"]
    assert any("换一种问法" in item for item in payload["followup"]["next_steps"])
