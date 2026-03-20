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
    evaluator_module,
    text: str,
    rag_chunks: List[Dict[str, Any]],
    rag_diagnostics: Dict[str, Any],
    settings: Dict[str, Any],
    cycle_label: str = "initial",
) -> Dict[str, Any]:
    """Coordinate planner -> rewriter -> tutor agents."""
    trace: List[Dict[str, Any]] = []
    planner_payload: Dict[str, Any]
    final_payload: Dict[str, Any]
    tutor_payload: Dict[str, Any]
    evaluator_payload: Dict[str, Any]
    rag_snapshot = {"enabled": bool(rag_chunks), "backend": settings.get("vector_backend"), **(rag_diagnostics or {})}

    try:
        start = time.perf_counter()
        planner_payload = planner_module.generate_plan(client=client, text=text, rag_chunks=rag_chunks)
        planner_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "planner",
                "cycle": cycle_label,
                "provider": "qwen",
                "model": settings["qwen_model"],
                "base_url": settings["base_url"],
                "latency_ms": planner_latency,
                "input_chars": len(text),
                "output_chars": len(str(planner_payload)),
                "rag": rag_snapshot,
            }
        )

        start = time.perf_counter()
        final_payload = rewriter_module.rewrite_quiz(client=client, planner_payload=planner_payload)
        rewriter_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "rewriter",
                "cycle": cycle_label,
                "provider": "deepseek",
                "model": settings["deepseek_model"],
                "base_url": settings["base_url"],
                "latency_ms": rewriter_latency,
                "input_chars": len(str(planner_payload)),
                "output_chars": len(str(final_payload)),
                "rag": rag_snapshot,
            }
        )

        start = time.perf_counter()
        tutor_payload = tutor_module.build_tutor_response(
            client=client,
            final_quiz=final_payload,
            answers={},
            rag_chunks=rag_chunks,
        )
        tutor_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "tutor",
                "cycle": cycle_label,
                "provider": "qwen",
                "model": settings["qwen_model"],
                "base_url": settings["base_url"],
                "latency_ms": tutor_latency,
                "input_chars": len(str(final_payload)),
                "output_chars": len(str(tutor_payload)),
                "rag": rag_snapshot,
            }
        )

        start = time.perf_counter()
        evaluator_payload = evaluator_module.build_quality_report(
            client=client,
            text=text,
            planner_payload=planner_payload,
            final_payload=final_payload,
            tutor_payload=tutor_payload,
            rag_chunks=rag_chunks,
            rag_diagnostics=rag_diagnostics,
        )
        evaluator_latency = int((time.perf_counter() - start) * 1000)
        trace.append(
            {
                "orchestrator": "pipeline",
                "step": "evaluator",
                "cycle": cycle_label,
                "provider": "qwen",
                "model": settings["qwen_model"],
                "base_url": settings["base_url"],
                "latency_ms": evaluator_latency,
                "input_chars": len(str(final_payload)) + len(str(tutor_payload)),
                "output_chars": len(str(evaluator_payload)),
                "rag": rag_snapshot,
            }
        )
    except AgentInvocationError as exc:
        logger.error("Agent invocation error: %s", exc)
        raise

    combined_final = final_payload.copy()
    combined_final.setdefault("tutor", tutor_payload)
    combined_final["evaluation"] = evaluator_payload.get("evaluation", {})
    combined_final["reflection"] = evaluator_payload.get("reflection", {})

    return {
        "planner_json": planner_payload,
        "final_json": combined_final,
        "model_trace": trace,
        "status": "completed",
    }
