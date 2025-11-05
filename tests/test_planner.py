from src.agents.planner import PlannerResponse


def test_planner_response_normalizes_string_refs():
    payload = {
        "title": "Deep Learning Study Plan",
        "summary": "Focus on foundational concepts and practice questions.",
        "knowledge_points": [{"id": "kp1", "title": "Neural Networks"}],
        "glossary": [{"term": "Gradient Descent", "definition": "Optimization method."}],
        "quiz": {
            "items": [
                {
                    "id": "q1",
                    "question": "Which component is central to CNNs?",
                    "options": {"A": "Convolution", "B": "Perceptron", "C": "Recurrent cell", "D": "Transformer"},
                    "answer": "A",
                    "refs": "123abc-0",
                }
            ]
        },
    }

    validated = PlannerResponse.model_validate(payload)

    refs = validated.quiz.items[0].refs
    assert refs == [{"doc_id": "123abc", "chunk_id": "123abc-0"}]


def test_planner_response_ignores_invalid_refs():
    payload = {
        "title": "Plan",
        "summary": "Summary",
        "knowledge_points": [],
        "glossary": [],
        "quiz": {
            "items": [
                {
                    "id": "q1",
                    "question": "Test",
                    "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                    "answer": "B",
                    "refs": ["", None, {"doc_id": "doc", "chunk_id": "doc-0"}],
                }
            ]
        },
    }

    validated = PlannerResponse.model_validate(payload)

    refs = validated.quiz.items[0].refs
    assert refs == [{"doc_id": "doc", "chunk_id": "doc-0"}]
