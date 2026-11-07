# Muzakkir (Syed) Work — Mobile UI & Client Integration

This folder contains Syed Muzakkir's completed client deliverables for the **Digital Memory Assistant**.

---

## Deliverables & Architecture

- **Flutter Client Architecture:** Built with `flutter_riverpod` state management and `dio` HTTP client.
- **Screen 1 (System Health & Server Configuration):**
  - Probes `GET /health` with real-time millisecond roundtrip latency tracking.
  - Interactive **Server Configuration Dialog** allowing seamless switching between presets:
    - Localhost (`http://127.0.0.1:8000`)
    - Android Emulator (`http://10.0.2.2:8000`)
    - Custom LAN / Wi-Fi IP address
  - Prominent visual status banners:
    - 🟢 `Backend & DB Connected` (FastAPI + pgvector fully operational)
    - 🟡 `Backend Connected (DB Disconnected)` (FastAPI alive, PostgreSQL container offline)
    - 🔴 `Backend Disconnected` (Network error / server offline with diagnostic hints)
  - Live server metadata (API Version, Environment, Target URL).
- **Screen 2 (Semantic Memory Retrieval & Document Ingestion):**
  - **Multi-Format Document Upload:** Integrated file picker supporting `.pdf`, `.docx`, `.txt`, `.png`, `.jpg`, `.jpeg` with safe fallback for both filesystem paths and raw memory bytes.
  - **Live Multipart Upload:** Directly sends documents to `POST /api/v1/memories/upload`, extracting chunks and embedding into pgvector in real time.
  - **Preset Query Chips:** Quick-select chips for demonstration (`"What is Banker's algorithm?"`, `"What did I learn about deadlock prevention?"`, `"How does Dijkstra's algorithm work in link state routing?"`).
  - **pgvector Cosine Similarity Match Cards:** Renders retrieved chunks with document title, page number / chunk index badge, exact decimal score (`0.3020`), match percentage (`30%`), and styled quoted content.
  - **Grounding & Zero False-Positive Handling:** Clean notification when no chunks exceed the similarity threshold.
- **Screen 3 (Stored Documents & Memory Management):**
  - Dedicated **Memories** screen connecting to `GET /api/v1/memories`.
  - Displays document cards with file format badges (PDF, DOCX, TXT, IMAGE), size, processing status, and upload dates.
  - Document deletion with confirmation dialog via `DELETE /api/v1/memories/{id}`.
  - Pull-to-refresh and empty-state guidance.
- **Testing Suite:** Comprehensive unit tests in `test/models_test.dart` validating `HealthStatus`, `SearchRequest`, `SearchResponse`, `MemoryItem`, and `MemoryListResponse` edge cases.
- **Multi-Platform Support:** Ready-to-run platform wrappers for Web (`web/`) and Android (`android/`).

---

## How to Run

```bash
cd muzakkir-work/mobile
flutter pub get
flutter run
```

### Target Platforms

- **Chrome / Web:** `flutter run -d chrome`
- **Android Emulator:** `flutter run -d emulator` (auto-detects `10.0.2.2:8000`)
- **Windows Desktop:** `flutter run -d windows`
- **Custom Backend URL:** Set dynamically in the app's Health screen or pass via command-line:
  ```bash
  flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
  ```

---

## Live Backup & Review Resources

- **Review Presentation Guide:** [REVIEW_PRESENTATION_GUIDE.md](file:///s:/GIT/digital-memory-assistant/muzakkir-work/REVIEW_PRESENTATION_GUIDE.md) (60-second live demo script + evaluator Q&A answers).
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
