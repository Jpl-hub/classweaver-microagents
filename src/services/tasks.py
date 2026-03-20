from __future__ import annotations

import io
import logging
import base64

from celery import shared_task
from django.db import close_old_connections
from django.utils import timezone

from src.agents.utils import AgentInvocationError
from src.core.models import PrestudyJob

from . import pipeline

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(AgentInvocationError,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def run_prestudy_job_task(self, *, job_id: int, text: str | None = None, ppt_payload: str | None = None, filename: str = "") -> None:
    close_old_connections()
    try:
        job = PrestudyJob.objects.get(pk=job_id)
    except PrestudyJob.DoesNotExist:
        logger.warning("Prestudy job %s vanished before pipeline execution", job_id)
        return

    ppt_file = None
    if ppt_payload:
        ppt_file = io.BytesIO(base64.b64decode(ppt_payload.encode("ascii")))
        ppt_file.name = filename or f"job-{job_id}.pptx"

    try:
        job.status = "processing"
        job.attempts += 1
        job.started_at = timezone.now()
        job.save(update_fields=["status", "attempts", "started_at"])
        pipeline.run_pipeline(job=job, text=text, ppt_file=ppt_file)
        job.finished_at = timezone.now()
        job.error_message = ""
        job.save(update_fields=["finished_at", "error_message"])
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prestudy pipeline failed for job %s", job_id)
        job.status = "failed"
        job.finished_at = timezone.now()
        job.final_json = {}
        job.model_trace = [{"step": "pipeline", "error": str(exc)}]
        job.error_message = str(exc)
        job.save(update_fields=["status", "finished_at", "final_json", "model_trace", "error_message"])
        raise
    finally:
        close_old_connections()
