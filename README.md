# 🛡️ UPI Safety Assistant

An AI-powered Retrieval-Augmented Generation (RAG) application designed to help users understand UPI safety, identify common digital-payment warning signs, and receive grounded guidance from trusted sources.

The application combines a modern React interface, FastAPI backend, hybrid retrieval, reranking, conversation memory, scam-scenario analysis, and a local LLM to provide explainable safety guidance.

---

## 🎯 Project Goal

The goal of the UPI Safety Assistant is to provide users with clear and trustworthy information about UPI and digital-payment safety.

The system is designed to:

- Answer UPI safety questions using trusted knowledge.
- Retrieve relevant information from a curated knowledge base.
- Combine semantic and keyword-based search.
- Rerank retrieved information for better relevance.
- Generate answers grounded in retrieved content.
- Display trusted sources used for the answer.
- Analyze potentially risky UPI scenarios.
- Understand recent conversation context.
- Provide safety-level indicators for user questions.
- Evaluate the RAG system using automated test cases.

---

## ✨ Key Features

### 💬 AI Safety Assistant

Users can ask questions about:

- UPI safety
- UPI PIN protection
- QR-code safety
- Payment requests
- Suspicious links
- Unknown applications
- Cashback and refund scenarios
- Digital-payment fraud awareness

### 🚨 Scam Scenario Analyzer

Users can describe a situation and receive an advisory classification such as:

- 🟢 General Guidance
- 🟡 Caution
- 🔴 Urgent Action

The analyzer provides warning indicators based on the scenario.

> The analyzer is advisory and does not guarantee that a situation is fraudulent.

### 🔎 Hybrid Retrieval

The RAG system combines:

- Semantic similarity search
- BM25 keyword search

This allows the system to handle both natural-language questions and important safety keywords.

### 🎯 Reranking

Retrieved documents are reranked using a CrossEncoder model so that the most relevant information is prioritized before being passed to the LLM.

### 📚 Trusted Sources

The knowledge base uses trusted sources including:

- National Payments Corporation of India (NPCI)
- Reserve Bank of India (RBI)
- Government of India cyber-crime resources

The application displays relevant sources alongside generated answers.

### 🧠 Conversation Memory

The assistant uses recent conversation history to understand follow-up questions.

For example:

> User: Someone sent me a QR code for a refund. Is this safe?

> User: What should I do instead?

The second question is interpreted using the previous conversation context.

### 🧪 RAG Evaluation

The project includes an automated evaluation suite containing 20 safety scenarios.

Latest internal evaluation:

**20 / 20 passed — 100% pass rate**

This result applies to the project's designed evaluation cases and should not be interpreted as a guarantee of accuracy for every real-world situation.

### 🎨 Modern Web Interface

The frontend provides:

- Responsive interface
- Dark/light appearance
- Suggested questions
- Safety indicators
- Source cards
- Loading states
- Conversation interface
- Scam scenario analysis

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │     + Vite          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Query Processing   │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       Hybrid Retrieval         │
              │                                │
              │  Semantic Search + BM25        │
              └────────────────┬───────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Reranking      │
                    │    CrossEncoder     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Relevant Context    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Qwen LLM / Ollama │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │ Grounded Answer + Sources      │
              │ + Safety Classification        │
              └────────────────────────────────┘