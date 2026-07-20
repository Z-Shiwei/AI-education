"""
批量生成题库 - 为所有学科的所有单元生成题目
可中断续传：已缓存的单元会自动跳过
"""
import sys
import time
sys.path.insert(0, "D:/桌面/智能教育/student_web_demo")

from services.knowledge_service import init_knowledge_base, get_units, get_kp_names
from services.question_service import get_or_generate_questions


def main():
    print("=" * 60)
    print("  批量题库生成器")
    print("=" * 60)

    init_knowledge_base()

    subjects = ["english", "math", "chinese"]
    total_generated = 0
    total_skipped = 0
    total_errors = 0

    for subject_id in subjects:
        units = get_units(subject_id)
        print(f"\n{'='*60}")
        print(f"  学科: {subject_id} ({len(units)} 个单元)")
        print(f"{'='*60}")

        for i, unit in enumerate(units):
            unit_id = unit["unit_id"]
            unit_name = unit.get("unit_name_zh", unit.get("unit_name", unit_id))
            kp_names = get_kp_names(subject_id, unit_id)

            print(f"\n[{i+1}/{len(units)}] {unit_id}: {unit_name}")
            print(f"  知识点数: {len(kp_names)}")

            try:
                result = get_or_generate_questions(
                    subject_id, unit_id, count=20, regenerate=False
                )
                if result.get("from_cache"):
                    total_skipped += 1
                    print(f"  [跳过] 已有缓存 ({result['total']} 题)")
                else:
                    total_generated += 1
                    print(f"  [生成] {result['total']} 题")

                # API 调用间短暂休息，避免触发频率限制
                if not result.get("from_cache"):
                    time.sleep(1)

            except Exception as e:
                total_errors += 1
                print(f"  [错误] {e}")

    print(f"\n{'='*60}")
    print(f"  批量生成完成！")
    print(f"  新生成: {total_generated} 个单元")
    print(f"  跳过(缓存): {total_skipped} 个单元")
    print(f"  失败: {total_errors} 个单元")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
