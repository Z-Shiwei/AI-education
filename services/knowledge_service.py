"""知识库加载和查询服务。"""
import json
import os
from collections import defaultdict

from config import KNOWLEDGE_BASE_DIR, SUBJECT_CONFIG


_units_cache: dict = {}
_name_to_kps: dict = {}
_unique_names: dict = {}
_merged_kps: dict = {}


def _load_units_file(filename: str) -> dict:
    filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"知识库文件不存在：{filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge_kp_instances(instances: list[dict]) -> dict:
    if not instances:
        return {}

    merged = dict(instances[0])
    all_prereqs = set()
    all_categories = set()
    all_tags = set()
    all_skills = set()

    for kp in instances:
        name = kp.get("name", "")
        for prereq in kp.get("prerequisites", []):
            if prereq and prereq != name:
                all_prereqs.add(prereq)
        if kp.get("category"):
            all_categories.add(kp["category"])
        all_tags.update(kp.get("diagnosis_tags", []))
        all_skills.update(kp.get("skills", []))

    merged["prerequisites"] = sorted(all_prereqs)
    merged["categories"] = sorted(all_categories)
    merged["primary_category"] = instances[0].get("category", "")
    merged["diagnosis_tags"] = sorted(all_tags)
    merged["skills"] = sorted(all_skills)
    merged["instance_count"] = len(instances)
    merged["unit_ids"] = sorted({kp.get("unit_id", "") for kp in instances})
    return merged


def _is_bad_text(value: str) -> bool:
    return not value or "?" in value or "�" in value


def init_knowledge_base():
    _units_cache.clear()
    _name_to_kps.clear()
    _unique_names.clear()
    _merged_kps.clear()

    for subject_id, cfg in SUBJECT_CONFIG.items():
        print(f"[加载] {cfg['grade']}年级{cfg['name']} ({subject_id})")
        data = _load_units_file(cfg["units_file"])
        _units_cache[subject_id] = data

        groups = defaultdict(list)
        for unit in data.get("units", []):
            for kp in unit.get("knowledge_points", []):
                name = kp.get("name", "")
                if not _is_bad_text(name):
                    groups[name].append(kp)

        _name_to_kps[subject_id] = dict(groups)
        _unique_names[subject_id] = sorted(groups.keys())
        _merged_kps[subject_id] = {
            name: _merge_kp_instances(instances)
            for name, instances in groups.items()
        }

        print(f"  OK：{len(data.get('units', []))} 个单元，{len(groups)} 个知识点")


def _format_unit_title(subject_id: str, unit: dict) -> str:
    cfg = SUBJECT_CONFIG[subject_id]
    unit_no = unit.get("unit_no", "")
    label = cfg.get("unit_label", "第{unit_no}单元").format(unit_no=unit_no)
    unit_name = unit.get("unit_name", "")
    unit_name_zh = unit.get("unit_name_zh", "")

    if cfg["name"] == "英语" and unit_name_zh and unit_name_zh != unit_name:
        name = f"{unit_name} {unit_name_zh}"
    else:
        name = unit_name_zh or unit_name

    return f"{cfg['name']} · {cfg['grade']}年级 · {unit.get('volume', '')} · {label}：{name}"


def get_subjects() -> list[dict]:
    subjects = []
    for subject_id, cfg in SUBJECT_CONFIG.items():
        data = _units_cache.get(subject_id, {})
        subjects.append({
            "id": subject_id,
            "grade": cfg["grade"],
            "name": cfg["name"],
            "publisher": cfg["publisher"],
            "total_units": len(data.get("units", [])),
            "total_knowledge_points": len(_unique_names.get(subject_id, [])),
        })
    return sorted(subjects, key=lambda item: (item["grade"], item["name"]))


def get_units(subject_id: str) -> list[dict]:
    data = _units_cache.get(subject_id)
    if not data:
        return []

    units = []
    for unit in data.get("units", []):
        units.append({
            "unit_id": unit.get("unit_id", ""),
            "unit_no": unit.get("unit_no", 0),
            "unit_name": unit.get("unit_name", ""),
            "unit_name_zh": unit.get("unit_name_zh", ""),
            "volume": unit.get("volume", ""),
            "display_title": _format_unit_title(subject_id, unit),
            "knowledge_point_count": unit.get("knowledge_point_count", 0),
        })
    return units


def get_knowledge_points(subject_id: str, unit_id: str | None = None) -> list[dict]:
    if unit_id:
        unit = get_unit_info(subject_id, unit_id)
        return unit.get("knowledge_points", []) if unit else []
    return list(_merged_kps.get(subject_id, {}).values())


def get_unit_info(subject_id: str, unit_id: str) -> dict | None:
    data = _units_cache.get(subject_id)
    if not data:
        return None
    for unit in data.get("units", []):
        if unit.get("unit_id") == unit_id:
            return unit
    return None


def get_kp_by_name(subject_id: str, name: str) -> dict | None:
    return _merged_kps.get(subject_id, {}).get(name)


def build_name_index(subject_id: str) -> dict[str, dict]:
    return _merged_kps.get(subject_id, {})


def get_kp_names(subject_id: str, unit_id: str | None = None) -> list[str]:
    if unit_id:
        seen = set()
        names = []
        for kp in get_knowledge_points(subject_id, unit_id):
            name = kp.get("name", "")
            if not _is_bad_text(name) and name not in seen:
                seen.add(name)
                names.append(name)
        return names
    return _unique_names.get(subject_id, [])
