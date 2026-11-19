def find_relevant_rank(results: list[dict], expected: dict) -> int | None:
    for rank, result in enumerate(results, start=1):
        if result["file_name"] != expected["file_name"]:
            continue

        if "page_number" in expected and result["page_number"] != expected["page_number"]:
            continue

        if "contains" in expected and expected["contains"] not in result["content"]:
            continue

        return rank

    return None


def calculate_metrics(ranks: list[int | None], k: int = 3) -> dict:
    if not ranks:
        raise ValueError("Cannot evaluate an empty dataset")

    hits = sum(rank is not None and rank <= k for rank in ranks)
    reciprocal_ranks = [1 / rank if rank is not None and rank <= k else 0 for rank in ranks]

    return {
        f"hit_at_{k}": hits / len(ranks),
        f"mrr_at_{k}": sum(reciprocal_ranks) / len(ranks),
        "evaluated_queries": len(ranks),
    }