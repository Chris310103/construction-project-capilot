
from types import SimpleNamespace

import app.llm.agent as agent_module


def test_agent_uses_reranker(monkeypatch):
    calls = []

    def fake_rerank(question, project_name, top_k):
        calls.append((question, project_name, top_k))
        return [{
            "chunk_id": 4,
            "content": "Electrical conduits conflict with HVAC ductwork.",
            "file_name": "RFI_040.pdf",
            "page_number": 2,
            "document_type": "unclassified",
        }]

    class FakeResponses:
        def __init__(self):
            self.count = 0

        def create(self, **kwargs):
            self.count += 1

            if self.count == 1:
                call = SimpleNamespace(
                    type="function_call", name="search_project_documents",
                    arguments='{"query":"HVAC conflict"}', call_id="call_1"
                )
                return SimpleNamespace(output=[call], output_text="")

            return SimpleNamespace(output=[], output_text="Electrical coordination issue [S1].")

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(agent_module, "rerank_chunks", fake_rerank)
    monkeypatch.setattr(agent_module, "OpenAI", lambda **kwargs: FakeClient())
    monkeypatch.setattr(agent_module.settings, "openai_api_key", "test-key")

    result = agent_module.ask_project_agent("What electrical coordination problems exist?")

    assert calls == [("HVAC conflict", "Demo Boston Office Tower", 3)]
    assert "[S1]" in result["answer"]
    assert result["sources"][0]["file_name"] == "RFI_040.pdf"
