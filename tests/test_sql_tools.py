from app.tools.sql_tools import get_total_approved_change_orders, get_cost_variances, analyze_schedule_risks, get_rfi_schedule_links

def test_get_total_approved_change_orders():
    result = get_total_approved_change_orders("Demo Boston Office Tower")

    assert result["project_name"] == "Demo Boston Office Tower"
    assert result["approved_change_order_total"] == 120000.0
    assert result["currency"] == "USD"

def test_get_cost_variances():
    result = get_cost_variances("Demo Boston Office Tower")

    assert result["as_of_date"] == "2026-08-01"
    assert result["total_budget"] == "1700000.00"
    assert result["total_forecast"] == "1820000.00"
    assert result["total_variance"] == "120000.00"
    assert len(result["items"]) == 3
    assert result["missing_cost_codes"] == []

def test_analyze_schedule_risks():
    result = analyze_schedule_risks("Demo Boston Office Tower")

    activities = {item["activity_code"]: item for item in result["activities"]}

    assert result["critical_activity_count"] == 1

    assert activities["MEP-100"]["finish_variance_days"] == 5
    assert activities["MEP-100"]["risk_level"] == "high"
    assert activities["MEP-100"]["finish_type"] == "forecast"

    assert activities["STR-200"]["finish_variance_days"] == 2
    assert activities["STR-200"]["risk_level"] == "completed"
    assert activities["STR-200"]["finish_type"] == "actual"


def test_get_rfi_schedule_links():
    result = get_rfi_schedule_links("Demo Boston Office Tower")

    links = {(item["rfi_number"], item["activity_code"]): item for item in result["links"]}
    link = links[("RFI-037", "MEP-100")]

    assert result["link_count"] >= 1
    assert link["rfi_status"] == "open"
    assert link["is_critical"] is True
    assert link["link_source"] == "demo_manual"
    assert link["is_verified"] is False
