from collections import defaultdict
from typing import Any, Dict, List, Tuple


def _sanitize_answer(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().upper()


def _compute_review(kp_stats: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    strengths = []
    focus = []
    for kp, stat in kp_stats.items():
        total = stat["total"]
        correct = stat["correct"]
        if total == 0:
            continue
        accuracy = correct / total
        if accuracy >= 0.8:
            strengths.append(kp)
        elif accuracy <= 0.5:
            focus.append(kp)
    overall = "Solid understanding overall." if not focus else "Needs targeted review."
    return {"strengths": strengths, "focus": focus, "summary": overall}


def score_quiz(*, questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate quiz answers and produce diagnostics."""
    question_map: Dict[str, Dict[str, Any]] = {str(question.get("id")): question for question in questions if question.get("id")}
    provided_answers: Dict[str, str] = {str(item["id"]): _sanitize_answer(item.get("answer")) for item in answers}

    total_questions = len(question_map)
    if total_questions == 0:
        return {
            "score": 0,
            "detail": [],
            "detail_map": {},
            "diagnostics": {"kp_stats": {}},
            "review_card": {"strengths": [], "focus": [], "summary": "No questions available."},
            "extra_questions": [],
        }

    correct_count = 0
    detail: List[Dict[str, Any]] = []
    kp_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    detail_map: Dict[str, Dict[str, Any]] = {}

    for qid, question in question_map.items():
        expected_answer = _sanitize_answer(question.get("answer"))
        user_answer = provided_answers.get(qid, "")
        is_correct = bool(expected_answer) and user_answer == expected_answer
        if is_correct:
            correct_count += 1

        explain = question.get("explain") or question.get("explanation", "")
        detail_entry = {
            "id": qid,
            "correct": is_correct,
            "answer": expected_answer,
            "user_answer": user_answer,
            "explain": explain,
            "difficulty": question.get("difficulty", "medium"),
        }
        detail.append(detail_entry)
        detail_map[qid] = detail_entry

        kp_ids = question.get("kp_ids") or question.get("knowledge_points") or []
        for kp in kp_ids:
            stats = kp_stats[str(kp)]
            stats["total"] += 1
            if is_correct:
                stats["correct"] += 1

    score_percent = round((correct_count / total_questions) * 100)
    kp_stats_serializable = {kp: dict(stat) for kp, stat in kp_stats.items()}
    review_card = _compute_review(kp_stats_serializable)

    diagnostics = {"kp_stats": kp_stats_serializable, "raw": {"total": total_questions, "correct": correct_count}}

    return {
        "score": score_percent,
        "detail": detail,
        "detail_map": detail_map,
        "diagnostics": diagnostics,
        "review_card": review_card,
        "extra_questions": [],
    }
