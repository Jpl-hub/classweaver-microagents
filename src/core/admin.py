from django.contrib import admin

from .models import KnowledgeChunk, KnowledgeDocument, LlmCallLog, PrestudyJob, QuizAnswer, QuizSession


@admin.register(PrestudyJob)
class PrestudyJobAdmin(admin.ModelAdmin):
    list_display = ("id", "source_type", "status", "duration_ms", "created_at")
    list_filter = ("source_type", "status", "created_at")
    search_fields = ("id", "source_excerpt")


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "job", "started_at", "ended_at")
    search_fields = ("session_id",)
    autocomplete_fields = ("job",)


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "question_id", "answer", "correct")
    list_filter = ("correct",)
    search_fields = ("question_id",)
    autocomplete_fields = ("session",)


@admin.register(LlmCallLog)
class LlmCallLogAdmin(admin.ModelAdmin):
    list_display = ("id", "step", "provider", "model", "latency_ms", "fallback", "created_at")
    list_filter = ("step", "provider", "fallback")
    search_fields = ("model",)
    autocomplete_fields = ("job",)


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_id", "title", "created_at")
    search_fields = ("doc_id", "title")


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_id", "created_at")
    search_fields = ("chunk_id", "text")
    autocomplete_fields = ("document",)
