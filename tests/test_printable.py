from src.services.printable import build_printable_payload


def test_build_printable_payload_enriches_refs_from_sources():
    payload = build_printable_payload(
        {
            "title": "牛顿三定律预习课",
            "knowledge_points": [
                {
                    "id": "kp-1",
                    "title": "牛顿第二定律",
                    "summary": "F=ma",
                    "refs": [{"doc_id": "doc-1", "chunk_id": "chunk-1"}],
                }
            ],
            "tutor": {
                "practice": [
                    {
                        "prompt": "求加速度",
                        "citations": [{"doc_id": "doc-1", "chunk_id": "chunk-1"}],
                    }
                ]
            },
            "sources": [
                {
                    "label": "[1]",
                    "doc_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "title": "sample-physics",
                    "text": "物体所受合外力等于质量乘以加速度。",
                }
            ],
        }
    )

    point_ref = payload["knowledge_points"][0]["refs"][0]
    practice_citation = payload["practice"][0]["citations"][0]

    assert point_ref["title"] == "sample-physics"
    assert point_ref["label"] == "[1]"
    assert practice_citation["title"] == "sample-physics"
    assert practice_citation["text"] == "物体所受合外力等于质量乘以加速度。"
