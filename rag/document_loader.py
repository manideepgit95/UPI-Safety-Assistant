from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def load_markdown_documents():
    """
    Load all Markdown knowledge documents from the data/raw directory.
    """

    documents = []

    for file_path in DATA_DIR.rglob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            {
                "content": content,
                "file_name": file_path.name,
                "file_path": str(file_path),
                "category": file_path.parent.name,
            }
        )

    return documents


if __name__ == "__main__":
    documents = load_markdown_documents()

    print(f"Loaded documents: {len(documents)}")

    for document in documents:
        print(
            f"- {document['file_name']} "
            f"({document['category']})"
        )