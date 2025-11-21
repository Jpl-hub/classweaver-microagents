from rest_framework import serializers


class PrestudyTextSerializer(serializers.Serializer):
    text = serializers.CharField()
    doc_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    def validate_text(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Text content cannot be empty.")
        return cleaned


class PrestudyResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    planner_json = serializers.JSONField()
    final_json = serializers.JSONField()
    model_trace = serializers.JSONField()
    duration_ms = serializers.IntegerField()
    printable = serializers.JSONField(required=False)
    lesson_plan = serializers.JSONField(required=False)


class PrestudyJobStatusSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    detail = serializers.CharField(required=False, allow_blank=True)
    estimated_wait_sec = serializers.IntegerField(required=False)


class QuizStartRequestSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()


class QuizAnswerSerializer(serializers.Serializer):
    id = serializers.CharField()
    answer = serializers.CharField(max_length=1)

    def validate_answer(self, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"A", "B", "C", "D"}:
            raise serializers.ValidationError("Answer must be one of A, B, C, or D.")
        return normalized


class QuizSubmitRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    answers = QuizAnswerSerializer(many=True)

    def validate_answers(self, value: list[dict]) -> list[dict]:
        seen = set()
        for item in value:
            qid = str(item.get("id"))
            if qid in seen:
                raise serializers.ValidationError(f"Duplicate answer detected for question {qid}.")
            seen.add(qid)
        return value


class KnowledgeSearchSerializer(serializers.Serializer):
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
    doc_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)


class LessonEventSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=64)
    actor = serializers.CharField(max_length=64, allow_blank=True, required=False)
    payload = serializers.JSONField(required=False)


class RecommendationTriggerSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    session_id = serializers.CharField(required=False, allow_blank=True)


class RecommendationTaskSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    output = serializers.JSONField(required=False)
