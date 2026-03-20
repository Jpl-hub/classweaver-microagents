from src.services.evaluation import evaluate_retrieval_cases


def test_evaluate_retrieval_cases_computes_metrics():
    cases = [
        {
            "query": "q1",
            "expected_refs": [{"doc_id": "doc-1", "chunk_id": "doc-1-0"}],
        },
        {
            "query": "q2",
            "expected_refs": [{"doc_id": "doc-2", "chunk_id": "doc-2-0"}],
        },
    ]

    def fake_retrieve(query: str, top_k: int):
        if query == "q1":
            return [{"refs": [{"doc_id": "doc-1", "chunk_id": "doc-1-0"}]}]
        return [{"refs": [{"doc_id": "doc-x", "chunk_id": "doc-x-0"}]}]

    report = evaluate_retrieval_cases(cases=cases, retrieve_fn=fake_retrieve, top_k=5)

    assert report["summary"]["cases"] == 2
    assert report["summary"]["hit_rate"] == 0.5
    assert report["summary"]["mrr"] == 0.5
    assert report["cases"][0]["hit"] is True
    assert report["cases"][1]["hit"] is False
