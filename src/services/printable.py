from typing import Any, Dict, List


def build_printable_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for printable template rendering."""
    quiz = data.get("quiz", {}) if isinstance(data, dict) else {}
    quiz_items: List[Dict[str, Any]] = quiz.get("items", [])
    knowledge_points = data.get("knowledge_points", [])
    glossary = data.get("glossary", [])
    practice = data.get("practice", {}).get("items", [])

    return {
        "title": data.get("title", "ClassWeaver Printable Pack"),
        "knowledge_points": knowledge_points,
        "glossary": glossary,
        "quiz": quiz_items,
        "practice": practice,
    }
