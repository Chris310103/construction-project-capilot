
from fastapi.testclient import TestClient

from app.api.routes import ask as ask_route
from app.main import app


client = TestClient(app)


def test_ask_api(monkeypatch):
    def fake_ask_project(question, project_name, top_k):
        assert question == "What coordination problems were reported?"
        assert project_name == "Demo Boston Office Tower"
        assert top_k == 3

        return {
            "answer": "Electrical conduits conflict with HVAC ductwork. [S1]",
            "sources": [
                {"id": "S1", "file_name": "RFI_040.pdf", "location": "Page 2", "chunk_id": 4}
            ],
        }

    monkeypatch.setattr(ask_route, "ask_project", fake_ask_project)

    response = client.post("/ask", json={"question": "What coordination problems were reported?"})

    assert response.status_code == 200
    assert response.json()["sources"][0]["file_name"] == "RFI_040.pdf"
    assert "[S1]" in response.json()["answer"]


def test_ask_rejects_empty_question():
    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 422


def test_ask_rejects_invalid_top_k():
    response = client.post("/ask", json={"question": "HVAC conflict", "top_k": 100})

    assert response.status_code == 422