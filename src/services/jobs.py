import io
import logging
import threading
from typing import Optional

from django.db import close_old_connections

from src.core.models import PrestudyJob

from . import pipeline

logger = logging.getLogger(__name__)


def enqueue_prestudy_job(
    *,
    job: PrestudyJob,
    text: Optional[str] = None,
    ppt_bytes: Optional[bytes] = None,
    filename: str = "",
) -> None:
    """Dispatch prestudy pipeline到后台线程，避免阻塞请求。"""

    job.status = "queued"
    job.save(update_fields=["status"])

    thread = threading.Thread(
        target=_run_prestudy_job,
        args=(job.pk, text, ppt_bytes, filename),
        name=f"prestudy-job-{job.pk}",
        daemon=True,
    )
    thread.start()


def _run_prestudy_job(job_id: int, text: Optional[str], ppt_bytes: Optional[bytes], filename: str) -> None:
    close_old_connections()
    try:
        job = PrestudyJob.objects.get(pk=job_id)
    except PrestudyJob.DoesNotExist:
        logger.warning("Prestudy job %s vanished before执行 pipeline", job_id)
        return

    ppt_file = None
    if ppt_bytes:
        ppt_file = io.BytesIO(ppt_bytes)
        ppt_file.name = filename or f"job-{job_id}.pptx"

    try:
        job.status = "processing"
        job.save(update_fields=["status"])
        pipeline.run_pipeline(job=job, text=text, ppt_file=ppt_file)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prestudy pipeline failed for job %s", job_id)
        job.status = "failed"
        job.final_json = {}
        job.model_trace = [{"step": "pipeline", "error": str(exc)}]
        job.save(update_fields=["status", "final_json", "model_trace"])
    finally:
        close_old_connections()
