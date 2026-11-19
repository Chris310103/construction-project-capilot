SQL_TOOL_TABLES = {
    "get_total_approved_change_orders": ["change_orders"],
    "get_open_rfis": ["rfis"],
    "get_cost_variances": ["cost_records"],
    "analyze_schedule_risks": ["schedule_activities"],
    "get_rfi_schedule_links": ["rfi_activity_links", "rfis", "schedule_activities"],
}


def build_sql_provenance(tool_name: str, project_name: str, data: dict) -> dict | None:
    tables = SQL_TOOL_TABLES.get(tool_name)

    if tables is None:
        return None

    source = {
        "tool": tool_name,
        "tables": tables,
        "project_name": project_name,
        "filters": {},
    }

    if tool_name == "get_total_approved_change_orders":
        source["filters"]["status"] = "approved"

    elif tool_name == "get_open_rfis":
        source["filters"]["status"] = "open"

    elif tool_name == "get_cost_variances":
        source["filters"]["snapshot"] = "latest"

    elif tool_name == "get_rfi_schedule_links":
        source["filters"]["rfi_status"] = "open"
        source["filters"]["activity_is_critical"] = True
        source["contains_unverified_links"] = any(
            link.get("is_verified") is False for link in data.get("links", [])
        )

    if data.get("as_of_date"):
        source["as_of_date"] = data["as_of_date"]

    return source