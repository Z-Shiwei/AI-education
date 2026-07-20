"""补习服务：追溯前置知识，并生成补习内容。"""
import json

from openai import OpenAI

from config import API_KEY, BASE_URL, MODEL, SUBJECT_CONFIG
from services.knowledge_service import build_name_index, get_kp_by_name


def trace_upstream(weak_point_names: list[str], graph: dict[str, dict], max_depth: int = 2, max_roots: int = 5) -> list[str]:
    upstream = []
    seen = set()

    def visit(name: str, depth: int):
        if depth > max_depth or len(upstream) >= max_roots:
            return
        kp = graph.get(name)
        if not kp:
            return
        for prereq in kp.get("prerequisites", []):
            if prereq and prereq not in seen:
                seen.add(prereq)
                upstream.append(prereq)
                visit(prereq, depth + 1)

    for weak in weak_point_names:
        visit(weak, 0)
    return upstream[:max_roots]


def _fallback_pack(kp_name: str, subject_id: str) -> dict:
    kp = get_kp_by_name(subject_id, kp_name) or {}
    desc = kp.get("description") or f"这是本次诊断发现的薄弱知识点：{kp_name}。"
    prereqs = kp.get("prerequisites", [])
    prereq_text = "、".join(prereqs[:3]) if prereqs else "相关基础概念"

    return {
        "point_name": kp_name,
        "micro_lesson": (
            f"先把“{kp_name}”当成一个小目标来补。"
            f"{desc} 如果做题时容易错，通常不是整章都不会，而是规则、条件或前置概念没有对齐。"
            f"建议先复习：{prereq_text}，再回到错题里看自己是哪一步判断错了。"
        ),
        "practice_questions": [
            {
                "question": f"复习“{kp_name}”时，第一步最应该做什么？",
                "options": [
                    "A. 先回顾概念和适用条件",
                    "B. 直接背答案",
                    "C. 跳过错题",
                    "D. 只看分数",
                ],
                "answer": "A",
                "explanation": "补习要先对齐概念和条件，再通过题目巩固。",
            },
            {
                "question": f"如果“{kp_name}”连续出错，最合理的处理方式是？",
                "options": [
                    "A. 找到错因并做同类题",
                    "B. 只换一个单元",
                    "C. 不看解析",
                    "D. 随机猜下一题",
                ],
                "answer": "A",
                "explanation": "诊断的价值在于定位错因，再进行针对性练习。",
            },
        ],
    }


def _ai_pack(kp_name: str, subject_id: str, api_key: str | None = None) -> dict | None:
    key = (api_key or API_KEY or "").strip()
    if not key:
        return None

    cfg = SUBJECT_CONFIG.get(subject_id, {})
    kp = get_kp_by_name(subject_id, kp_name) or {}
    prompt = f"""你是一位耐心的七年级{cfg.get('name', '')}老师。学生在这个知识点上出错：{kp_name}

知识点说明：{kp.get('description', '')}
前置知识：{kp.get('prerequisites', [])}

请输出 JSON：
{{
  "point_name": "{kp_name}",
  "micro_lesson": "3-5句话，像老师面对面讲解一样，通俗清楚。",
  "practice_questions": [
    {{
      "question": "练习题",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "一句话解析"
    }}
  ]
}}
"""
    try:
        client = OpenAI(api_key=key, base_url=BASE_URL)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return None


def remediate(subject_id: str, weak_point_names: list[str], api_key: str | None = None) -> dict:
    if subject_id not in SUBJECT_CONFIG:
        return {"error": f"未知学科：{subject_id}", "remediations": []}

    graph = build_name_index(subject_id)
    if not graph:
        return {"error": "知识图谱未加载", "remediations": []}

    upstream_roots = trace_upstream(weak_point_names, graph)
    points_to_fix = []
    for name in weak_point_names + upstream_roots:
        if name not in points_to_fix:
            points_to_fix.append(name)
        if len(points_to_fix) >= 5:
            break

    remediations = []
    for kp_name in points_to_fix:
        pack = _ai_pack(kp_name, subject_id, api_key=api_key) or _fallback_pack(kp_name, subject_id)
        remediations.append({
            "kp_name": pack.get("point_name", kp_name),
            "micro_lesson": pack.get("micro_lesson", ""),
            "practice_questions": pack.get("practice_questions", []),
            "upstream_roots": upstream_roots,
        })

    if upstream_roots:
        summary = f"系统追溯到 {len(upstream_roots)} 个可能影响本次表现的前置知识点：{'、'.join(upstream_roots)}。"
    else:
        summary = "这些薄弱点暂未发现更深层前置依赖，建议先做直接补习和同类练习。"

    return {
        "remediations": remediations,
        "upstream_summary": summary,
        "upstream_roots": upstream_roots,
        "fixed_points": points_to_fix,
    }
