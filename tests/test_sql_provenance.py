from app.llm.provenance import build_sql_provenance


def test_change_order_provenance():
    source = build_sql_provenance(
        "get_total_approved_change_orders",
        "Demo Boston Office Tower",
        {"approved_change_order_total": 120000.0},
    )

    assert source["tables"] == ["change_orders"]
    assert source["filters"]["status"] == "approved"


def test_unverified_rfi_link_provenance():
    source = build_sql_provenance(
        "get_rfi_schedule_links",
        "Demo Boston Office Tower",
        {"links": [{"rfi_number": "RFI-037", "is_verified": False}]},
    )

    assert source["contains_unverified_links"] is True
    assert "schedule_activities" in source["tables"]


def test_document_retrieval_has_no_sql_source():
    source = build_sql_provenance("search_project_documents", "Demo Boston Office Tower", {})

    assert source is None