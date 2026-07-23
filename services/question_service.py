"""题库服务：缓存优先，必要时调用 DeepSeek 生成。"""
import json
import os
import re

from openai import OpenAI

from config import (
    API_KEY,
    BASE_URL,
    DEFAULT_QUESTIONS_PER_UNIT,
    MODEL,
    QUESTION_GEN_TEMPERATURE,
    SUBJECT_CONFIG,
)
from services.knowledge_service import get_kp_names, get_knowledge_points, get_unit_info


DIFFICULTY_LABELS = {
    "mixed": "综合难度",
    "basic": "基础",
    "core": "核心",
    "advanced": "提高",
}


def _get_client(api_key: str | None = None) -> OpenAI | None:
    key = (api_key or API_KEY or "").strip()
    if not key:
        return None
    return OpenAI(api_key=key, base_url=BASE_URL)


def _safe_difficulty(difficulty: str | None) -> str:
    value = (difficulty or "mixed").strip().lower()
    return value if value in DIFFICULTY_LABELS else "mixed"


def _get_cache_path(subject_id: str, unit_id: str, difficulty: str = "mixed") -> str:
    subject_dir = SUBJECT_CONFIG[subject_id]["question_dir"]
    os.makedirs(subject_dir, exist_ok=True)
    safe_unit = re.sub(r"[^A-Za-z0-9_-]+", "_", unit_id)
    safe_diff = _safe_difficulty(difficulty)
    return os.path.join(subject_dir, f"{safe_unit}_{safe_diff}.json")


def _is_bad_label(value: str) -> bool:
    return not value or "?" in value or "�" in value


def _load_from_cache(subject_id: str, unit_id: str, difficulty: str = "mixed") -> list[dict] | None:
    path = _get_cache_path(subject_id, unit_id, difficulty)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    cleaned = []
    for q in questions:
        item = dict(q)
        item["tags"] = [tag for tag in item.get("tags", []) if not _is_bad_label(str(tag))]
        cleaned.append(item)
    return cleaned or None


def _save_to_cache(subject_id: str, unit_id: str, difficulty: str, questions: list[dict], kp_names: list[str]):
    path = _get_cache_path(subject_id, unit_id, difficulty)
    data = {
        "subject_id": subject_id,
        "unit_id": unit_id,
        "difficulty": _safe_difficulty(difficulty),
        "knowledge_points": kp_names,
        "question_count": len(questions),
        "questions": questions,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_questions(questions: list[dict], kp_names: list[str]) -> list[dict]:
    valid = []
    allowed = set(kp_names)
    seen_text = set()

    for idx, raw in enumerate(questions, 1):
        text = str(raw.get("text", "")).strip()
        options = raw.get("options", [])
        answer = str(raw.get("correct_answer", "")).strip().upper()
        tags = [str(tag).strip() for tag in raw.get("tags", [])]

        if not text or not isinstance(options, list) or len(options) < 2:
            continue
        if answer not in {"A", "B", "C", "D"}:
            continue
        if not tags or any(tag not in allowed for tag in tags):
            continue
        if text.lower() in seen_text:
            continue

        seen_text.add(text.lower())
        valid.append({
            "id": str(raw.get("id") or f"q{idx}"),
            "text": text,
            "options": [str(opt).strip() for opt in options[:4]],
            "correct_answer": answer,
            "tags": tags,
        })

    return valid


def _subject_style(subject_name: str) -> str:
    return {
        "数学": "数学选择题，重点考查概念理解、计算规则、图形推理和应用建模。",
        "英语": "英语选择题，重点考查词汇、语法、功能句、阅读理解和写作表达。选项自然，难度贴合年级。",
        "语文": "语文选择题，重点考查字词积累、阅读理解、文学常识、古诗文基础和写作知识。",
        "物理": "物理选择题，重点考查概念规律、实验探究、公式应用和生活现象解释。",
        "化学": "化学选择题，重点考查概念原理、实验现象、物质性质、化学方程式和基础计算。",
    }.get(subject_name, "选择题，难度贴合当前年级学生。")


def _difficulty_instruction(difficulty: str) -> str:
    difficulty = _safe_difficulty(difficulty)
    return {
        "mixed": "难度覆盖基础、核心和提高，比例约为 4:4:2。",
        "basic": "只出基础题，重点考查概念识别、基本规则和直接应用，避免复杂综合。",
        "core": "以核心题为主，重点考查本单元最常见的考试点和标准解题方法。",
        "advanced": "以提高题为主，允许适度综合、情境迁移和易错点辨析，但仍适合当前年级。",
    }[difficulty]


def _build_generation_prompt(
    subject_id: str,
    kp_names: list[str],
    target_count: int,
    difficulty: str = "mixed",
) -> str:
    cfg = SUBJECT_CONFIG[subject_id]
    subject_name = cfg["name"]
    grade = cfg["grade"]

    unit_kps = [
        {
            "name": kp.get("name", ""),
            "description": kp.get("description", ""),
            "category": kp.get("category", kp.get("primary_category", "")),
        }
        for kp in get_knowledge_points(subject_id)
        if kp.get("name") in kp_names
    ]

    return f"""你是一位初中{grade}年级{subject_name}老师。请为学生生成 {target_count} 道单元诊断选择题。
出题风格：{_subject_style(subject_name)}
难度要求：{_difficulty_instruction(difficulty)}

合法知识点标签如下，题目 tags 字段只能从这里逐字复制，不能改写：
{json.dumps(kp_names, ensure_ascii=False, indent=2)}

知识点说明：
{json.dumps(unit_kps, ensure_ascii=False, indent=2)}

要求：
1. 每题 4 个选项，选项文本以 "A. "、"B. "、"C. "、"D. " 开头。
2. correct_answer 只能是 A/B/C/D。
3. tags 至少包含 1 个合法知识点名称。
4. 输出纯 JSON，不要 Markdown，不要解释。

格式：
{{
  "questions": [
    {{
      "id": "q1",
      "text": "题干",
      "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
      "correct_answer": "A",
      "tags": ["知识点名称"]
    }}
  ]
}}"""


def _generate_via_deepseek(
    subject_id: str,
    kp_names: list[str],
    target_count: int,
    difficulty: str = "mixed",
    api_key: str | None = None,
) -> tuple[list[dict], str | None]:
    client = _get_client(api_key)
    if client is None:
        return [], "未设置 DeepSeek API Key，无法生成新题；如果已有缓存题库，系统会优先使用缓存。"

    prompt = _build_generation_prompt(subject_id, kp_names, target_count, difficulty=difficulty)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=QUESTION_GEN_TEMPERATURE,
        )
        raw = json.loads(response.choices[0].message.content)
        questions = validate_questions(raw.get("questions", []), kp_names)
        return questions, None
    except Exception as exc:
        return [], f"AI 生成失败：{exc}"


def get_or_generate_questions(
    subject_id: str,
    unit_id: str,
    count: int = DEFAULT_QUESTIONS_PER_UNIT,
    difficulty: str = "mixed",
    regenerate: bool = False,
    api_key: str | None = None,
) -> dict:
    difficulty = _safe_difficulty(difficulty)
    if subject_id not in SUBJECT_CONFIG:
        return {"error": f"未知学科：{subject_id}", "questions": [], "total": 0}

    unit_info = get_unit_info(subject_id, unit_id)
    if not unit_info:
        return {"error": f"未知单元：{unit_id}", "questions": [], "total": 0}

    kp_names = get_kp_names(subject_id, unit_id)
    if not kp_names:
        return {"error": "该单元没有知识点", "questions": [], "total": 0}

    if not regenerate:
        cached = _load_from_cache(subject_id, unit_id, difficulty)
        if cached:
            selected = cached[:count]
            return {
                "unit_id": unit_id,
                "subject_id": subject_id,
                "difficulty": difficulty,
                "questions": selected,
                "total": len(selected),
                "from_cache": True,
                "message": "已使用缓存题库",
            }

    target = min(count, 30)
    questions, error = _generate_via_deepseek(
        subject_id,
        kp_names,
        target,
        difficulty=difficulty,
        api_key=api_key,
    )
    if not questions:
        return {
            "unit_id": unit_id,
            "subject_id": subject_id,
            "difficulty": difficulty,
            "questions": [],
            "total": 0,
            "from_cache": False,
            "error": error or "题目生成失败，请稍后重试",
        }

    _save_to_cache(subject_id, unit_id, difficulty, questions, kp_names)
    selected = questions[:count]
    return {
        "unit_id": unit_id,
        "subject_id": subject_id,
        "difficulty": difficulty,
        "questions": selected,
        "total": len(selected),
        "from_cache": False,
        "message": "已生成新的诊断题",
    }


def load_question_bank(subject_id: str, unit_id: str, difficulty: str = "mixed") -> list[dict]:
    return _load_from_cache(subject_id, unit_id, difficulty=difficulty) or []
