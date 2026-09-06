# 2nd Review (20% Milestone) — Presentation Cheat Sheet for Syed (Muzakkir)

This document provides a concise 1-minute live demo walkthrough, technical explanation notes, and direct answers to evaluator questions for **Syed (Mobile UI / Client)**.

---

## 1. 5-Minute Team Presentation Breakdown

| Time | Presenter | Module | Key Action |
| :--- | :--- | :--- | :--- |
| **1.0 min** | **Abhinav** | Architecture & RAG | Shows 3-tier storage architecture (Metadata DB, pgvector, File storage) |
| **1.5 min** | **Prasanna** | Ingestion & Validation | Shows file validation (magic bytes, size limits) & PDF chunking with page numbers |
| **1.5 min** | **Abhinav** | Retrieval & Database | Runs pgvector HNSW cosine query via API script, shows top-K results & scores |
| **1.0 min** | **Syed (You)** | **Frontend & Integration** | **Shows Flutter calling `/health` and rendering retrieved semantic search results** |

---

## 2. Syed's 60-Second Live Demo Script

### [0:00 – 0:15] Screen 1: Backend Connection & Health Probing
> *"Good morning/afternoon, evaluators. I am Syed Muzakkir, responsible for the client interface, integration, and end-to-end frontend testing.*
> *Here on Screen 1, our Flutter application connects directly to the FastAPI backend using Dio and Riverpod state management.*
> *When the app launches, it probes `GET /health`. As you can see from our live badge, the backend is active on port 8000 with low roundtrip latency. The app automatically detects the host platform—routing to `10.0.2.2:8000` on Android emulators and `127.0.0.1:8000` on desktop and simulators."*

### [0:15 – 0:45] Screen 2: Semantic Memory Retrieval & Upload UI
> *"Moving to Screen 2, we have our Memory Search and Ingestion panel.*
> *At the top, users can select a PDF or text document. Our upload panel validates the document format and prepares it for Module 1's ingestion pipeline.*
> *Below, we query the user's vector memories using natural language. For instance, clicking or typing: **'What is Banker's algorithm?'** or **'What did I learn about deadlock prevention?'**.*
> *When we tap Search, the app issues a `POST /api/v1/memories/search` request scoped strictly to the authenticated `user_id`. pgvector computes cosine similarity across stored 1536-dimensional embeddings, and our Flutter client renders the top-K chunks with document titles, page number badges, and similarity confidence scores."*

### [0:45 – 1:00] Wrap-up & Fallback
> *"If a query is completely unrelated—like 'How to bake a chocolate cake?'—the system filters out low-similarity chunks, returning zero false positives to prevent downstream LLM hallucination.*
> *As a backup and verification layer, our OpenAPI Swagger documentation is also running live at `http://127.0.0.1:8000/docs`. Thank you!"*

---

## 3. Key Evaluator Questions & Your Exact Answers

### Q1: "Why use pgvector instead of Pinecone or Chroma?"
> **Answer:**
> *"Keeping relational metadata (user accounts, document records, processing status) and vector embeddings in a single PostgreSQL database simplifies transactions, enables atomic cascading deletes (`ON DELETE CASCADE`), and avoids managing multiple cloud database providers during our MVP development."*

### Q2: "How do you prevent data leaks between different users?"
> **Answer:**
> *"Every chunk record in pgvector has a `user_id` foreign key, and all vector similarity queries enforce strict SQL `WHERE chunks.user_id = :user_id` filtering. The mobile app binds the authenticated user ID into every payload, ensuring zero cross-tenant leakage."*

### Q3: "How will you prevent LLM hallucinations?"
> **Answer:**
> *"In Phase 4, the LLM will only receive retrieved chunks as grounded context with explicit system prompts instructing it to answer solely based on provided sources and state 'I couldn't find this in your memories' if similarity scores fall below our minimum threshold."*

---

## 4. Live Demo Commands & URLs

- **Interactive Swagger Docs (Backup):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Start Backend Manually (if needed):**
  ```powershell
  cd s:\GIT\digital-memory-assistant\backend
  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
  ```
- **Run Standalone Presentation Script (Abhinav's CLI Demo):**
  ```powershell
  $env:PYTHONUTF8=1
  backend\.venv\Scripts\python.exe backend\scripts\demo_walkthrough.py
  ```
