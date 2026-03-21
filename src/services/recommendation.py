
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


def _issue_driven_suggestions(*, final_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    evaluation = final_json.get('evaluation') or {}
    reflection = final_json.get('reflection') or {}
    review_summary = final_json.get('review_summary') or {}
    primary_issue = str(evaluation.get('primary_issue') or '').strip()
    issue_tags = [str(item) for item in (evaluation.get('issue_tags') or []) if str(item).strip()]
    missing_evidence = [str(item) for item in (evaluation.get('missing_evidence') or []) if str(item).strip()]

    suggestions: List[Dict[str, Any]] = []

    if primary_issue in {'retrieval_gap', 'evidence_gap'}:
        suggestions.append(
            {
                'id': _build_action_id('issue', primary_issue),
                'agent': 'planner',
                'stage': 'planning',
                'type': 'stabilize',
                'target': 'review',
                'title': '先补证据再继续',
                'summary': missing_evidence[0] if missing_evidence else '当前证据覆盖不足，先补资料或先复核引用，再进入下一步会更稳。',
                'action': '优先回到知识库补资料，或重新生成一轮带更多证据的课程内容',
                'reason': '系统评测发现当前结果的证据链不够稳，直接继续学习容易把不确定内容讲错。',
                'confidence': 0.91,
                'issue_tags': issue_tags,
            }
        )

    if primary_issue in {'tutoring_gap', 'learner_fit_gap'}:
        suggestions.append(
            {
                'id': _build_action_id('issue', primary_issue or 'practice'),
                'agent': 'tutor',
                'stage': 'practice',
                'type': 'stabilize',
                'target': 'quiz',
                'title': '先做一轮引导练习',
                'summary': '当前更需要把知识点讲透并接一轮低压力练习，再继续推进。',
                'action': '先进入陪学助教或发起一次短测，确认哪里还没跟上',
                'reason': '评测显示主要风险在练习承接和学习体验，而不是知识点本身。',
                'confidence': 0.86,
                'issue_tags': issue_tags,
            }
        )

    if primary_issue == 'quiz_gap':
        suggestions.append(
            {
                'id': _build_action_id('issue', 'quiz-gap'),
                'agent': 'rewriter',
                'stage': 'practice',
                'type': 'stabilize',
                'target': 'quiz',
                'title': '先用测验校准掌握度',
                'summary': '当前测验覆盖还不够，先用小测把薄弱点找出来，再决定是否重讲。',
                'action': '发起一次课堂测验，优先看错题对应的知识点',
                'reason': '系统认为当前最值得先修的是测验质量和诊断能力。',
                'confidence': 0.84,
                'issue_tags': issue_tags,
            }
        )

    if review_summary.get('pending_multimodal_review') or reflection.get('should_add_multimodal_review'):
        suggestions.append(
            {
                'id': _build_action_id('issue', 'multimodal-review'),
                'agent': 'planner',
                'stage': 'resource',
                'type': 'resource',
                'target': 'resource',
                'title': '考虑补充图示或板书材料',
                'summary': '当前系统认为文字证据还不够直观，图示、实验图或板书结构会明显提升理解。',
                'action': '补一张关键图示、实验示意图或公式结构图，再继续讲解',
                'reason': '这一步主要提升理解丝滑度，不是为了堆资料。',
                'confidence': 0.72,
                'issue_tags': issue_tags,
            }
        )

    return suggestions


def generate_recommendations(*, job, session: Optional[Any] = None) -> Dict[str, Any]:
    """Build personalized multi-agent playbook suggestions."""
    plan: LessonPlan | None = getattr(job, 'lesson_plan', None)
    final_json: Dict[str, Any] = job.final_json or {}

    focus_points = final_json.get('knowledge_points') or []
    quiz_items = (final_json.get('quiz') or {}).get('items', [])

    suggestions: List[Dict[str, Any]] = _issue_driven_suggestions(final_json=final_json)
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
                'reason': '这是课程主线知识点，适合按顺序推进。',
                'confidence': 0.68,
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
                'reason': '这一步用于快速确认掌握度，避免后续建议失焦。',
                'confidence': 0.74,
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
                'reason': '把学习动作排进时间线后，后续追踪和复习会更顺。',
                'confidence': 0.62,
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
