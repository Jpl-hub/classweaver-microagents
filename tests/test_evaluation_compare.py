from src.services.evaluation import build_report_metadata, compare_report_summaries


def test_build_report_metadata_contains_basic_fields():
    metadata = build_report_metadata(report_type="retrieval", dataset="demo.json", top_k=5)

    assert metadata["report_type"] == "retrieval"
    assert metadata["dataset"] == "demo.json"
    assert metadata["top_k"] == 5
    assert "generated_at" in metadata


def test_compare_report_summaries_calculates_numeric_deltas():
    diff = compare_report_summaries(
        baseline={"summary": {"hit_rate": 0.5, "cases": 10}, "config": {"label": "dense"}},
        candidate={"summary": {"hit_rate": 0.8, "cases": 10}, "config": {"label": "hybrid"}},
    )

    assert diff["baseline"]["label"] == "dense"
    assert diff["candidate"]["label"] == "hybrid"
    assert diff["metrics"]["hit_rate"]["delta"] == 0.3
    assert diff["metrics"]["cases"]["delta"] == 0.0
