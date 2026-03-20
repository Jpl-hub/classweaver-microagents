from src.services.evaluation import evaluate_citation_cases


def test_evaluate_citation_cases_computes_metrics():
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

    def fake_qa(query: str, top_k: int):
        if query == "q1":
            return {
                "answer": "答案见[1]。",
                "citations": [{"doc_id": "doc-1", "chunk_id": "doc-1-0", "label": "[1]"}],
            }
        return {
            "answer": "这是答案，没有引用。",
            "citations": [{"doc_id": "doc-x", "chunk_id": "doc-x-0", "label": "[1]"}],
        }

    report = evaluate_citation_cases(cases=cases, qa_fn=fake_qa, top_k=4)

    assert report["summary"]["cases"] == 2
    assert report["summary"]["citation_hit_rate"] == 0.5
    assert report["summary"]["citation_marker_rate"] == 0.5
    assert report["cases"][0]["citation_hit"] is True
    assert report["cases"][1]["citation_hit"] is False
