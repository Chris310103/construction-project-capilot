import argparse

from app.retrieval.hybrid_search import search_hybrid_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--project", default="Demo Boston Office Tower")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--document-type", default=None)

    args = parser.parse_args()
    results = search_hybrid_chunks(args.question, args.project, args.top_k, document_type=args.document_type)

    if not results:
        print("No hybrid search results found.")
        return

    for index, result in enumerate(results, start=1):
        print(f"\n===== Result {index} =====")
        print(f"File: {result['file_name']}")
        print(f"Page: {result['page_number']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"RRF Score: {result['rrf_score']:.6f}")
        print(f"Vector Rank: {result['vector_rank']}")
        print(f"Keyword Rank: {result['keyword_rank']}")
        print(f"Content:\n{result['content']}")


if __name__ == "__main__":
    main()