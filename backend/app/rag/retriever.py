"""
Phase 3 — RAG Pipeline: ChromaDB retriever for Andromeda refund policy.

Splits the policy document into semantic chunks (one per heading section),
embeds them with sentence-transformers (all-MiniLM-L6-v2, runs locally,
no API key required), stores in ChromaDB, and retrieves the top-K most
relevant chunks for any incoming query.

ChromaDB runs in-process for development (persistent mode) and as a
separate container in production (see docker-compose.yml Phase 3 extension).
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
except ImportError:
    chromadb = None
    ChromaSettings = None
    SentenceTransformer = None
    ML_AVAILABLE = False

from app.core.config import get_settings

# ── Module-level singletons (initialised once per process) ───────────────
_client: chromadb.Client | None = None
_collection: chromadb.Collection | None = None
_embedder: SentenceTransformer | None = None

COLLECTION_NAME = "andromeda_refund_policy"
MODEL_NAME = "all-MiniLM-L6-v2"  # 22MB, fully local, no API key


class PolicyChunk(TypedDict):
    text: str
    section: str
    score: float


# ── Initialisation ────────────────────────────────────────────────────────

def _get_embedder():
    global _embedder
    if not ML_AVAILABLE:
        return None
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def _get_client() -> chromadb.Client:
    global _client
    if _client is None:
        settings = get_settings()
        if settings.chroma_host == "localhost" and settings.chroma_port == 8001:
            # Persistent local mode (development)
            persist_dir = Path(__file__).resolve().parents[2] / "data" / "chroma"
            persist_dir.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(persist_dir))
        else:
            # Remote ChromaDB server (production docker)
            _client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
    return _client


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ── Indexing ──────────────────────────────────────────────────────────────

def _split_policy_into_chunks(policy_text: str) -> list[dict]:
    """Split markdown policy by ## headings into semantic chunks."""
    chunks = []
    current_section = "Introduction"
    current_lines: list[str] = []

    for line in policy_text.splitlines():
        if line.startswith("## "):
            # Save previous section
            if current_lines:
                text = "\n".join(current_lines).strip()
                if text:
                    chunks.append({"section": current_section, "text": text})
            current_section = line.lstrip("# ").strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({"section": current_section, "text": text})

    return chunks


def index_policy(force: bool = False) -> int:
    """
    Index the Andromeda refund policy into ChromaDB.

    Args:
        force: If True, clears and rebuilds the collection.

    Returns:
        Number of chunks indexed.
    """
    if not ML_AVAILABLE:
        return 0

    collection = _get_collection()

    if not force and collection.count() > 0:
        return collection.count()

    settings = get_settings()
    policy_text = Path(settings.policy_path).read_text(encoding="utf-8")
    chunks = _split_policy_into_chunks(policy_text)

    embedder = _get_embedder()
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, convert_to_numpy=True).tolist()

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"section": c["section"]} for c in chunks]

    if force:
        _get_client().delete_collection(COLLECTION_NAME)
        collection = _get_client().create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(chunks)


# ── Retrieval ─────────────────────────────────────────────────────────────

def retrieve_relevant_policy(query: str) -> list[PolicyChunk]:
    """
    Retrieve the top-K most relevant policy sections for a query.

    Args:
        query: The user's refund request or extracted reason text.

    Returns:
        List of PolicyChunk dicts sorted by relevance (highest first),
        filtered to those above settings.rag_score_threshold.
    """
    if not ML_AVAILABLE:
        return []

    settings = get_settings()
    collection = _get_collection()

    # Ensure indexed
    if collection.count() == 0:
        index_policy()

    embedder = _get_embedder()
    query_embedding = embedder.encode([query], convert_to_numpy=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=settings.rag_top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[PolicyChunk] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB cosine distance → similarity score (1 - distance)
        score = float(1.0 - dist)
        if score >= settings.rag_score_threshold:
            chunks.append(PolicyChunk(
                text=doc,
                section=meta.get("section", "unknown"),
                score=score,
            ))

    return sorted(chunks, key=lambda c: c["score"], reverse=True)
