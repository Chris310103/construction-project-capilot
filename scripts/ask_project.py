import argparse

from app.llm.rag import ask_project


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", type=str)
    parser.add_argument("--project", default="Demo Boston Office Tower")
    parser.add_argument("--top-k", type=int, default=3)

    args = parser.parse_args()

    result = ask_project(args.question, args.project, args.top_k)

    print("\n===== AI Answer =====")
    print(result["answer"])

    print("\n===== Cited Sources =====")

    if not result["sources"]:
        print("No source citations returned.")

    for source in result["sources"]:
        print(f"[{source['id']}] {source['file_name']} | {source['location']} | Chunk {source['chunk_id']}")


if __name__ == "__main__":
    main()