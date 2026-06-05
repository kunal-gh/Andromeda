"""
Phase 3 — RAG package.
Lazy exports — chromadb only imported when RAG_ENABLED=true.
"""


def index_policy(force: bool = False) -> int:
    from app.rag.retriever import index_policy as _index
    return _index(force=force)


def retrieve_relevant_policy(query: str) -> list:
    from app.rag.retriever import retrieve_relevant_policy as _retrieve
    return _retrieve(query)


__all__ = ["index_policy", "retrieve_relevant_policy"]
