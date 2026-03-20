from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model

from src.core.models import KnowledgeBase, PrestudyJob
from src.services.jobs import enqueue_prestudy_job


@pytest.mark.django_db
def test_enqueue_prestudy_job_schedules_celery_task(monkeypatch):
    user = get_user_model().objects.create_user(username="alice", password="pw123456")
    base = KnowledgeBase.objects.create(user=user, name="默认知识库")
    job = PrestudyJob.objects.create(user=user, knowledge_base=base, source_type="text")

    captured = {}

    def fake_delay(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="task-123")

    monkeypatch.setattr("src.services.jobs.run_prestudy_job_task.delay", fake_delay)

    enqueue_prestudy_job(job=job, text="hello world")
    job.refresh_from_db()

    assert job.status == "queued"
    assert job.task_id == "task-123"
    assert captured["job_id"] == job.pk
    assert captured["text"] == "hello world"
    assert captured["ppt_payload"] is None
