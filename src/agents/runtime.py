import logging
import time
from typing import Any, Dict, List

from .utils import AgentInvocationError


logger = logging.getLogger(__name__)


def orchestrate_pipeline(
    *,
    client,
    planner_module,
    rewriter_module,
    tutor_module,
    text: str,
    rag_chunks: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Coordinate planner -> rewriter -> tutor agents."""
    trace: List[Dict[str, Any]] = []
    planner_payload: Dict[str, Any] = {}
    final_payload: Dict[str, Any] = {}
    tutor_payload: Dict[str, Any] = {}
    pipeline_status = "completed"

    try:
        start = time.perf_counter()
        planner_payload = planner_module.generate_plan(client=client, text=text, rag_chunks=rag_chunks)
        planner_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "planner",
                "provider": "qwen",
                "model": settings["qwen_model"],
                "base_url": settings["base_url"],
                "latency_ms": planner_latency,
                "input_chars": len(text),
                "output_chars": len(str(planner_payload)),
                "rag": {"enabled": bool(rag_chunks), "backend": settings.get("vector_backend")},
                "fallback": False,
            }
        )

        start = time.perf_counter()
        rewriter_error = None
        final_payload = planner_payload.copy()
        try:
            rewritten_payload = rewriter_module.rewrite_quiz(client=client, planner_payload=planner_payload)
            final_payload = rewritten_payload
        except AgentInvocationError as exc:
            rewriter_error = str(exc)
            pipeline_status = "completed_with_fallback"
            logger.warning("Rewriter failed, fallback to planner payload: %s", exc)
        rewriter_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "rewriter",
                "provider": "deepseek",
                "model": settings["deepseek_model"],
                "base_url": settings["base_url"],
                "latency_ms": rewriter_latency,
                "input_chars": len(str(planner_payload)),
                "output_chars": len(str(final_payload)),
                "rag": {"enabled": bool(rag_chunks), "backend": settings.get("vector_backend")},
                "fallback": bool(rewriter_error),
                "error": rewriter_error,
            }
        )

        start = time.perf_counter()
        tutor_error = None
        tutor_payload = {}
        try:
            tutor_payload = tutor_module.build_tutor_response(
                client=client,
                final_quiz=final_payload,
                answers={},
                rag_chunks=rag_chunks,
            )
        except AgentInvocationError as exc:
            tutor_error = str(exc)
            pipeline_status = "completed_with_fallback"
            logger.warning("Tutor failed, fallback to basic summary: %s", exc)
            tutor_payload = {
                "summary": "Tutor 模块暂时不可用，请稍后重试。",
                "practice": [],
                "followups": ["你可以继续在聊天框追问或重新生成。"],
            }
        tutor_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "tutor",
                "provider": "qwen",
                "model": settings["qwen_model"],
                "base_url": settings["base_url"],
                "latency_ms": tutor_latency,
                "input_chars": len(str(final_payload)),
                "output_chars": len(str(tutor_payload)),
                "rag": {"enabled": bool(rag_chunks), "backend": settings.get("vector_backend")},
                "fallback": bool(tutor_error),
                "error": tutor_error,
            }
        )
    except AgentInvocationError as exc:
        logger.error("Agent invocation error: %s", exc)
        raise

    combined_final = final_payload.copy()
    combined_final.setdefault("tutor", tutor_payload)

    return {
        "planner_json": planner_payload,
        "final_json": combined_final,
        "model_trace": trace,
        "status": pipeline_status,
    }
