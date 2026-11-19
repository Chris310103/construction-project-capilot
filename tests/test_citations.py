from types import SimpleNamespace

import pytest

import app.llm.agent as agent_module
from app.llm.citations import validate_document_citations, normalize_document_citations


SOURCES = [{"id": "S1", "file_name": "rfis_demo.csv", "location": "CSV row 2", "chunk_id": 5}]


def test_valid_citation():
    result = validate_document_citations("RFI-038 concerns curtain wall details [S1].", SOURCES)
    assert result == SOURCES


def test_missing_citation():
    with pytest.raises(ValueError, match="Missing document citations"):
        validate_document_citations("RFI-038 concerns curtain wall details.", SOURCES)


def test_unknown_citation():
    with pytest.raises(ValueError, match="Unknown document citations"):
        validate_document_citations("RFI-038 concerns curtain wall details [S99].", SOURCES)


def test_sql_answer_without_document_citations():
    result = validate_document_citations("Approved change orders total $120,000.", [])
    assert result == []


def test_agent_repairs_missing_citation(monkeypatch):
    class FakeResponses:
        def __init__(self):
            self.count = 0

        def create(self, **kwargs):
            self.count += 1

            if self.count == 1:
                call = SimpleNamespace(
                    type="function_call", name="search_project_documents",
                    arguments='{"query":"curtain wall"}', call_id="call_1"
                )
                return SimpleNamespace(output=[call], output_text="")

            if self.count == 2:
                return SimpleNamespace(output=[], output_text="RFI-038 concerns curtain wall details.")

            return SimpleNamespace(output=[], output_text="RFI-038 concerns curtain wall details. [S1]")

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    client = FakeClient()
    monkeypatch.setattr(agent_module, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(agent_module.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(agent_module, "rerank_chunks", lambda *args: [{
        "chunk_id": 5,
        "file_name": "rfis_demo.csv",
        "document_type": "RFI_CSV",
        "page_number": None,
        "content": "CSV row: 2\nRFI number: RFI-038\nSubject: Curtain Wall Anchor Detail",
    }])

    result = agent_module.ask_project_agent("Which RFI concerns curtain wall details?")

    assert client.responses.count == 3
    assert "[S1]" in result["answer"]
    assert result["sources"][0]["chunk_id"] == 5


def test_grouped_citations():
    sources = [
        {"id": "S1", "file_name": "RFI_040.pdf"},
        {"id": "S2", "file_name": "RFI_037.pdf"},
        {"id": "S3", "file_name": "RFI_037.pdf"},
    ]

    answer = "Electrical conflict [S1]. HVAC structural conflict [S2, S3]."
    result = validate_document_citations(answer, sources)

    assert [item["id"] for item in result] == ["S1", "S2", "S3"]


def test_unknown_grouped_citation():
    sources = [{"id": "S1", "file_name": "RFI_040.pdf"}]

    with pytest.raises(ValueError, match="Unknown document citations"):
        validate_document_citations("Electrical conflict [S1, S99].", sources)


def test_normalize_parenthesized_citations():
    answer = "Electrical conflict (S1). Mechanical conflict (S2, S3)."
    normalized = normalize_document_citations(answer)

    assert normalized == "Electrical conflict [S1]. Mechanical conflict [S2, S3]."

    sources = [{"id": "S1"}, {"id": "S2"}, {"id": "S3"}]
    validated = validate_document_citations(normalized, sources)

    assert [source["id"] for source in validated] == ["S1", "S2", "S3"]