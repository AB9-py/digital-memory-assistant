# Muzakkir (Syed) Work — Mobile UI & Client Integration

This folder contains Syed Muzakkir's allotted deliverables for the **Digital Memory Assistant 2nd Review (20% Implementation Milestone)**.

---

## Deliverables & Features

- **Flutter Client Architecture:** Built with `flutter_riverpod` state management and `dio` HTTP client.
- **Screen 1 (System Health & Connection):**
  - Probes `GET /health` with millisecond latency tracking.
  - Prominent visual status badges:
    - 🟢 `Backend & DB Connected` (FastAPI + pgvector fully operational)
    - 🟡 `Backend Connected (DB Disconnected)` (FastAPI alive, PostgreSQL container offline)
    - 🔴 `Backend Disconnected` (Network error / server offline)
  - Live server metadata (API Version, Environment, Target URL).
- **Screen 2 (Semantic Memory Retrieval & Ingestion):**
  - **Document Selection & Upload:** Integrated `file_picker` for `.pdf` and `.txt` files with file details (size, format) and an explicit **"Upload to Memory"** button and validation status sheet.
  - **Preset Query Chips:** Quick-select chips for review demonstration (`"What is Banker's algorithm?"`, `"What did I learn about deadlock prevention?"`, `"How does Dijkstra's algorithm work?"`).
  - **pgvector Cosine Similarity Match Cards:** Renders retrieved chunks with document title, page number / chunk index badge, exact decimal score (`0.3020`), match percentage (`30%`), and quoted snippet.
  - **Grounding & Negative Filter:** Displays zero false-positive indicator when queries fall below similarity threshold.
- **Testing Suite:** Comprehensive unit tests in `test/models_test.dart` validating `HealthStatus`, `SearchRequest`, and `SearchResponse` edge cases and JSON schemas.
- **Review Presentation Guide:** See [REVIEW_PRESENTATION_GUIDE.md](file:///s:/GIT/digital-memory-assistant/muzakkir-work/REVIEW_PRESENTATION_GUIDE.md) for Syed's 60-second live demo speaking script and answers to evaluator questions.

---

## How to Run

```bash
cd muzakkir-work/mobile
flutter pub get
flutter run
```

### Backend Connection Details

- **Desktop (Windows/macOS), iOS Simulator, Web:** `http://127.0.0.1:8000`
- **Android Emulator:** `http://10.0.2.2:8000` (auto-detected)
- **Custom Override:**
  ```bash
  flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
  ```

---

## Live Backup

During review evaluation, the OpenAPI interactive Swagger documentation is available in any browser at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

