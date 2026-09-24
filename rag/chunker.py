from document_loader import load_markdown_documents


def split_into_paragraphs(text):
    """
    Split a document into meaningful paragraphs/sections.
    """
    paragraphs = []

    for block in text.split("\n\n"):
        block = block.strip()

        if block:
            paragraphs.append(block)

    return paragraphs


def chunk_text(text, chunk_size=800, overlap_paragraphs=1):
    """
    Create chunks using paragraph boundaries.
    """

    paragraphs = split_into_paragraphs(text)

    if not paragraphs:
        return []

    chunks = []
    current_paragraphs = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)

        if (
            current_paragraphs
            and current_length + paragraph_length > chunk_size
        ):
            chunks.append("\n\n".join(current_paragraphs))

            current_paragraphs = current_paragraphs[
                -overlap_paragraphs:
            ]

            current_length = sum(
                len(item) for item in current_paragraphs
            )

        current_paragraphs.append(paragraph)
        current_length += paragraph_length

    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs))

    return chunks


def create_chunks():
    documents = load_markdown_documents()
    all_chunks = []

    for document in documents:
        chunks = chunk_text(document["content"])

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "chunk_id": (
                        f"{document['category']}_"
                        f"{document['file_name']}_"
                        f"{index}"
                    ),
                    "content": chunk,
                    "file_name": document["file_name"],
                    "category": document["category"],
                    "source_file": document["file_path"],
                }
            )

    return all_chunks


if __name__ == "__main__":
    chunks = create_chunks()

    print(f"Total chunks created: {len(chunks)}")

    for chunk in chunks[:5]:
        print("\n--- CHUNK ---")
        print(f"ID: {chunk['chunk_id']}")
        print(f"Category: {chunk['category']}")
        print(chunk["content"][:400])