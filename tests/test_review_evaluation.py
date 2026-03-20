from src.services.evaluation import evaluate_review_cases


def test_evaluate_review_cases_reports_review_deltas():
    def fake_review_fn(text: str):
        if "牛顿" in text:
            return {
                "final_json": {
                    "evaluation": {
                        "scores": {"overall": 80, "groundedness": 84, "learner_fit": 78},
                    },
                    "review_summary": {
                        "executed_rounds": 1,
                        "initial_overall_score": 62,
                        "final_overall_score": 80,
                        "pending_multimodal_review": True,
                        "cycles": [
                            {
                                "strategy": "full_pipeline",
                                "initial_evaluation": {
                                    "scores": {"overall": 62, "groundedness": 65, "learner_fit": 60}
                                },
                                "evaluation": {
                                    "scores": {"overall": 80, "groundedness": 84, "learner_fit": 78}
                                },
                                "accepted": True,
                            }
                        ],
                    },
                }
            }
        return {
            "final_json": {
                "evaluation": {
                    "scores": {"overall": 70, "groundedness": 73, "learner_fit": 72},
                },
                "review_summary": {},
            }
        }

    report = evaluate_review_cases(
        cases=[
            {"text": "请生成牛顿三定律预习课"},
            {"text": "请生成欧姆定律预习课"},
        ],
        review_fn=fake_review_fn,
    )

    assert report["summary"]["cases"] == 2
    assert report["summary"]["review_trigger_rate"] == 0.5
    assert report["summary"]["review_execution_rate"] == 0.5
    assert report["summary"]["avg_score_delta"] == 9.0
    assert report["summary"]["avg_groundedness_delta"] == 9.5
    assert report["summary"]["avg_learner_fit_delta"] == 9.0
    assert report["summary"]["review_accept_rate"] == 0.5
    assert report["cases"][0]["strategy"] == "full_pipeline"
    assert report["cases"][0]["pending_multimodal_review"] is True
    assert report["cases"][0]["accepted"] is True
    assert report["cases"][1]["triggered_review"] is False
