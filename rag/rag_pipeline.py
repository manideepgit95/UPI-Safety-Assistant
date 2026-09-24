import json
import time
from pathlib import Path

from rag.reranker import retrieve_and_rerank
from rag.llm_generator import generate_answer


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCES_FILE = (
    BASE_DIR
    / "data"
    / "metadata"
    / "sources.json"
)


# ============================================================
# LOAD SOURCE METADATA
# ============================================================

def load_source_metadata():
    """
    Load trusted source information from sources.json.
    """

    with SOURCES_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# MAP KNOWLEDGE-BASE FILES TO TRUSTED SOURCES
# ============================================================

SOURCE_MAPPING = {
    "upi_basics.md": "npci_upi",
    "fraud_awareness.md": "npci_fraud_awareness",
    "payment_requests.md": "npci_bhim",
    "qr_code_safety.md": "npci_fraud_awareness",
    "after_fraud.md": "cybercrime_portal",
    "digital_payment_safety.md": "rbi_digital_safety",
    "qr_safety.md": "rbi_digital_safety",
    "reporting_fraud.md": "cybercrime_portal",
    "cyber_crime_reporting.md": "cybercrime_portal",
}


# ============================================================
# BUILD CONVERSATION-AWARE RETRIEVAL QUERY
# ============================================================

def build_retrieval_query(
    question,
    history=None
):
    """
    Build a retrieval query that includes recent conversation
    context when the current question looks like a follow-up.

    Example:

    Previous:
        Someone sent me a QR code for a refund.

    Current:
        What should I do instead?

    Retrieval query becomes approximately:

        Someone sent me a QR code for a refund.
        What should I do instead?
    """

    if not history:
        return question

    recent_history = history[-4:]

    previous_user_messages = []

    for message in recent_history:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        ).strip()

        if (
            role == "user"
            and content
            and content.lower() != question.lower()
        ):
            previous_user_messages.append(
                content
            )

    if not previous_user_messages:
        return question

    # --------------------------------------------------------
    # Keep only the most recent user context.
    # --------------------------------------------------------

    previous_context = previous_user_messages[-2:]

    retrieval_query = (
        "Previous user context: "
        + " ".join(previous_context)
        + "\nCurrent user question: "
        + question
    )

    return retrieval_query


# ============================================================
# DETECT RECEIVING / REFUND QUESTIONS
# ============================================================

def is_receiving_money_question(
    question
):
    """
    Detect questions where the user is talking about
    receiving money, refunds, cashback, or rewards.
    """

    text = question.lower()

    receiving_keywords = [
        "receive",
        "receiving",
        "refund",
        "cashback",
        "reward",
        "receive money",
        "get money",
        "money received",
        "payment received",
    ]

    return any(
        keyword in text
        for keyword in receiving_keywords
    )


# ============================================================
# CLEAN CHUNK FOR RECEIVING / REFUND QUESTIONS
# ============================================================

def clean_chunk_for_receiving_question(
    content
):
    """
    Remove payment-authorization instructions from a
    chunk when the user's question is specifically about
    receiving money or receiving a refund.

    The original knowledge base is never modified.
    Only the temporary LLM context is cleaned.
    """

    lines = content.splitlines()

    cleaned_lines = []

    skip_pin_section = False

    for line in lines:

        lower_line = line.lower().strip()

        # ----------------------------------------------------
        # Remove lines specifically about entering a PIN
        # for payment authorization.
        # ----------------------------------------------------

        pin_related = (
            "before entering your upi pin"
            in lower_line
            or
            "entering your upi pin"
            in lower_line
            or
            "enter your upi pin"
            in lower_line
            or
            "upi pin is used to authorize"
            in lower_line
            or
            "upi pin to authorize"
            in lower_line
        )

        if pin_related:

            skip_pin_section = True

            continue

        # ----------------------------------------------------
        # Skip bullet points that directly describe
        # payment authorization through a PIN.
        # ----------------------------------------------------

        if skip_pin_section:

            if (
                lower_line.startswith("-")
                or
                lower_line.startswith("*")
            ):
                continue

            if not lower_line:

                skip_pin_section = False

                continue

            if lower_line.startswith("#"):

                skip_pin_section = False

            else:

                continue

        cleaned_lines.append(
            line
        )

    cleaned_content = "\n".join(
        cleaned_lines
    ).strip()

    return cleaned_content


# ============================================================
# BUILD QUERY-AWARE LLM CONTEXT
# ============================================================

def build_context(
    question,
    results
):
    """
    Build focused context for the LLM.

    For normal questions:
        Keep retrieved content unchanged.

    For refund/receiving-money questions:
        Remove unrelated payment-PIN instructions.
    """

    receiving_question = (
        is_receiving_money_question(
            question
        )
    )

    context_parts = []

    source_number = 1

    for result in results:

        chunk = result["chunk"]

        content = chunk["content"]

        # ----------------------------------------------------
        # Apply temporary context cleaning.
        # ----------------------------------------------------

        if receiving_question:

            content = (
                clean_chunk_for_receiving_question(
                    content
                )
            )

        # ----------------------------------------------------
        # Skip completely empty content.
        # ----------------------------------------------------

        if not content.strip():

            continue

        context_parts.append(
            f"""
SOURCE {source_number}
File: {chunk['file_name']}
Category: {chunk['category']}

Content:
{content}
"""
        )

        source_number += 1

    return "\n".join(
        context_parts
    )


# ============================================================
# BUILD CLEAN SOURCE LIST FOR FRONTEND
# ============================================================

def build_sources(
    results
):
    """
    Build a clean list of trusted sources for the frontend.

    Multiple retrieved chunks can belong to the same official
    source. The frontend displays each trusted source only once.
    """

    source_metadata = (
        load_source_metadata()
    )

    source_lookup = {
        source["source_id"]: source
        for source in source_metadata
    }

    sources = []

    seen_sources = set()

    for result in results:

        chunk = result["chunk"]

        source_id = SOURCE_MAPPING.get(
            chunk["file_name"]
        )

        source = source_lookup.get(
            source_id,
            {}
        )

        # ----------------------------------------------------
        # Skip duplicate trusted sources.
        # ----------------------------------------------------

        if source_id in seen_sources:

            continue

        seen_sources.add(
            source_id
        )

        # ----------------------------------------------------
        # Add unique source.
        # ----------------------------------------------------

        sources.append(
            {
                "source_id": source_id,

                "organization": source.get(
                    "organization",
                    "Trusted Source"
                ),

                "title": source.get(
                    "title",
                    chunk["file_name"]
                ),

                "url": source.get(
                    "url",
                    ""
                ),

                "trust_level": source.get(
                    "trust_level",
                    "official"
                ),

                "file_name": chunk[
                    "file_name"
                ],

                "category": chunk[
                    "category"
                ],

                "chunk_id": chunk[
                    "chunk_id"
                ],

                "rerank_score": result[
                    "rerank_score"
                ],
            }
        )

    return sources


# ============================================================
# COMPLETE RAG PIPELINE
# ============================================================

def answer_question(
    question,
    history=None
):
    """
    Complete RAG pipeline:

    User Question
          ↓
    Conversation-Aware Query
          ↓
    Hybrid Retrieval
          ↓
    CrossEncoder Reranking
          ↓
    Query-Aware Context Cleaning
          ↓
    Trusted Context
          ↓
    LLM + Conversation History
          ↓
    Grounded Answer
          ↓
    Clean Trusted Sources
    """

    print(
        "\nSearching trusted knowledge base..."
    )

    # --------------------------------------------------------
    # Make sure history is always a list.
    # --------------------------------------------------------

    if history is None:

        history = []


    # --------------------------------------------------------
    # Build retrieval query.
    # --------------------------------------------------------

    retrieval_query = (
        build_retrieval_query(
            question,
            history
        )
    )

    # --------------------------------------------------------
    # Show whether conversation context is being used.
    # --------------------------------------------------------

    if retrieval_query != question:

        print(
            "Using recent conversation "
            "context for retrieval..."
        )


    # --------------------------------------------------------
    # Start retrieval timer.
    # --------------------------------------------------------

    start_time = (
        time.perf_counter()
    )


    # --------------------------------------------------------
    # Retrieve and rerank trusted information.
    # --------------------------------------------------------

    results = (
        retrieve_and_rerank(
            retrieval_query,
            retrieval_k=5,
            final_k=3
        )
    )


    # --------------------------------------------------------
    # Calculate retrieval time.
    # --------------------------------------------------------

    retrieval_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Retrieval + reranking time: "
        f"{retrieval_time:.2f} seconds"
    )


    # --------------------------------------------------------
    # Handle no results.
    # --------------------------------------------------------

    if not results:

        return {
            "answer": (
                "I could not find relevant information "
                "in the trusted knowledge base."
            ),
            "sources": []
        }


    # --------------------------------------------------------
    # Build query-aware trusted context.
    #
    # IMPORTANT:
    # The original user question is passed here so that
    # context cleaning is based on the actual question.
    # --------------------------------------------------------

    context = build_context(
        question,
        results
    )


    # --------------------------------------------------------
    # Generate grounded answer.
    # --------------------------------------------------------

    print(
        "Generating answer..."
    )

    answer = generate_answer(
        question,
        context,
        history
    )


    # --------------------------------------------------------
    # Build clean source list.
    # --------------------------------------------------------

    sources = build_sources(
        results
    )


    # --------------------------------------------------------
    # Return final result.
    # --------------------------------------------------------

    return {
        "answer": answer,
        "sources": sources
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    question = input(
        "\nEnter your UPI safety question: "
    ).strip()


    # --------------------------------------------------------
    # Validate question.
    # --------------------------------------------------------

    if not question:

        print(
            "Please enter a question."
        )


    else:

        # ----------------------------------------------------
        # Run complete RAG pipeline.
        # ----------------------------------------------------

        result = answer_question(
            question
        )


        # ====================================================
        # DISPLAY ANSWER
        # ====================================================

        print(
            "\n================================"
        )

        print(
            "AI ANSWER"
        )

        print(
            "================================"
        )

        print(
            result["answer"]
        )


        # ====================================================
        # DISPLAY SOURCES
        # ====================================================

        print(
            "\n================================"
        )

        print(
            "SOURCES"
        )

        print(
            "================================"
        )


        if result["sources"]:

            for index, source in enumerate(
                result["sources"],
                start=1
            ):

                print(
                    f"\n[{index}] "
                    f"{source['file_name']}"
                )

                print(
                    f"Category: "
                    f"{source['category']}"
                )

                print(
                    f"Source: "
                    f"{source['title']}"
                )

                print(
                    f"Organization: "
                    f"{source['organization']}"
                )

        else:

            print(
                "No sources found."
            )