import json
from pathlib import Path
from time import perf_counter

from app.retrieval.hybrid_search import search_hybrid_chunks
from app.retrieval.reranker import rerank_chunks
from eval.metrics import calculate_metrics, find_relevant_rank


PROJECT_NAME = "Demo Boston Office Tower"


def main():
    cases = json.loads(Path("eval/retrieval_cases.json").read_text(encoding="utf-8"))

    methods = {
        "hybrid": search_hybrid_chunks,
        "reranked": rerank_chunks,
    }

    report = {}

    for method_name, search_fn in methods.items():
        ranks = []
        latencies = []

        print(f"\n===== Evaluating {method_name} =====")

        for case in cases:
            start = perf_counter()
            results = search_fn(case["question"], PROJECT_NAME, top_k=3)
            elapsed = perf_counter() - start

            rank = find_relevant_rank(results, case["expected"])
            ranks.append(rank)
            latencies.append(elapsed)

            print(f"{case['id']}: rank={rank}, latency={elapsed:.3f}s")

        metrics = calculate_metrics(ranks, k=3)
        metrics["avg_latency_seconds"] = sum(latencies) / len(latencies)
        report[method_name] = metrics

        print(f"Hit@3: {metrics['hit_at_3']:.3f}")
        print(f"MRR@3: {metrics['mrr_at_3']:.3f}")
        print(f"Average latency: {metrics['avg_latency_seconds']:.3f}s")

    output = Path("eval/results/retrieval_baseline.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\nEvaluation saved to: {output}")


if __name__ == "__main__":
    main()