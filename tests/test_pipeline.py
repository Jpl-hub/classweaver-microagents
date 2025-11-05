from src.services.scoring import score_quiz


def test_score_quiz_returns_diagnostics():
    questions = [
        {
            "id": "q1",
            "question": "What is 2+2?",
            "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
            "answer": "B",
            "difficulty": "easy",
            "kp_ids": ["kp_math"],
        },
        {
            "id": "q2",
            "question": "Capital of France?",
            "options": {"A": "Berlin", "B": "Rome", "C": "Paris", "D": "Madrid"},
            "answer": "C",
            "difficulty": "medium",
            "kp_ids": ["kp_geo"],
        },
    ]
    answers = [
        {"id": "q1", "answer": "B"},
        {"id": "q2", "answer": "A"},
    ]

    result = score_quiz(questions=questions, answers=answers)

    assert result["score"] == 50
    assert result["diagnostics"]["kp_stats"]["kp_math"]["correct"] == 1
    assert result["diagnostics"]["kp_stats"]["kp_geo"]["correct"] == 0
    assert result["review_card"]["focus"] == ["kp_geo"]
