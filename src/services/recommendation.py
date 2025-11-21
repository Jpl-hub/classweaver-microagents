
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from django.utils import timezone

from src.core.models import LessonPlan, RecommendationTask

logger = logging.getLogger(__name__)


def _build_action_id(prefix: str, value: Any) -> str:
    suffix = str(value).strip().replace(' ', '').lower()
    if not suffix:
        suffix = uuid4().hex[:6]
    return f"{prefix}-{suffix}"


def generate_recommendations(*, job, session: Optional[Any] = None) -> Dict[str, Any]:
    """Build personalized multi-agent playbook suggestions."""
    plan: LessonPlan | None = getattr(job, 'lesson_plan', None)
    final_json: Dict[str, Any] = job.final_json or {}
    knowledge_ids: List[str] = job.knowledge_doc_ids or []

    focus_points = final_json.get('knowledge_points') or []
    quiz_items = (final_json.get('quiz') or {}).get('items', [])

    suggestions: List[Dict[str, Any]] = []
    for idx, kp in enumerate(focus_points[:5]):
        kp_id = kp.get('id') or f"{idx + 1}"
        suggestions.append(
            {
                'id': _build_action_id('focus', kp_id or idx),
                'agent': 'planner',
                'stage': 'focus',
                'type': 'review',
                'target': 'review',
                'title': kp.get('title') or f"知识点 {idx + 1}",
                'summary': kp.get('summary', ''),
                'action': '复盘该知识点，稍后参与课堂问答',
                'kp_ids': [kp_id] if kp_id else [],
            }
        )

    for item in quiz_items[:3]:
        question_id = item.get('id') or uuid4().hex[:4]
        suggestions.append(
            {
                'id': _build_action_id('quiz', question_id),
                'agent': 'rewriter',
                'stage': 'practice',
                'type': 'practice',
                'target': 'quiz',
                'title': item.get('question', '巩固练习'),
                'summary': '跟随 Tutor 完成一次快速测验，确认掌握情况。',
                'action': '前往小测页面，完成系统推荐的题目',
                'kp_ids': item.get('kp_ids') or [],
            }
        )

    if plan:
        suggestions.append(
            {
                'id': _build_action_id('timeline', plan.pk),
                'agent': 'tutor',
                'stage': 'classroom',
                'type': 'classroom',
                'target': 'timeline',
                'title': '写入课堂节奏',
                'summary': '把 Planner 的知识节点与互动动作同步到时间线，方便课堂跟进。',
                'action': '在课堂节奏面板登记一条互动节点',
                'doc_ids': knowledge_ids,
            }
        )

    return {
        'generated_at': timezone.now().isoformat(),
        'job_id': job.pk,
        'session_id': getattr(session, 'session_id', None),
        'suggestions': suggestions,
    }


def run_recommendation_task(*, job, session: Optional[Any] = None) -> RecommendationTask:
    task = RecommendationTask.objects.create(
        job=job,
        session=session,
        status='running',
        input_snapshot={'job_id': job.pk, 'session_id': getattr(session, 'session_id', None)},
    )
    try:
        output = generate_recommendations(job=job, session=session)
        task.output = output
        task.status = 'completed'
        task.save(update_fields=['output', 'status', 'updated_at'])
    except Exception as exc:  # noqa: BLE001
        logger.exception('Failed to generate recommendations for job %s', job.pk)
        task.status = 'failed'
        task.error_message = str(exc)
        task.save(update_fields=['status', 'error_message', 'updated_at'])
    return task
