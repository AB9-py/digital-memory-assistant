# Muzakkir Work - Mobile UI / Client

This folder contains Muzakkir's allotted mobile UI work for the Digital Memory Assistant review.

## Delivered

- Flutter mobile app source under `mobile/`.
- Dio client configured for the FastAPI backend.
- Riverpod providers for backend health and semantic memory search.
- Health screen calling `GET /health`.
- Search screen calling `POST /api/v1/memories/search`.
- Search result cards showing document name, page/chunk badge, similarity score, and content snippet.
- File picker UI for selecting PDF or text files.
- Basic model tests for backend JSON compatibility.

## Run

```bash
cd muzakkir-work/mobile
flutter pub get
flutter run
```

## Backend URLs

- Android emulator: `http://10.0.2.2:8000`
- iOS simulator, desktop, and web: `http://127.0.0.1:8000`

Override if needed:

```bash
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## Current Backend Gap

The mobile app can select a file, but it cannot upload it yet because the backend currently exposes `POST /api/v1/memories/ingest` for metadata plus pre-extracted chunks, not a multipart raw-file upload endpoint.
