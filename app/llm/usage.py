def empty_llm_usage() -> dict:
    return {
        "api_calls": 0,
        "measured_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }


def add_llm_usage(stats: dict, response) -> None:
    stats["api_calls"] += 1

    usage = getattr(response, "usage", None)
    if usage is None:
        return

    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or (input_tokens + output_tokens))

    stats["measured_calls"] += 1
    stats["input_tokens"] += input_tokens
    stats["output_tokens"] += output_tokens
    stats["total_tokens"] += total_tokens