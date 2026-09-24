import json
from pathlib import Path

from chunker import create_chunks


OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "knowledge_base.json"
)


def build_knowledge_base():
    chunks = create_chunks()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, indent=2, ensure_ascii=False)

    print(f"Knowledge base created successfully.")
    print(f"Total chunks: {len(chunks)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_knowledge_base()