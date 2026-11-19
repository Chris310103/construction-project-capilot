import pytest

import app.retrieval.hybrid_search as hybrid_module


def make_hit(chunk_id: int, **scores) -> dict:
    return {
        "chunk_id": chunk_id,
        "content": f"Chunk {chunk_id}",
        "file_name": "demo.csv",
        "document_type": "RFI",
        "page_number": None,
        **scores,
    }


def test_rrf_fusion(monkeypatch):
    def fake_vector(question, project_name, top_k):
        return [
            make_hit(2, similarity=0.90),
            make_hit(1, similarity=0.70),
        ]

    def fake_keyword(question, project_name, top_k):
        return [
            make_hit(1, keyword_score=0.40),
            make_hit(3, keyword_score=0.20),
        ]

    monkeypatch.setattr(hybrid_module, "search_similar_chunks", fake_vector)
    monkeypatch.setattr(hybrid_module, "search_keyword_chunks", fake_keyword)

    results = hybrid_module.search_hybrid_chunks("HVAC routing", "Demo Boston Office Tower", top_k=3)

    assert [item["chunk_id"] for item in results] == [1, 2, 3]
    assert results[0]["vector_rank"] == 2
    assert results[0]["keyword_rank"] == 1
    assert results[0]["rrf_score"] == pytest.approx(1 / 62 + 1 / 61)


def test_keyword_only_results(monkeypatch):
    monkeypatch.setattr(hybrid_module, "search_similar_chunks", lambda *args: [])
    monkeypatch.setattr(hybrid_module, "search_keyword_chunks", lambda *args: [make_hit(5, keyword_score=0.25)])

    results = hybrid_module.search_hybrid_chunks("RFI-038", "Demo Boston Office Tower")

    assert len(results) == 1
    assert results[0]["chunk_id"] == 5
    assert results[0]["vector_rank"] is None
    assert results[0]["keyword_rank"] == 1


def test_invalid_hybrid_query():
    with pytest.raises(ValueError, match="Question cannot be empty"):
        hybrid_module.search_hybrid_chunks("", "Demo Boston Office Tower")

    with pytest.raises(ValueError, match="top_k must be"):
        hybrid_module.search_hybrid_chunks("HVAC", "Demo Boston Office Tower", top_k=0)


def test_document_type_filter_forwarding(monkeypatch):
    calls = []

    def fake_vector(question, project_name, top_k, document_type=None):
        calls.append(("vector", document_type))
        return [make_hit(5, similarity=0.85)]

    def fake_keyword(question, project_name, top_k, document_type=None):
        calls.append(("keyword", document_type))
        return [make_hit(5, keyword_score=0.30)]

    monkeypatch.setattr(hybrid_module, "search_similar_chunks", fake_vector)
    monkeypatch.setattr(hybrid_module, "search_keyword_chunks", fake_keyword)

    results = hybrid_module.search_hybrid_chunks(
        "curtain wall anchor", "Demo Boston Office Tower", document_type="RFI_CSV"
    )

    assert calls == [("vector", "RFI_CSV"), ("keyword", "RFI_CSV")]
    assert len(results) == 1
    assert results[0]["chunk_id"] == 5
