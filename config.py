"""学生端网页配置。"""
import os
from pathlib import Path


PROJECT_ROOT = Path(os.getenv("SMART_EDU_ROOT", Path(__file__).resolve().parent))

# 不要把真实 Key 写进代码。网页输入的 Key 会通过请求头传入，也可以用环境变量。
_BUILTIN_KEY = "sk-02168810f6ca444fa3d964cfc332161e"
API_KEY = os.getenv("DEEPSEEK_API_KEY", _BUILTIN_KEY).strip()
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", str(PROJECT_ROOT / "knowlege"))
QUESTION_DIR = os.getenv("QUESTION_DIR", str(PROJECT_ROOT / "question"))

SUBJECT_CONFIG = {
    "math": {
        "id": "math",
        "name": "数学",
        "publisher": "北京师范大学出版社",
        "grade": 7,
        "units_file": "beishida_grade7_math_units.json",
        "question_dir": os.path.join(QUESTION_DIR, "math"),
        "unit_label": "第{unit_no}单元",
    },
    "english": {
        "id": "english",
        "name": "英语",
        "publisher": "北京师范大学出版社",
        "grade": 7,
        "units_file": "beishida_grade7_english_units.json",
        "question_dir": os.path.join(QUESTION_DIR, "english"),
        "unit_label": "Unit {unit_no}",
    },
    "chinese": {
        "id": "chinese",
        "name": "语文",
        "publisher": "人民教育出版社（统编版）",
        "grade": 7,
        "units_file": "tongbian_grade7_chinese_units.json",
        "question_dir": os.path.join(QUESTION_DIR, "chinese"),
        "unit_label": "第{unit_no}单元",
    },
}

DEFAULT_QUESTIONS_PER_UNIT = 20
MAX_QUESTIONS_PER_QUIZ = 30
QUESTION_GEN_TEMPERATURE = 0.5

HIGH_CONFIDENCE_THRESHOLD = 0.5
MEDIUM_CONFIDENCE_THRESHOLD = 0.3
