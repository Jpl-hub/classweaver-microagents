import logging
from time import perf_counter
from typing import Any, Dict, List, Optional

from django.conf import settings

from src.agents import planner, rewriter, runtime, tutor
from src.agents.utils import build_client
from src.core.models import PrestudyJob
from src.kb import retrieve

from . import printable
from .ppt import extract_text

logger = logging.getLogger(__name__)


def _collect_rag_context(text: str, *, top_k: int = 5) -> List[Dict[str, Any]]:
    if not settings.AGENT_SETTINGS.get("rag_enabled", True):
        return []

    try:
        return retrieve.retrieve_context(query=text, top_k=top_k)
    except NotImplementedError:
        logger.debug("RAG retrieval not implemented yet; continuing without context.")
        return []
    except Exception:  # noqa: BLE001
        logger.exception("Failed to retrieve RAG context; proceeding without it.")
        return []


def run_pipeline(
    *,
    job: PrestudyJob,
    text: Optional[str] = None,
    ppt_file: Any | None = None,
) -> Dict[str, Any]:
    """Execute planner → rewriter → tutor pipeline for a prestudy job."""
    if text is None and ppt_file is None:
        raise ValueError("Either text or ppt_file must be provided.")

    if ppt_file is not None:
        extracted_text = extract_text(ppt_file)
        job.source_type = "ppt"
    else:
        extracted_text = (text or "").strip()
        job.source_type = "text"

    if not extracted_text:
        raise ValueError("Failed to obtain content for pipeline execution.")

    job.source_excerpt = extracted_text[:1024]
    job.save(update_fields=["source_type", "source_excerpt"])

    agent_settings = settings.AGENT_SETTINGS
    client = build_client(agent_settings)
    rag_chunks = _collect_rag_context(extracted_text, top_k=5)

    start = perf_counter()
    pipeline_result = runtime.orchestrate_pipeline(
        client=client,
        planner_module=planner,
        rewriter_module=rewriter,
        tutor_module=tutor,
        text=extracted_text,
        rag_chunks=rag_chunks,
        settings=agent_settings,
    )
    duration_ms = int((perf_counter() - start) * 1000)

    job.planner_json = pipeline_result.get("planner_json", {})
    job.final_json = pipeline_result.get("final_json", {})
    job.model_trace = pipeline_result.get("model_trace", {})
    job.status = pipeline_result.get("status", "completed")
    job.duration_ms = duration_ms
    job.save(update_fields=["planner_json", "final_json", "model_trace", "status", "duration_ms"])

    printable_payload = pipeline_result.get("printable") or printable.build_printable_payload(job.final_json)

    response_payload = {
        "id": str(job.pk),
        "status": job.status,
        "planner_json": job.planner_json,
        "final_json": job.final_json,
        "model_trace": job.model_trace,
        "duration_ms": duration_ms,
        "printable": printable_payload,
    }
    return response_payload
