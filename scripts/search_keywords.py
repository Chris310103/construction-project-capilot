import argparse

from app.retrieval.keyword_search import search_keyword_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--project", default="Demo Boston Office Tower")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    results = search_keyword_chunks(args.query, args.project, args.top_k)

    if not results:
        print("No keyword matches found.")
        return

    for index, result in enumerate(results, start=1):
        print(f"\n===== Result {index} =====")
        print(f"File: {result['file_name']}")
        print(f"Page: {result['page_number']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Keyword Score: {result['keyword_score']:.4f}")
        print(f"Content:\n{result['content']}")


if __name__ == "__main__":
    main()