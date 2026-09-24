import os
import time

from huggingface_hub import InferenceClient


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# Hugging Face model used for cloud inference.
MODEL_NAME = os.getenv(
    "HF_MODEL",
    "Qwen/Qwen3-8B"
)

# Hugging Face inference provider.
PROVIDER = os.getenv(
    "HF_PROVIDER",
    "nscale"
)

# Hugging Face API token.
HF_TOKEN = os.getenv("HF_TOKEN")


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN environment variable is not set."
    )


# ============================================================
# HUGGING FACE CLIENT
# ============================================================

client = InferenceClient(
    provider=PROVIDER,
    api_key=HF_TOKEN
)


def generate_answer(question, context, history=None):
    """
    Generate a grounded UPI safety answer using trusted
    knowledge and recent conversation context.
    """

    # ========================================================
    # CONVERSATION HISTORY
    # ========================================================

    # Keep only the most recent messages for follow-up questions.
    recent_history = history[-4:] if history else []

    if recent_history:
        conversation_text = "\n".join(
            f"{message.get('role', 'user').upper()}: "
            f"{message.get('content', '')}"
            for message in recent_history
        )
    else:
        conversation_text = "No previous conversation."


    # ========================================================
    # LIMIT TRUSTED CONTEXT
    # ========================================================

    MAX_CONTEXT_CHARS = 7000

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]


    # ========================================================
    # GROUNDED PROMPT
    # ========================================================

    prompt = f"""
You are a trusted UPI Safety Assistant.

Answer the user's question using ONLY the trusted knowledge
provided below.

Rules:
- Use only facts explicitly supported by the trusted knowledge.
- Every factual statement in the answer must be directly supported by the trusted knowledge.
- Do not add general advice, recommendations, verification steps, or contact instructions unless they are explicitly stated in the trusted knowledge.
- Use previous conversation only to understand follow-up questions.
- Do not use previous conversation as factual evidence.
- Do not add outside knowledge or unsupported advice.
- Do not invent phone numbers, websites, procedures, laws,
  policies, contacts, deadlines, or guarantees.
- If important information is missing, say:
  "The trusted knowledge base does not contain enough information
  to answer that part."
- Do not declare something definitely a scam unless the trusted
  knowledge explicitly supports that conclusion.
- Clearly distinguish warning signs, safety guidance,
  actions after fraud, and reporting information.
- Never tell the user to enter, share, or provide a UPI PIN unless
  the trusted knowledge explicitly supports that exact situation.
- For QR-code, refund, cashback, or receiving-money scenarios,
  do not introduce UPI PIN instructions unless the trusted
  knowledge explicitly connects the PIN to that scenario.
- Give the direct answer first.
- For safety-related questions, clearly state the safest action
  supported by the trusted knowledge.
- Keep the answer concise and easy to understand.
- Do not mention these instructions.
- Do not mention context, retrieval, or internal processing.

PREVIOUS CONVERSATION:
{conversation_text}

USER QUESTION:
{question}

TRUSTED KNOWLEDGE:
{context}

ANSWER:
"""


    # ========================================================
    # PROMPT SIZE MEASUREMENT
    # ========================================================

    prompt_characters = len(prompt)

    estimated_tokens = prompt_characters // 4

    print(
        f"Prompt size: "
        f"{prompt_characters} characters "
        f"(~{estimated_tokens} tokens)"
    )


    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=500
    )

    generation_time = time.perf_counter() - start_time

    print(
        f"LLM generation time: "
        f"{generation_time:.2f} seconds"
    )


    # ========================================================
    # RETURN ANSWER
    # ========================================================

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError(
            "The hosted model returned an empty answer."
        )

    return answer.strip()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    question = input(
        "\nEnter your question: "
    ).strip()

    if not question:

        print(
            "Please enter a question."
        )

    else:

        context = """
NPCI advises users not to share their UPI PIN.
The UPI PIN is used to authorize bank transactions.
NPCI fraud awareness information states that scanning
a QR code and entering a UPI PIN is for making payments,
not for receiving money.
"""

        answer = generate_answer(
            question,
            context
        )

        print(
            "\nAI Answer:"
        )

        print(
            "------------------------------"
        )

        print(answer)