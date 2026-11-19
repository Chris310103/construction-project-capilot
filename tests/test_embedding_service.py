import logging

import pytest

import app.services.embedding_service as embedding_module


def test_invalid_batch_size():
    with pytest.raises(ValueError, match="batch_size must be positive"):
        embedding_module.embed_document_chunks(document_id=1, batch_size=0)


def test_background_embedding_failure_is_logged(monkeypatch, caplog):
    def fake_embed(document_id):
        raise RuntimeError("Simulated embedding failure")

    monkeypatch.setattr(embedding_module, "embed_document_chunks", fake_embed)

    with caplog.at_level(logging.ERROR):
        embedding_module.index_document_safely(document_id=99)

    assert "Embedding failed for document 99" in caplog.text
    assert "Simulated embedding failure" in caplog.text