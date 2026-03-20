from src.services.citations import build_citations, extract_citation_markers


def test_build_citations_deduplicates_refs():
    entries = [
        {
            "text": "alpha",
            "score": 0.9,
            "title": "Doc A",
            "refs": [{"doc_id": "doc-a", "chunk_id": "doc-a-0"}],
        },
        {
            "text": "alpha duplicate",
            "score": 0.8,
            "title": "Doc A",
            "refs": [{"doc_id": "doc-a", "chunk_id": "doc-a-0"}],
        },
    ]

    citations = build_citations(entries)

    assert len(citations) == 1
    assert citations[0]["doc_id"] == "doc-a"
    assert citations[0]["label"] == "[1]"

def test_extract_citation_markers_reads_bracket_indices():
    assert extract_citation_markers("答案见[1]，补充见[2]。") == [1, 2]
