import argparse

from app.retrieval.reranker import rerank_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--project", default="Demo Boston Office Tower")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--document-type", default=None)
    args = parser.parse_args()

    results = rerank_chunks(args.question, args.project, args.top_k, args.document_type)

    if not results:
        print("No reranked search results found.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\n===== Result {rank} =====")
        print(f"File: {item['file_name']}")
        print(f"Page: {item['page_number']}")
        print(f"Chunk ID: {item['chunk_id']}")
        print(f"RRF Score: {item['rrf_score']:.6f}")
        print(f"Rerank Score: {item['rerank_score']:.4f}")
        print(f"Content:\n{item['content']}")


if __name__ == "__main__":
    main()