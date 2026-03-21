from types import SimpleNamespace

from src.services.recommendation import generate_recommendations


def test_generate_recommendations_prioritizes_issue_driven_actions():
    job = SimpleNamespace(
        pk=1,
        lesson_plan=SimpleNamespace(pk=7),
        final_json={
            "evaluation": {
                "primary_issue": "retrieval_gap",
                "issue_tags": ["retrieval_gap", "quiz_gap"],
                "missing_evidence": ["关键概念缺少稳定引用"],
            },
            "reflection": {
                "should_add_multimodal_review": True,
            },
            "review_summary": {
                "pending_multimodal_review": True,
            },
            "knowledge_points": [
                {"id": "kp1", "title": "牛顿第一定律", "summary": "惯性与运动状态"},
            ],
            "quiz": {
                "items": [
                    {"id": "q1", "question": "什么是惯性？", "kp_ids": ["kp1"]},
                ]
            },
        },
    )

    payload = generate_recommendations(job=job)

    assert payload["suggestions"][0]["title"] == "先补证据再继续"
    assert payload["suggestions"][0]["reason"].startswith("系统评测发现")
    assert payload["suggestions"][0]["issue_tags"] == ["retrieval_gap", "quiz_gap"]
    assert payload["suggestions"][1]["title"] == "考虑补充图示或板书材料"
    assert any(item["title"] == "牛顿第一定律" for item in payload["suggestions"])
