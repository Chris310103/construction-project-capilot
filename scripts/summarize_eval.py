import json
from collections import defaultdict
from math import ceil
from pathlib import Path
from statistics import mean, median


CASE_FILE = Path("eval/answer_cases.json")
RUN_FILE = Path("eval/results/answer_runs.jsonl")
OUTPUT_FILE = Path("eval/results/evaluation_summary.json")


def summarize():
    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    results = {}

    for line in RUN_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            results[item["id"]] = item

    categories = defaultdict(list)

    for case in cases:
        categories[case["category"]].append(results.get(case["id"]))

    report = {"categories": {}, "total_cases": len(cases)}
    all_results = []

    for category, items in categories.items():
        completed = [item for item in items if item is not None]
        all_results.extend(completed)

        passed = sum(bool(item.get("passed")) for item in completed)
        latencies = sorted(float(item["latency_seconds"]) for item in completed if isinstance(item.get("latency_seconds"), (int, float)))

        stats = {
            "total": len(items),
            "evaluated": len(completed),
            "passed": passed,
            "failed": len(completed) - passed,
            "pass_rate": round(passed / len(completed), 4) if completed else None,
            "avg_latency": round(mean(latencies), 3) if latencies else None,
            "median_latency": round(median(latencies), 3) if latencies else None,
            "p95_latency": round(latencies[ceil(0.95 * len(latencies)) - 1], 3) if latencies else None,
            "failed_ids": [item["id"] for item in completed if not item.get("passed")],
        }

        report["categories"][category] = stats

    total_passed = sum(bool(item.get("passed")) for item in all_results)
    total_evaluated = len(all_results)
    all_latencies = [float(item["latency_seconds"]) for item in all_results if isinstance(item.get("latency_seconds"), (int, float))]

    report["overall"] = {
        "evaluated": total_evaluated,
        "passed": total_passed,
        "failed": total_evaluated - total_passed,
        "basic_check_pass_rate": round(total_passed / total_evaluated, 4) if total_evaluated else None,
        "avg_latency": round(mean(all_latencies), 3) if all_latencies else None,
    }

    report["evaluation_note"] = "Keyword and source-presence checks on synthetic data; post-fix regression, not independent answer accuracy."

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n===== Evaluation Summary =====")

    for category, stats in report["categories"].items():
        print(f"{category}: {stats['passed']}/{stats['evaluated']} passed")
        print(f"  Avg Latency: {stats['avg_latency']}s")
        print(f"  P95 Latency: {stats['p95_latency']}s")
        print(f"  Failed Cases: {stats['failed_ids']}")

    print(f"\nTotal: {total_passed}/{total_evaluated}")
    print(f"Basic Check Pass Rate: {report['overall']['basic_check_pass_rate']}")
    print(f"Average Latency: {report['overall']['avg_latency']}s")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    summarize()