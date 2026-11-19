import json
from pathlib import Path
from time import perf_counter

from app.llm.agent import ask_project_agent


PROJECT_NAME = "Demo Boston Office Tower"


def evaluate_case(case: dict) -> dict:
    start = perf_counter()
    result = ask_project_agent(case["question"], case.get("project_name", PROJECT_NAME))
    latency = perf_counter() - start

    answer = result["answer"]
    answer_lower = answer.lower()

    source_files = {source["file_name"] for source in result.get("sources", [])}
    source_tables = {
        table
        for source in result.get("data_sources", [])
        for table in source.get("tables", [])
    }

    missing_terms = [term for term in case.get("must_contain", []) if term.lower() not in answer_lower]
    missing_files = [name for name in case.get("required_files", []) if name not in source_files]
    missing_tables = [name for name in case.get("required_tables", []) if name not in source_tables]

    passed = not (missing_terms or missing_files or missing_tables)

    return {
        "id": case["id"],
        "question": case["question"],
        "passed": passed,
        "missing_terms": missing_terms,
        "missing_files": missing_files,
        "missing_tables": missing_tables,
        "latency_seconds": round(latency, 3),
        "answer": answer,
        "sources": result.get("sources", []),
        "data_sources": result.get("data_sources", []),
    }


def main():
    cases = json.loads(Path("eval/answer_cases.json").read_text(encoding="utf-8"))
    results = []

    for case in cases:
        result = evaluate_case(case)
        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(f"{result['id']}: {status}, latency={result['latency_seconds']:.3f}s")

        if not result["passed"]:
            print(f"  Missing terms: {result['missing_terms']}")
            print(f"  Missing files: {result['missing_files']}")
            print(f"  Missing tables: {result['missing_tables']}")

    passed_count = sum(item["passed"] for item in results)
    pass_rate = passed_count / len(results)
    avg_latency = sum(item["latency_seconds"] for item in results) / len(results)

    report = {
        "total_cases": len(results),
        "passed_cases": passed_count,
        "basic_check_pass_rate": pass_rate,
        "avg_latency_seconds": round(avg_latency, 3),
        "results": results,
    }

    output = Path("eval/results/answer_baseline.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nBasic Check Pass Rate: {pass_rate:.1%}")
    print(f"Average Latency: {avg_latency:.3f}s")
    print(f"Saved to: {output}")


if __name__ == "__main__":
    main()