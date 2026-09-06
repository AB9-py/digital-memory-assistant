# Digital Memory Assistant Mobile

Flutter client for the FastAPI backend.

## Local Setup

```bash
cd muzakkir-work/mobile
flutter pub get
flutter run
```

The default Android emulator API base URL is `http://10.0.2.2:8000`.
For iOS simulator, macOS, Windows, Linux, or web, the app uses `http://127.0.0.1:8000`.

You can override the base URL:

```bash
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## Current Demo Scope

- Health screen calls `GET /health`.
- Search screen calls `POST /api/v1/memories/search`.
- File picker is present for the upload flow, but upload is not submitted because the backend does not yet expose a multipart file upload endpoint.
