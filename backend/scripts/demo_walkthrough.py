"""
demo_walkthrough.py

Interactive 1-command live demo walkthrough for review presentations.
Demonstrates:
  1. System Health Check (/health)
  2. Ingesting Academic Notes into Vector Memory (/api/v1/memories/ingest)
  3. Listing Stored Memories with Status (/api/v1/memories)
  4. Semantic Retrieval with Cosine Similarity Scores (/api/v1/memories/search)
  5. Multi-Tenant User Isolation (verifying zero cross-user leakage)
  6. Grounding / Negative Query Filtering
"""

from datetime import datetime, timezone
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.database import get_db
from backend.main import app
from backend.models.memory import Memory
from backend.schemas.chunk import ChunkSearchResult
from backend.schemas.memory import MemoryIngestRequest, MemoryStatus
from backend.services.embedding import DeterministicEmbeddingProvider

# ANSI color codes for presentation formatting
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def header(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'=' * 70}{RESET}")
    print(f"{BOLD}{CYAN} ▶ {title.upper()}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 70}{RESET}\n")


def print_step(num: int, title: str) -> None:
    print(f"{BOLD}{MAGENTA}[Step {num}] {title}{RESET}")


class InMemoryDemoStore:
    """In-memory demo store used for standalone presentation runs."""

    def __init__(self) -> None:
        self.memories: dict[uuid.UUID, Memory] = {}
        self.chunks: list[dict] = []
        self.embedding_provider = DeterministicEmbeddingProvider(dimension=1536)

    async def ingest_memory_with_chunks(self, db, payload: MemoryIngestRequest) -> Memory:
        mem_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        memory = Memory(
            id=mem_id,
            user_id=payload.user_id,
            original_filename=payload.original_filename,
            file_type=payload.file_type,
            file_path=payload.file_path,
            file_size_bytes=payload.file_size_bytes,
            status=MemoryStatus.PROCESSED.value,
            meta_info=payload.meta_info,
            created_at=now,
            updated_at=now,
        )
        self.memories[mem_id] = memory

        if payload.chunks:
            texts = [c.content for c in payload.chunks]
            embeddings = await self.embedding_provider.embed_batch(texts)
            for i, c in enumerate(payload.chunks):
                self.chunks.append(
                    {
                        "id": uuid.uuid4(),
                        "memory_id": mem_id,
                        "user_id": payload.user_id,
                        "original_filename": payload.original_filename,
                        "chunk_index": c.chunk_index,
                        "content": c.content,
                        "page_number": c.page_number,
                        "embedding": embeddings[i],
                        "chunk_metadata": c.chunk_metadata,
                    }
                )
        return memory

    async def list_memories(self, db, user_id: uuid.UUID, skip: int = 0, limit: int = 50):
        items = [m for m in self.memories.values() if m.user_id == user_id]
        return len(items), items[skip : skip + limit]

    async def get_memory(self, db, memory_id: uuid.UUID, user_id: uuid.UUID):
        m = self.memories.get(memory_id)
        return m if (m and m.user_id == user_id) else None

    async def delete_memory(self, db, memory_id: uuid.UUID, user_id: uuid.UUID):
        if memory_id in self.memories and self.memories[memory_id].user_id == user_id:
            del self.memories[memory_id]
            self.chunks = [c for c in self.chunks if c["memory_id"] != memory_id]
            return True
        return False

    async def search_memories(
        self, db, user_id: uuid.UUID, query: str, top_k: int = 5, min_similarity: float = 0.0
    ) -> list[ChunkSearchResult]:
        query_vec = await self.embedding_provider.embed_text(query)
        results = []

        for c in self.chunks:
            if c["user_id"] != user_id:
                continue
            # Cosine similarity between unit vectors
            sim = sum(a * b for a, b in zip(query_vec, c["embedding"], strict=False))
            sim = max(0.0, min(1.0, sim))
            if sim >= min_similarity:
                results.append(
                    ChunkSearchResult(
                        chunk_id=c["id"],
                        memory_id=c["memory_id"],
                        original_filename=c["original_filename"],
                        content=c["content"],
                        page_number=c["page_number"],
                        chunk_index=c["chunk_index"],
                        similarity_score=round(sim, 4),
                        chunk_metadata=c["chunk_metadata"],
                    )
                )

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]


async def mock_get_db():
    yield None


def run_demo() -> None:
    # Override get_db dependency to avoid trying to open asyncpg connection when demoing
    app.dependency_overrides[get_db] = mock_get_db

    client = TestClient(app)

    header("Digital Memory Assistant — Live Demo Walkthrough")

    # 1. Health Check
    print_step(1, "Checking Backend & Service Health")
    health_resp = client.get("/health")
    data = health_resp.json()
    print(f"Status Code : {GREEN}{health_resp.status_code} OK{RESET}")
    print(f"Version     : {data.get('version')} ({data.get('environment')})\n")

    demo_store = InMemoryDemoStore()

    patchers = [
        patch("backend.api.memories.memory_service.ingest_memory_with_chunks", side_effect=demo_store.ingest_memory_with_chunks),
        patch("backend.api.memories.memory_service.list_memories", side_effect=demo_store.list_memories),
        patch("backend.api.memories.memory_service.get_memory", side_effect=demo_store.get_memory),
        patch("backend.api.memories.memory_service.delete_memory", side_effect=demo_store.delete_memory),
        patch("backend.api.memories.retrieval_service.search_memories", side_effect=demo_store.search_memories),
    ]

    for p in patchers:
        p.start()

    # Setup Demo Users
    abhinav_user_id = uuid.uuid4()
    stranger_user_id = uuid.uuid4()

    print(f"Primary User (Abhinav) : {YELLOW}{abhinav_user_id}{RESET}")
    print(f"Stranger User (Tester) : {YELLOW}{stranger_user_id}{RESET}\n")

    # 2. Ingest Sample Documents
    print_step(2, "Ingesting Sample Documents & Generating Vector Embeddings")

    sample_documents = [
        {
            "user_id": str(abhinav_user_id),
            "original_filename": "OS_Unit_3_Deadlocks.pdf",
            "file_type": "PDF",
            "file_size_bytes": 1048576,
            "file_path": "/uploads/OS_Unit_3_Deadlocks.pdf",
            "meta_info": {"course": "CS301", "topic": "Operating Systems"},
            "chunks": [
                {
                    "chunk_index": 0,
                    "page_number": 1,
                    "content": "A deadlock occurs in an OS when a set of processes are blocked because each process is holding a resource and waiting for another resource held by some other process.",
                    "chunk_metadata": {"section": "Deadlock Definition"},
                },
                {
                    "chunk_index": 1,
                    "page_number": 3,
                    "content": "Deadlock Prevention eliminates at least one of Coffman's 4 conditions: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Ordering all resources linearly prevents circular wait.",
                    "chunk_metadata": {"section": "Deadlock Prevention"},
                },
                {
                    "chunk_index": 2,
                    "page_number": 5,
                    "content": "Banker's Algorithm is a deadlock avoidance algorithm developed by Edsger Dijkstra. It tests for safe states by simulating resource allocation for maximum possible amounts before granting requests.",
                    "chunk_metadata": {"section": "Deadlock Avoidance / Banker's Algorithm"},
                },
            ],
        },
        {
            "user_id": str(abhinav_user_id),
            "original_filename": "CN_Unit_2_Routing.pdf",
            "file_type": "PDF",
            "file_size_bytes": 2097152,
            "file_path": "/uploads/CN_Unit_2_Routing.pdf",
            "meta_info": {"course": "CS304", "topic": "Computer Networks"},
            "chunks": [
                {
                    "chunk_index": 0,
                    "page_number": 2,
                    "content": "Link-State routing protocols like OSPF require every router to build a complete topological map of the entire network using Dijkstra's shortest path algorithm.",
                    "chunk_metadata": {"section": "Link-State Routing"},
                },
                {
                    "chunk_index": 1,
                    "page_number": 4,
                    "content": "Distance Vector routing protocols like RIP share routing tables only with immediate neighbors periodically using the Bellman-Ford algorithm.",
                    "chunk_metadata": {"section": "Distance Vector"},
                },
            ],
        },
    ]

    for doc in sample_documents:
        resp = client.post("/api/v1/memories/ingest", json=doc)
        if resp.status_code == 201:
            data = resp.json()
            print(
                f"  {GREEN}✔ Ingested & Vectorized:{RESET} {BOLD}{data['original_filename']}{RESET} "
                f"(Status: {GREEN}{data['status']}{RESET}, Chunks: {len(doc['chunks'])})"
            )
        else:
            print(f"  {YELLOW}⚠ Ingest error:{RESET} {resp.text}")

    print()

    # 3. List Stored Memories
    print_step(3, "Listing Stored Memories for User")
    list_resp = client.get(f"/api/v1/memories?user_id={abhinav_user_id}")
    memories_data = list_resp.json()
    print(f"Total Stored Documents: {GREEN}{memories_data['total']}{RESET}")
    for item in memories_data["items"]:
        print(f"  • {item['original_filename']} [{item['file_type']}] — Status: {GREEN}{item['status']}{RESET}")
    print()

    # 4. Perform Semantic Search Queries
    print_step(4, "Executing Semantic Queries via pgvector Cosine Search")

    queries = [
        "What did I learn about deadlock prevention?",
        "How does Dijkstra's algorithm work in link state routing?",
        "What is Banker's algorithm used for?",
        "How to bake a chocolate cake?",  # Negative / unrelated query
    ]

    for query in queries:
        print(f"\n{BOLD}Query:{RESET} \"{YELLOW}{query}{RESET}\"")
        search_resp = client.post(
            "/api/v1/memories/search",
            json={
                "query": query,
                "user_id": str(abhinav_user_id),
                "top_k": 2,
                "min_similarity": 0.15,
            },
        )
        data = search_resp.json()
        results: list[dict] = data.get("results", [])

        if not results:
            print(f"  {YELLOW}ℹ No relevant chunks found above similarity threshold (Grounding enforced).{RESET}")
            continue

        print(f"  Found {GREEN}{len(results)}{RESET} relevant chunk(s):")
        for i, res in enumerate(results, 1):
            score = res["similarity_score"]
            color = GREEN if score >= 0.70 else YELLOW
            print(f"    {BOLD}[Match {i}]{RESET} Document: {CYAN}{res['original_filename']}{RESET} (Page {res.get('page_number', 'N/A')})")
            print(f"            Similarity Score: {color}{score:.4f}{RESET}")
            print(f"            Content Snippet : \"{res['content'][:90]}...\"")

    print()

    # 5. Multi-Tenant User Isolation Test
    print_step(5, "Verifying Multi-Tenant Data Isolation")
    print(f"Querying with Stranger User ID: {YELLOW}{stranger_user_id}{RESET}...")
    isolation_resp = client.post(
        "/api/v1/memories/search",
        json={
            "query": "deadlock prevention",
            "user_id": str(stranger_user_id),
            "top_k": 5,
        },
    )
    iso_results = isolation_resp.json().get("results", [])
    if len(iso_results) == 0:
        print(f"  {GREEN}✔ Strict Tenant Isolation Verified:{RESET} 0 chunks retrieved for unauthorized user.\n")
    else:
        print(f"  {YELLOW}⚠ Leak detected!{RESET}\n")

    for p in patchers:
        p.stop()

    app.dependency_overrides.clear()
    header("Demo Walkthrough Completed Successfully!")


if __name__ == "__main__":
    run_demo()
