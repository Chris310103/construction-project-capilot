import argparse
import json
from pathlib import Path
from time import perf_counter

from scripts.evaluate_answers import evaluate_case


CASE_FILE = Path("eval/answer_cases.json")
RESULT_FILE = Path("eval/results/answer_runs.jsonl")

CATEGORIES = [
    "factual_retrieval",
    "multi_document_reasoning",
    "sql_aggregation",
    "schedule_cost_analysis",
]


def load_previous_results() -> dict:
    results = {}

    if not RESULT_FILE.exists():
        return results

    with RESULT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                item = json.loads(line)
                results[item["id"]] = item

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=CATEGORIES, required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()

    if args.limit < 1:
        raise ValueError("--limit must be positive")

    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    selected = [case for case in cases if case["category"] == args.category]
    previous = load_previous_results()

    pending = [
        case for case in selected
        if case["id"] not in previous or (args.retry_failed and not previous[case["id"]]["passed"])
    ]

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Category: {args.category}")
    print(f"Total cases: {len(selected)}")
    print(f"Pending cases: {len(pending)}")

    for case in pending[:args.limit]:
        start = perf_counter()

        try:
            result = evaluate_case(case)
            result["status"] = "pass" if result["passed"] else "fail"

        except Exception as exc:
            result = {
                "id": case["id"],
                "question": case["question"],
                "passed": False,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "latency_seconds": round(perf_counter() - start, 3),
            }

        result["category"] = args.category

        with RESULT_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

        previous[case["id"]] = result

        print(f"{case['id']}: {result['status'].upper()}")

        if not result["passed"]:
            print("  Details:", result.get("error", result.get("missing_terms", [])))
            print("  Missing files:", result.get("missing_files", []))
            print("  Missing tables:", result.get("missing_tables", []))

    completed = [previous[case["id"]] for case in selected if case["id"] in previous]
    passed = sum(item["passed"] for item in completed)
    failed = len(completed) - passed

    print(f"\nProgress: {len(completed)}/{len(selected)}")
    print(f"Passed: {passed}")
    print(f"Failed or errored: {failed}")
    print(f"Results saved: {RESULT_FILE}")


if __name__ == "__main__":
    main()