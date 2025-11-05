import pytest

from src.api.serializers import QuizSubmitRequestSerializer


def test_quiz_submit_serializer_rejects_duplicate_answers():
    payload = {
        "session_id": "session-1",
        "answers": [
            {"id": "q1", "answer": "A"},
            {"id": "q1", "answer": "B"},
        ],
    }
    serializer = QuizSubmitRequestSerializer(data=payload)
    assert not serializer.is_valid()
    assert "duplicate" in str(serializer.errors).lower()


@pytest.mark.parametrize("answer", ["a", "B", "c", "D"])
def test_quiz_answer_serializer_normalizes_case(answer):
    serializer = QuizSubmitRequestSerializer(
        data={"session_id": "session-1", "answers": [{"id": "q1", "answer": answer}]}
    )
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated["answers"][0]["answer"] in {"A", "B", "C", "D"}
