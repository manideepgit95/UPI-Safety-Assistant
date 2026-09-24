import faiss
import numpy as np
from pathlib import Path


EMBEDDINGS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "embeddings.npy"
)

INDEX_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "faiss.index"
)


def create_vector_index():
    embeddings = np.load(EMBEDDINGS_FILE)

    dimension = embeddings.shape[1]

    print(f"Loaded embeddings: {embeddings.shape}")
    print(f"Vector dimension: {dimension}")

    # Inner Product works as cosine similarity
    # because our embeddings were normalized.
    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings.astype("float32"))

    faiss.write_index(index, str(INDEX_FILE))

    print(f"Vectors stored in index: {index.ntotal}")
    print(f"FAISS index saved to: {INDEX_FILE}")


if __name__ == "__main__":
    create_vector_index()