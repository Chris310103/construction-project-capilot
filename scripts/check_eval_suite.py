
import json
from collections import Counter
from pathlib import Path


CATEGORIES = [
    "factual_retrieval",
    "multi_document_reasoning",
    "sql_aggregation",
    "schedule_cost_analysis",
]

TARGET_PER_CATEGORY = 30


def main():
    cases = json.loads(Path("eval/answer_cases.json").read_text(encoding="utf-8"))
    counts = Counter()
    seen_ids = set()
    seen_questions = set()

    for case in cases:
        case_id = case["id"]
        category = case["category"]
        question = case["question"].strip().lower()

        if category not in CATEGORIES:
            raise ValueError(f"Unknown category: {category}")

        if case_id in seen_ids or question in seen_questions:
            raise ValueError(f"Duplicate evaluation case: {case_id}")

        if not any(case.get(key) for key in ("must_contain", "required_files", "required_tables")):
            raise ValueError(f"Missing expected evidence: {case_id}")

        seen_ids.add(case_id)
        seen_questions.add(question)
        counts[category] += 1

    print(f"Total evaluation cases: {len(cases)}/120")

    for category in CATEGORIES:
        print(f"{category}: {counts[category]}/{TARGET_PER_CATEGORY}")

    print("Dataset validation passed.")


if __name__ == "__main__":
    main()