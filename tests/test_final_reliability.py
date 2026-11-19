from decimal import Decimal
from types import SimpleNamespace

from app.llm.provenance import build_sql_provenance
from app.llm.usage import add_llm_usage, empty_llm_usage
from app.tools.sql_tools import analyze_schedule_risks, get_cost_variances, get_rfi_schedule_links


PROJECT = "Demo Boston Office Tower"


def test_cost_variance_arithmetic():
    result = get_cost_variances(PROJECT)
    items = result["items"]

    total_budget = sum((Decimal(item["budget"]) for item in items), Decimal("0"))
    total_forecast = sum((Decimal(item["forecast"]) for item in items), Decimal("0"))

    assert total_budget == Decimal(result["total_budget"])
    assert total_forecast == Decimal(result["total_forecast"])
    assert total_forecast - total_budget == Decimal(result["total_variance"])

    for item in items:
        assert Decimal(item["forecast"]) - Decimal(item["budget"]) == Decimal(item["variance"])


def test_forecast_and_actual_are_distinguished():
    result = analyze_schedule_risks(PROJECT)
    activities = {item["activity_code"]: item for item in result["activities"]}

    mep = activities["MEP-100"]
    structure = activities["STR-200"]

    assert mep["finish_type"] == "forecast"
    assert mep["finish_variance_days"] == 5
    assert mep["risk_level"] == "high"

    assert structure["finish_type"] == "actual"
    assert structure["risk_level"] == "completed"
    assert "not CPM calculations" in result["note"]


def test_unverified_rfi_link():
    result = get_rfi_schedule_links(PROJECT)
    link = next(item for item in result["links"] if item["rfi_number"] == "RFI-037")

    assert link["activity_code"] == "MEP-100"
    assert link["is_verified"] is False

    source = build_sql_provenance("get_rfi_schedule_links", PROJECT, result)

    assert source["contains_unverified_links"] is True
    assert "rfi_activity_links" in source["tables"]


def test_llm_token_usage_accumulation():
    stats = empty_llm_usage()

    first = SimpleNamespace(usage=SimpleNamespace(input_tokens=800, output_tokens=20, total_tokens=820))
    second = SimpleNamespace(usage=SimpleNamespace(input_tokens=540, output_tokens=18, total_tokens=558))
    missing = SimpleNamespace(usage=None)

    add_llm_usage(stats, first)
    add_llm_usage(stats, second)
    add_llm_usage(stats, missing)

    assert stats["api_calls"] == 3
    assert stats["measured_calls"] == 2
    assert stats["input_tokens"] == 1340
    assert stats["output_tokens"] == 38
    assert stats["total_tokens"] == 1378