from __future__ import annotations

import logging
from datetime import timedelta
from time import perf_counter
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from src.agents import planner, rewriter, runtime, tutor
from src.agents.utils import build_client
from src.core.models import LessonEvent, LessonPlan, LlmCallLog, PrestudyJob
from src.kb import retrieve

from . import printable
from .ppt import extract_text

logger = logging.getLogger(__name__)


def _collect_rag_context(text: str, *, top_k: int = 5, doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    if not settings.AGENT_SETTINGS.get("rag_enabled", True):
        return []

    try:
        return retrieve.retrieve_context(query=text, top_k=top_k, doc_ids=doc_ids)
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
    doc_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute planner -> rewriter -> tutor pipeline for a prestudy job."""
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
    rag_chunks = _collect_rag_context(extracted_text, top_k=5, doc_ids=doc_ids)

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
    lesson_plan_snapshot = _ensure_lesson_plan(job)

    _persist_model_trace(job=job, trace=pipeline_result.get("model_trace", []))

    response_payload = {
        "id": str(job.pk),
        "status": job.status,
        "planner_json": job.planner_json,
        "final_json": job.final_json,
        "model_trace": job.model_trace,
        "duration_ms": duration_ms,
        "printable": printable_payload,
        "lesson_plan": lesson_plan_snapshot,
    }
    return response_payload


def _persist_model_trace(*, job: PrestudyJob, trace: List[Dict[str, Any]]) -> None:
    if not trace:
        return
    log_entries: List[LlmCallLog] = []
    for segment in trace:
        log_entries.append(
            LlmCallLog(
                job=job,
                step=str(segment.get("step", ""))[:32],
                provider=str(segment.get("provider", ""))[:32],
                model=str(segment.get("model", ""))[:128],
                base_url=str(segment.get("base_url", ""))[:200],
                latency_ms=int(segment.get("latency_ms", 0) or 0),
                input_chars=int(segment.get("input_chars", 0) or 0),
                output_chars=int(segment.get("output_chars", 0) or 0),
                fallback=bool(segment.get("fallback", False)),
                rag_snapshot=segment.get("rag") or {},
            )
        )
    LlmCallLog.objects.bulk_create(log_entries)


def _ensure_lesson_plan(job: PrestudyJob) -> Dict[str, Any] | None:
    final_payload = job.final_json or {}
    structure = final_payload.get("lesson_plan") or {
        "focus": final_payload.get("knowledge_points", []),
        "quiz": final_payload.get("quiz", {}).get("items", []),
        "glossary": final_payload.get("glossary", []),
    }
    title = final_payload.get("title") or f"课堂计划 #{job.pk}"

    plan, _created = LessonPlan.objects.update_or_create(
        job=job,
        defaults={
            "title": title,
            "structure": structure,
            "notes": final_payload.get("summary", ""),
        },
    )
    _seed_lesson_events(plan=plan, structure=structure)
    return {"id": plan.pk, "title": plan.title, "structure": plan.structure, "notes": plan.notes}


def _seed_lesson_events(*, plan: LessonPlan, structure: Dict[str, Any]) -> None:
    if plan.events.exists():
        return

    events: List[LessonEvent] = []
    timeline = structure or {}
    focus_points = timeline.get("focus") or timeline.get("knowledge_points") or []
    quiz_items: List[Dict[str, Any]] = []
    quiz_block = timeline.get("quiz")
    if isinstance(quiz_block, dict):
        quiz_items = quiz_block.get("items", []) or []

    current_time = timezone.now()

    def enqueue(event_type: str, payload: Dict[str, Any]) -> None:
        nonlocal current_time
        events.append(
            LessonEvent(
                plan=plan,
                event_type=event_type,
                actor="系统",
                payload=payload,
                occurred_at=current_time,
            )
        )
        current_time += timedelta(minutes=5)

    enqueue("课堂准备", {"note": "自动生成课堂节奏"})
    for point in focus_points[:8]:
        enqueue(
            "知识点讲解",
            {"title": point.get("title"), "summary": point.get("summary")},
        )
    for quiz in quiz_items[:5]:
        enqueue(
            "课堂提问",
            {"question": quiz.get("question"), "difficulty": quiz.get("difficulty")},
        )

    if events:
        LessonEvent.objects.bulk_create(events)
