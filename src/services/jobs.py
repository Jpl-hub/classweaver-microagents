import logging
import base64
from typing import Optional

from django.utils import timezone

from src.core.models import PrestudyJob

from .tasks import run_prestudy_job_task

logger = logging.getLogger(__name__)


def enqueue_prestudy_job(
    *,
    job: PrestudyJob,
    text: Optional[str] = None,
    ppt_bytes: Optional[bytes] = None,
    filename: str = "",
) -> None:
    """Dispatch prestudy pipeline to Celery workers."""

    job.status = "queued"
    job.queued_at = timezone.now()
    job.error_message = ""
    job.save(update_fields=["status", "queued_at", "error_message"])

    async_result = run_prestudy_job_task.delay(
        job_id=job.pk,
        text=text,
        ppt_payload=base64.b64encode(ppt_bytes).decode("ascii") if ppt_bytes else None,
        filename=filename,
    )
    job.task_id = async_result.id or ""
    job.save(update_fields=["task_id"])
