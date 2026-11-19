import re


PAREN_CITATION_PATTERN = re.compile(r"\(\s*(S\d+(?:\s*,\s*S\d+)*)\s*\)")


def normalize_document_citations(answer: str) -> str:
    return PAREN_CITATION_PATTERN.sub(lambda match: f"[{match.group(1)}]", answer)

CITATION_PATTERN = re.compile(r"\[(S\d+(?:\s*,\s*S\d+)*)\]")

def extract_citation_ids(answer: str) -> list[str]:
    cited_ids = []

    for group in CITATION_PATTERN.findall(answer):
        for source_id in group.split(","):
            source_id = source_id.strip()

            if source_id not in cited_ids:
                cited_ids.append(source_id)

    return cited_ids


def validate_document_citations(answer: str, sources: list[dict]) -> list[dict]:
    available = {source["id"]: source for source in sources}
    cited_ids = extract_citation_ids(answer)

    unknown = [source_id for source_id in cited_ids if source_id not in available]

    if unknown:
        raise ValueError(f"Unknown document citations: {unknown}")

    if sources and not cited_ids:
        raise ValueError("Missing document citations")

    return [available[source_id] for source_id in cited_ids]