from app.retrieval.keyword_search import search_keyword_chunks
from app.retrieval.vector_search import search_similar_chunks


RRF_K = 60


def search_hybrid_chunks(question: str, project_name: str, top_k: int = 3, document_type:str|None=None) -> list[dict]:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    if document_type is not None and not document_type.strip():
        raise ValueError("document_type cannot be blank")

    candidate_k = min(20, max(10, top_k * 3))

    search_kwargs = {"document_type": document_type} if document_type is not None else {}
    vector_results = search_similar_chunks(question, project_name, candidate_k, **search_kwargs)
    keyword_results = search_keyword_chunks(question, project_name, candidate_k, **search_kwargs)

    fused = {}

    for method, results in (("vector", vector_results), ("keyword", keyword_results)):
        for rank, item in enumerate(results, start=1):
            chunk_id = item["chunk_id"]

            if chunk_id not in fused:
                fused[chunk_id] = {
                    "chunk_id": chunk_id,
                    "content": item["content"],
                    "file_name": item["file_name"],
                    "document_type": item["document_type"],
                    "page_number": item["page_number"],
                    "rrf_score": 0.0,
                    "vector_rank": None,
                    "keyword_rank": None,
                    "similarity": None,
                    "keyword_score": None,
                }

            result = fused[chunk_id]
            result["rrf_score"] += 1.0 / (RRF_K + rank)
            result[f"{method}_rank"] = rank

            if method == "vector":
                result["similarity"] = item["similarity"]
            else:
                result["keyword_score"] = item["keyword_score"]

    ranked = sorted(fused.values(), key=lambda item: (-item["rrf_score"], item["chunk_id"]))

    return ranked[:top_k]