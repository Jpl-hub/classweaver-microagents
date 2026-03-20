from typing import Any, Dict, List

from .citations import normalize_citation


def _citation_key(doc_id: Any, chunk_id: Any) -> tuple[str, str]:
    normalized = normalize_citation({"doc_id": doc_id, "chunk_id": chunk_id})
    return (str(normalized.get("doc_id") or ""), str(normalized.get("chunk_id") or ""))


def _enrich_ref(ref: Dict[str, Any], source_lookup: Dict[tuple[str, str], Dict[str, Any]], doc_lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(ref, dict):
        return ref
    normalized = normalize_citation(ref)
    doc_id = normalized.get("doc_id")
    chunk_id = normalized.get("chunk_id")
    source = source_lookup.get(_citation_key(doc_id, chunk_id))
    doc_source = doc_lookup.get(str(doc_id or ""))
    title = ref.get("title") or (source or {}).get("title") or (doc_source or {}).get("title") or ""
    label = ref.get("label") or (source or {}).get("label")
    text = ref.get("text") or (source or {}).get("text") or ""
    enriched = {**ref, "doc_id": doc_id, "chunk_id": chunk_id}
    if title:
        enriched["title"] = title
    if label:
        enriched["label"] = label
    if text:
        enriched["text"] = text
    return enriched


def _enrich_knowledge_points(points: List[Dict[str, Any]], source_lookup: Dict[tuple[str, str], Dict[str, Any]], doc_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched_points: List[Dict[str, Any]] = []
    for point in points:
        refs = point.get("refs") or []
        enriched_points.append(
            {
                **point,
                "refs": [_enrich_ref(ref, source_lookup, doc_lookup) for ref in refs if isinstance(ref, dict)],
            }
        )
    return enriched_points


def _enrich_practice(practice_items: List[Dict[str, Any]], source_lookup: Dict[tuple[str, str], Dict[str, Any]], doc_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched_practice: List[Dict[str, Any]] = []
    for item in practice_items:
        citations = item.get("citations") or []
        enriched_practice.append(
            {
                **item,
                "citations": [_enrich_ref(citation, source_lookup, doc_lookup) for citation in citations if isinstance(citation, dict)],
            }
        )
    return enriched_practice


def build_printable_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for printable template rendering."""
    quiz = data.get("quiz", {}) if isinstance(data, dict) else {}
    quiz_items: List[Dict[str, Any]] = quiz.get("items", [])
    sources = data.get("sources", [])
    source_lookup = {
        _citation_key(source.get("doc_id"), source.get("chunk_id")): source
        for source in sources
        if isinstance(source, dict)
    }
    doc_lookup = {
        str(source.get("doc_id") or ""): source
        for source in sources
        if isinstance(source, dict) and source.get("doc_id")
    }
    knowledge_points = _enrich_knowledge_points(data.get("knowledge_points", []), source_lookup, doc_lookup)
    glossary = data.get("glossary", [])
    practice = data.get("practice", {}).get("items", [])
    if not practice:
        practice = data.get("tutor", {}).get("practice", [])
    practice = _enrich_practice(practice, source_lookup, doc_lookup)

    return {
        "title": data.get("title", "ClassWeaver Printable Pack"),
        "knowledge_points": knowledge_points,
        "glossary": glossary,
        "quiz": quiz_items,
        "practice": practice,
        "sources": sources,
    }
