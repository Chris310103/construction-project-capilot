
import app.retrieval.reranker as reranker_module
from app.retrieval.identifier_search import extract_identifiers


def test_extract_identifiers():
    question = "Compare issue EV-301 with RFI-040."

    assert extract_identifiers(question) == ["EV-301", "RFI-040"]
    assert extract_identifiers("What coordination problems occurred?") == []


def test_exact_identifier_candidates(monkeypatch):
    def make_hit(chunk_id, file_name, content):
        return {
            "chunk_id": chunk_id,
            "file_name": file_name,
            "content": content,
            "page_number": 1,
            "document_type": "unclassified",
            "rrf_score": 0.0,
        }

    def fake_exact(question, project_name, top_k, document_type=None):
        assert "EV-301" in question
        assert project_name == "Demo Evaluation Project"

        return [
            make_hit(31, "EV-301-A.pdf", "Issue ID: EV-301\nObserved condition: Fire damper access blocked."),
            make_hit(32, "EV-301-B.pdf", "Issue ID: EV-301\nCorrective action: Relocate access hatch."),
        ]

    def unexpected_hybrid(*args, **kwargs):
        raise AssertionError("Hybrid search should not replace exact identifier matches")

    class FakeReranker:
        def predict(self, pairs, batch_size=8, show_progress_bar=False):
            assert len(pairs) == 2
            return [0.7, 0.9]

    monkeypatch.setattr(reranker_module, "search_identifier_chunks", fake_exact)
    monkeypatch.setattr(reranker_module, "search_hybrid_chunks", unexpected_hybrid)
    monkeypatch.setattr(reranker_module, "load_reranker", lambda: FakeReranker())

    results = reranker_module.rerank_chunks(
        "For issue EV-301, what was observed and corrected?",
        "Demo Evaluation Project",
        top_k=3,
    )

    assert {item["file_name"] for item in results} == {"EV-301-A.pdf", "EV-301-B.pdf"}