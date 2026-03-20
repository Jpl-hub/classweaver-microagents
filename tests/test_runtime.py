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


class _EvaluatorModule:
    @staticmethod
    def build_quality_report(**kwargs):
        return {
            "evaluation": {"verdict": "review", "scores": {"overall": 72}},
            "reflection": {"diagnosis": ["证据覆盖一般"], "next_actions": ["补更多引用"]},
        }


def test_orchestrate_pipeline_fails_when_rewriter_fails():
    with pytest.raises(AgentInvocationError):
        orchestrate_pipeline(
            client=object(),
            planner_module=_PlannerModule,
            rewriter_module=_RewriterModule,
            tutor_module=_TutorModule,
            evaluator_module=_EvaluatorModule,
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


def test_orchestrate_pipeline_includes_evaluation_and_reflection():
    class _RewriterOkModule:
        @staticmethod
        def rewrite_quiz(**kwargs):
            return {"title": "plan", "quiz": {"items": []}}

    result = orchestrate_pipeline(
        client=object(),
        planner_module=_PlannerModule,
        rewriter_module=_RewriterOkModule,
        tutor_module=_TutorModule,
        evaluator_module=_EvaluatorModule,
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

    assert result["final_json"]["evaluation"]["verdict"] == "review"
    assert result["final_json"]["reflection"]["diagnosis"] == ["证据覆盖一般"]
    assert [segment["step"] for segment in result["model_trace"]] == ["planner", "rewriter", "tutor", "evaluator"]
