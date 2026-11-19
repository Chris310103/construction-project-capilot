from functools import lru_cache

from app.retrieval.hybrid_search import search_hybrid_chunks
from app.retrieval.identifier_search import search_identifier_chunks

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANK_MODEL, device="cpu")


def rerank_chunks(question: str, project_name: str, top_k: int = 3, document_type: str | None = None) -> list[dict]:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    if document_type is not None and not document_type.strip():
        raise ValueError("document_type cannot be blank")


    candidate_k = min(20, max(10, top_k * 3))

    exact_matches = search_identifier_chunks(question, project_name, candidate_k, document_type=document_type)

    if exact_matches:
        candidates = exact_matches
    else:
        candidates = search_hybrid_chunks(question, project_name, candidate_k, document_type=document_type)

    if not candidates:
        return []

    pairs = [(question, item["content"]) for item in candidates]
    scores = load_reranker().predict(pairs, batch_size=8, show_progress_bar=False)

    if len(scores) != len(candidates):
        raise RuntimeError("Reranker score count does not match candidate count")

    reranked = []

    for item, score in zip(candidates, scores):
        result = {**item, "rerank_score": float(score)}
        reranked.append(result)

    reranked.sort(key=lambda item: (-item["rerank_score"], -item["rrf_score"], item["chunk_id"]))

    for rank, item in enumerate(reranked, start=1):
        item["rerank_rank"] = rank

    return reranked[:top_k]     