# Digital Memory Assistant

A personal knowledge and memory assistant for finding information across a user's uploaded digital material.

## MVP

Upload PDF or text documents, extract and chunk their content, search it semantically, and answer questions with source references.

## Architecture

    Flutter mobile app
            ↓
    FastAPI backend
            ↓
    PostgreSQL + pgvector
            ↓
    File storage

## Project structure

- `backend/` — FastAPI application and database logic
- `mobile/` — Flutter application
- `docs/` — architecture, API, and team documentation

## Team

- P. Prasanna Kumar — ingestion and preprocessing
- Nagendra Abhinav K. — embeddings, retrieval, and storage
- Syed Muzakkir — interface, integration, and testing

## Development workflow

- Do not push directly to `main`.
- Work in a feature branch and open a pull request for review.
- Never commit API keys, passwords, or `.env` files.
