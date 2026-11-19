from eval.metrics import calculate_metrics, find_relevant_rank


def test_find_relevant_rank():
    results = [
        {"file_name": "RFI_040.pdf", "page_number": 1, "content": "RFI header"},
        {"file_name": "RFI_040.pdf", "page_number": 2, "content": "Electrical conflict"},
    ]

    expected = {"file_name": "RFI_040.pdf", "page_number": 2}

    assert find_relevant_rank(results, expected) == 2


def test_missing_relevant_document():
    results = [{"file_name": "other.pdf", "page_number": 1, "content": "Other"}]

    assert find_relevant_rank(results, {"file_name": "RFI_040.pdf"}) is None


def test_calculate_metrics():
    metrics = calculate_metrics([1, 2, None, 3], k=3)

    assert metrics["hit_at_3"] == 0.75
    assert abs(metrics["mrr_at_3"] - 0.4583333333) < 1e-6
    assert metrics["evaluated_queries"] == 4