"""学生端网页配置。"""
import os
from pathlib import Path


# 部署时使用项目内相对路径，本地和云服务器都能读取。
PROJECT_ROOT = Path(os.getenv("SMART_EDU_ROOT", Path(__file__).resolve().parent))

# 部署 Demo 按你的要求保留内置 Key；服务器环境变量仍然可以覆盖它。
_BUILTIN_KEY = "sk-02168810f6ca444fa3d964cfc332161e"
API_KEY = os.getenv("DEEPSEEK_API_KEY", _BUILTIN_KEY).strip()
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", str(PROJECT_ROOT / "knowlege"))
QUESTION_DIR = os.getenv("QUESTION_DIR", str(PROJECT_ROOT / "question"))


def _subject(
    subject_id: str,
    grade: int,
    name: str,
    publisher: str,
    units_file: str,
    question_folder: str,
    unit_label: str,
) -> dict:
    return {
        "id": subject_id,
        "grade": grade,
        "name": name,
        "publisher": publisher,
        "units_file": units_file,
        "question_dir": os.path.join(QUESTION_DIR, question_folder),
        "unit_label": unit_label,
    }


SUBJECT_CONFIG = {
    "grade7_math": _subject(
        "grade7_math", 7, "数学", "北京师范大学出版社",
        "beishida_grade7_math_units.json", "grade7_math", "第{unit_no}单元",
    ),
    "grade7_english": _subject(
        "grade7_english", 7, "英语", "北京师范大学出版社",
        "beishida_grade7_english_units.json", "grade7_english", "Unit {unit_no}",
    ),
    "grade7_chinese": _subject(
        "grade7_chinese", 7, "语文", "人民教育出版社（统编版）",
        "tongbian_grade7_chinese_units.json", "grade7_chinese", "第{unit_no}单元",
    ),
    "grade8_math": _subject(
        "grade8_math", 8, "数学", "北京师范大学出版社",
        "beishida_grade8_math_units.json", "grade8_math", "第{unit_no}单元",
    ),
    "grade8_english": _subject(
        "grade8_english", 8, "英语", "北京师范大学出版社",
        "beishida_grade8_english_units.json", "grade8_english", "Unit {unit_no}",
    ),
    "grade8_chinese": _subject(
        "grade8_chinese", 8, "语文", "人民教育出版社（统编版）",
        "tongbian_grade8_chinese_units.json", "grade8_chinese", "第{unit_no}单元",
    ),
    "grade8_physics": _subject(
        "grade8_physics", 8, "物理", "人民教育出版社",
        "renjiao_grade8_physics_units.json", "grade8_physics", "第{unit_no}章",
    ),
    "grade9_math": _subject(
        "grade9_math", 9, "数学", "北京师范大学出版社",
        "beishida_grade9_math_units.json", "grade9_math", "第{unit_no}单元",
    ),
    "grade9_english": _subject(
        "grade9_english", 9, "英语", "北京师范大学出版社",
        "beishida_grade9_english_units.json", "grade9_english", "Unit {unit_no}",
    ),
    "grade9_chinese": _subject(
        "grade9_chinese", 9, "语文", "人民教育出版社（统编版）",
        "tongbian_grade9_chinese_units.json", "grade9_chinese", "第{unit_no}单元",
    ),
    "grade9_physics": _subject(
        "grade9_physics", 9, "物理", "人民教育出版社",
        "renjiao_grade9_physics_units.json", "grade9_physics", "第{unit_no}章",
    ),
    "grade9_chemistry": _subject(
        "grade9_chemistry", 9, "化学", "人民教育出版社",
        "renjiao_grade9_chemistry_units.json", "grade9_chemistry", "第{unit_no}单元",
    ),
}

DEFAULT_QUESTIONS_PER_UNIT = 20
MAX_QUESTIONS_PER_QUIZ = 30
QUESTION_GEN_TEMPERATURE = 0.5

HIGH_CONFIDENCE_THRESHOLD = 0.5
MEDIUM_CONFIDENCE_THRESHOLD = 0.3
