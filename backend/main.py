from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.rag_pipeline import answer_question
from backend.scam_analyzer import analyze_scenario


app = FastAPI(
    title="UPI Safety Assistant API",
    description="RAG-based UPI safety assistant",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


def determine_safety_level(question):
    """
    Determine the safety level of the user's question.

    This is an advisory classification.
    It does not confirm that a situation is fraudulent.
    """

    text = question.lower().strip()

    # ---------------------------------------------------------
    # URGENT
    # ---------------------------------------------------------

    urgent_keywords = [
        "money stolen",
        "money was stolen",
        "money has been stolen",
        "money deducted",
        "money has been deducted",
        "money lost",
        "lost money",

        "unauthorized transaction",
        "unauthorised transaction",
        "unauthorized upi transaction",
        "unauthorised upi transaction",

        "fraudulent transaction",

        "account hacked",
        "account has been hacked",
        "account was hacked",

        "already scammed",
        "sent money to scammer",
        "paid scammer",
    ]

    if any(keyword in text for keyword in urgent_keywords):
        return {
            "level": "urgent",
            "label": "Urgent Action",
            "icon": "🔴",
        }

    # ---------------------------------------------------------
    # CAUTION - DIRECT INDICATORS
    # ---------------------------------------------------------

    caution_keywords = [
        "scam",
        "scammer",
        "suspicious",
        "fraud",
        "fraudster",

        "unknown person",

        "unknown qr",
        "unknown qr code",
        "unknown qr-code",

        "suspicious qr",
        "suspicious qr code",

        "unexpected qr",
        "unexpected qr code",

        "unknown link",
        "suspicious link",

        "unknown app",
        "install app",
        "download app",
        "remote access",

        "cashback",
        "reward",
        "prize",
        "refund",

        "collect request",
        "payment request",
        "request money",
    ]

    if any(keyword in text for keyword in caution_keywords):
        return {
            "level": "caution",
            "label": "Caution",
            "icon": "🟡",
        }

    # ---------------------------------------------------------
    # QR CODE + RECEIVING MONEY / REWARD CONTEXT
    # ---------------------------------------------------------

    qr_keywords = [
        "qr code",
        "qr",
        "scan qr",
        "scan a qr",
        "scan this qr",
    ]

    receiving_keywords = [
        "receive",
        "receiving",
        "get money",
        "receive money",
        "refund",
        "cashback",
        "reward",
        "prize",
        "₹",
        "rs ",
        "rs.",
        "rupees",
    ]

    has_qr = any(
        keyword in text
        for keyword in qr_keywords
    )

    has_receiving_context = any(
        keyword in text
        for keyword in receiving_keywords
    )

    if has_qr and has_receiving_context:
        return {
            "level": "caution",
            "label": "Caution",
            "icon": "🟡",
        }

    # ---------------------------------------------------------
    # UNKNOWN / UNEXPECTED QR CODE + SCAN REQUEST
    # ---------------------------------------------------------

    has_qr = any(
        keyword in text
        for keyword in [
            "qr",
            "qr code",
        ]
    )

    has_scan_request = any(
        phrase in text
        for phrase in [
            "asked me to scan",
            "ask me to scan",
            "asked me scan",
            "ask me scan",
            "scan it",
            "scan the qr",
            "scan this qr",
            "scan a qr",
        ]
    )

    has_unknown_context = any(
        phrase in text
        for phrase in [
            "don't know",
            "do not know",
            "unknown",
            "unexpected",
            "someone",
            "stranger",
        ]
    )

    if (
        has_qr
        and has_scan_request
        and has_unknown_context
    ):
        return {
            "level": "caution",
            "label": "Caution",
            "icon": "🟡",
        }

    # ---------------------------------------------------------
    # GENERAL
    # ---------------------------------------------------------

    return {
        "level": "general",
        "label": "General Guidance",
        "icon": "🟢",
    }


# -------------------------------------------------------------
# ROOT
# -------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "UPI Safety Assistant API is running"
    }


# -------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# -------------------------------------------------------------
# CHAT
# -------------------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    result = answer_question(
        request.question,
        request.history
    )

    safety = determine_safety_level(
        request.question
    )

    return {
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "safety": safety,
    }


# -------------------------------------------------------------
# SCAM SCENARIO ANALYZER
# -------------------------------------------------------------

@app.post("/analyze-scenario")
def analyze_scam_scenario(
    request: ChatRequest
):

    result = analyze_scenario(
        request.question
    )

    return {
        "scenario": request.question,
        "analysis": result,
    }


# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------

if __name__ == "__main__":

    import os
    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port
    )