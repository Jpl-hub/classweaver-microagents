import pytest

from src.agents.runtime import orchestrate_pipeline
from src.agents.utils import AgentInvocationError


class _PlannerModule:
    @staticmethod
    def generate_plan(**kwargs):
        return {"title": "plan", "quiz": {"items": []}}


class _RewriterModule:
    @staticmethod
    def rewrite_quiz(**kwargs):
        raise AgentInvocationError("rewriter boom")


class _TutorModule:
    @staticmethod
    def build_tutor_response(**kwargs):
        return {"summary": {}, "practice": [], "followups": []}


def test_orchestrate_pipeline_fails_when_rewriter_fails():
    with pytest.raises(AgentInvocationError):
        orchestrate_pipeline(
            client=object(),
            planner_module=_PlannerModule,
            rewriter_module=_RewriterModule,
            tutor_module=_TutorModule,
            text="hello",
            rag_chunks=[],
            rag_diagnostics={},
            settings={
                "qwen_model": "gpt-4.1-mini",
                "deepseek_model": "gpt-4.1-mini",
                "base_url": "https://example.com/v1",
                "vector_backend": "pgvector",
            },
        )
