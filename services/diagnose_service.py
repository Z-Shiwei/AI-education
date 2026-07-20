"""规则诊断服务：根据错题标签汇总薄弱知识点。"""
from collections import Counter

from config import HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD
from services.question_service import load_question_bank


def _is_bad_label(value: str) -> bool:
    return not value or "?" in value or "�" in value


def _reason_for(error_rate: float, wrong_count: int) -> str:
    if error_rate >= HIGH_CONFIDENCE_THRESHOLD:
        return f"相关题目错误率较高，共错 {wrong_count} 次，说明这个知识点需要优先补。"
    if error_rate >= MEDIUM_CONFIDENCE_THRESHOLD:
        return f"相关题目出现不稳定错误，共错 {wrong_count} 次，建议及时巩固。"
    return f"这个知识点有轻微失误，共错 {wrong_count} 次，可以通过少量练习修正。"


def _suggestion_for(kp_name: str, tags: list[str]) -> str:
    clean_tags = [tag for tag in tags if not _is_bad_label(tag)]
    prereq_hint = "、".join(clean_tags[:2])
    if prereq_hint:
        return f"先回看“{kp_name}”的基本概念，再结合错题复盘相关前置点：{prereq_hint}。"
    return f"先复习“{kp_name}”的定义、规则和典型例题，再做 2-3 道同类题。"


def diagnose(subject_id: str, unit_id: str, student_answers: list[dict]) -> dict:
    question_bank = load_question_bank(subject_id, unit_id)
    if not question_bank:
        return {
            "error": "题库不存在，请先生成题目。",
            "score": 0,
            "total": 0,
            "correct": 0,
            "wrong": 0,
            "accuracy": 0,
            "weak_points": [],
            "wrong_details": [],
        }

    q_index = {q["id"]: q for q in question_bank}
    correct_count = 0
    wrong_details = []
    kp_wrong_count = Counter()
    kp_total_count = Counter()

    for ans in student_answers:
        q_id = ans.get("q_id", "")
        student_ans = str(ans.get("student_answer", "")).strip().upper()
        question = q_index.get(q_id)
        if not question:
            continue

        correct_ans = str(question.get("correct_answer", "")).strip().upper()
        tags = [tag for tag in question.get("tags", []) if not _is_bad_label(str(tag))]
        for tag in tags:
            kp_total_count[tag] += 1

        if student_ans == correct_ans:
            correct_count += 1
            continue

        wrong_details.append({
            "q_id": q_id,
            "student_answer": student_ans,
            "correct_answer": correct_ans,
            "text": question.get("text", ""),
            "tags": tags,
        })
        for tag in tags:
            kp_wrong_count[tag] += 1

    total = len(student_answers)
    wrong = total - correct_count
    accuracy = correct_count / total if total else 0

    weak_points = []
    for kp_name in set(kp_total_count) | set(kp_wrong_count):
        asked = kp_total_count.get(kp_name, 0)
        wrong_count = kp_wrong_count.get(kp_name, 0)
        if asked == 0 or wrong_count == 0:
            continue
        error_rate = wrong_count / asked
        if error_rate >= HIGH_CONFIDENCE_THRESHOLD:
            confidence = "high"
        elif error_rate >= MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "medium"
        else:
            confidence = "low"

        related_tags = sorted({
            tag
            for detail in wrong_details
            for tag in detail.get("tags", [])
            if tag != kp_name
        })
        weak_points.append({
            "name": kp_name,
            "wrong_count": wrong_count,
            "total_asked": asked,
            "error_rate": round(error_rate, 2),
            "confidence": confidence,
            "wrong_question_ids": [
                d["q_id"] for d in wrong_details if kp_name in d.get("tags", [])
            ],
            "reason": _reason_for(error_rate, wrong_count),
            "suggestion": _suggestion_for(kp_name, related_tags),
        })

    weak_points.sort(key=lambda item: item["error_rate"], reverse=True)

    return {
        "score": correct_count,
        "total": total,
        "correct": correct_count,
        "wrong": wrong,
        "accuracy": round(accuracy, 2),
        "weak_points": weak_points,
        "wrong_details": wrong_details,
    }
