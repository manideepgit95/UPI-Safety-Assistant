import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


KNOWLEDGE_BASE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "knowledge_base.json"
)

EMBEDDINGS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "embeddings.npy"
)

MODEL_NAME = "all-MiniLM-L6-v2"


def load_chunks():
    with KNOWLEDGE_BASE.open("r", encoding="utf-8") as file:
        return json.load(file)


def create_embeddings():
    chunks = load_chunks()

    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["content"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    np.save(EMBEDDINGS_FILE, embeddings)

    print(f"Chunks: {len(chunks)}")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"Embeddings saved to: {EMBEDDINGS_FILE}")


if __name__ == "__main__":
    create_embeddings()