from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PrestudyJob(TimestampedModel):
    SOURCE_CHOICES = [
        ("text", "Text"),
        ("ppt", "PowerPoint"),
    ]

    source_type = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    source_excerpt = models.TextField(blank=True)
    planner_json = models.JSONField(default=dict, blank=True)
    final_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, default="pending")
    duration_ms = models.PositiveIntegerField(default=0)
    model_trace = models.JSONField(default=dict, blank=True)
    knowledge_doc_ids = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return f"PrestudyJob#{self.pk}"


class QuizSession(TimestampedModel):
    job = models.ForeignKey(PrestudyJob, related_name="sessions", on_delete=models.CASCADE)
    session_id = models.CharField(max_length=64, unique=True)
    questions_snapshot = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"QuizSession#{self.session_id}"


class QuizAnswer(TimestampedModel):
    session = models.ForeignKey(QuizSession, related_name="answers", on_delete=models.CASCADE)
    question_id = models.CharField(max_length=64)
    answer = models.CharField(max_length=8)
    correct = models.BooleanField(default=False)
    used_variant = models.CharField(max_length=16, blank=True)
    kp_ids = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return f"QuizAnswer#{self.pk}"


class LlmCallLog(TimestampedModel):
    job = models.ForeignKey(PrestudyJob, related_name="llm_logs", on_delete=models.CASCADE, null=True, blank=True)
    step = models.CharField(max_length=32)
    provider = models.CharField(max_length=32)
    model = models.CharField(max_length=128)
    base_url = models.URLField()
    latency_ms = models.PositiveIntegerField()
    input_chars = models.PositiveIntegerField()
    output_chars = models.PositiveIntegerField()
    fallback = models.BooleanField(default=False)
    rag_snapshot = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"LlmCallLog#{self.pk}:{self.step}"


class KnowledgeDocument(TimestampedModel):
    doc_id = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    source_path = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.title


class KnowledgeChunk(TimestampedModel):
    document = models.ForeignKey(KnowledgeDocument, related_name="chunks", on_delete=models.CASCADE)
    chunk_id = models.CharField(max_length=64)
    text = models.TextField()
    embedding = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("document", "chunk_id")

    def __str__(self) -> str:
        return f"{self.document.doc_id}:{self.chunk_id}"


class LessonPlan(TimestampedModel):
    """结构化教学计划，供课堂助教与推荐系统复用。"""

    job = models.OneToOneField(PrestudyJob, related_name="lesson_plan", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    structure = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"LessonPlan#{self.pk}:{self.title}"


class LessonEvent(TimestampedModel):
    """课堂事件流水，如提问、投票、练习提交。"""

    plan = models.ForeignKey(LessonPlan, related_name="events", on_delete=models.CASCADE)
    event_type = models.CharField(max_length=64)
    actor = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-occurred_at",)

    def __str__(self) -> str:
        return f"{self.event_type}@{self.occurred_at:%H:%M:%S}"


class RecommendationTask(TimestampedModel):
    """记录基于学习行为生成的个性化推荐任务。"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    job = models.ForeignKey(PrestudyJob, related_name="recommendations", on_delete=models.CASCADE)
    session = models.ForeignKey(QuizSession, related_name="recommendations", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    input_snapshot = models.JSONField(default=dict, blank=True)
    output = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"RecommendationTask#{self.pk}:{self.status}"
