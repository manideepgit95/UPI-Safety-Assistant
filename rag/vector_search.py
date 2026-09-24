import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

INDEX_FILE = BASE_DIR / "data" / "processed" / "faiss.index"
KNOWLEDGE_BASE = BASE_DIR / "data" / "processed" / "knowledge_base.json"

MODEL_NAME = "all-MiniLM-L6-v2"


def load_knowledge_base():
    with KNOWLEDGE_BASE.open("r", encoding="utf-8") as file:
        return json.load(file)


def search(query, top_k=3):
    print(f"\nQuery: {query}")

    model = SentenceTransformer(MODEL_NAME)

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    index = faiss.read_index(str(INDEX_FILE))

    scores, indices = index.search(
        query_embedding.astype("float32"),
        top_k
    )

    chunks = load_knowledge_base()

    print("\nTop results:")

    for rank, (score, index_id) in enumerate(
        zip(scores[0], indices[0]),
        start=1
    ):
        chunk = chunks[index_id]

        print("\n-----------------------------")
        print(f"Rank: {rank}")
        print(f"Score: {score:.4f}")
        print(f"File: {chunk['file_name']}")
        print(f"Category: {chunk['category']}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print("Content:")
        print(chunk["content"][:500])


if __name__ == "__main__":
    search("Should I enter my UPI PIN to receive money?")