"""retrieval_node — Node 4: Semantic policy retrieval via ChromaDB (Phase 3).

Phase 1: Returns empty chunks — the response_node uses the full policy text.
Phase 3: Connects to ChromaDB, returns top-K semantically relevant policy sections.

The RAG_ENABLED env var gates whether ChromaDB is queried.
"""

from app.agent.events import record_trace
from app.agent.graph.state import AgentState
from app.core.config import get_settings


async def retrieval_node(state: AgentState) -> dict:
    """
    Retrieves semantically relevant policy sections for the current query.

    Phase 1 behaviour: RAG_ENABLED=false → returns empty list, no ChromaDB call.
    Phase 3 behaviour: RAG_ENABLED=true → queries ChromaDB with sentence-transformer embeddings.

    IMPORTANT: Retrieved chunks are used ONLY for LLM response composition context.
    They do NOT influence the deterministic policy decision in policy_node.
    """
    db = state["_db"]
    conversation_id = state["conversation_id"]
    settings = get_settings()

    if not settings.rag_enabled:
        # Phase 1: skip retrieval, full policy loaded in tool_node
        return {
            "retrieved_policy_chunks": [],
            "retrieval_scores": [],
            "node_history": state.get("node_history", []) + ["retrieval"],
        }

    # Phase 3: ChromaDB semantic search
    try:
        from app.rag.retriever import retrieve_relevant_policy

        query = state.get("extracted_reason") or state["raw_message"]
        chunks = retrieve_relevant_policy(query)

        await record_trace(
            db,
            conversation_id,
            "rag.retrieve",
            f"Retrieved {len(chunks)} policy chunks"
            + (f" (top score: {chunks[0]['score']:.3f})" if chunks else ""),
            {
                "query_preview": query[:80],
                "chunks": len(chunks),
                "sections": [c["section"] for c in chunks],
            },
        )

        return {
            "retrieved_policy_chunks": [c["text"] for c in chunks],
            "retrieval_scores": [c["score"] for c in chunks],
            "node_history": state.get("node_history", []) + ["retrieval"],
        }

    except Exception as exc:
        await record_trace(
            db, conversation_id, "rag.error",
            "ChromaDB retrieval failed — continuing without RAG context",
            {"error": str(exc)}, "warning",
        )
        return {
            "retrieved_policy_chunks": [],
            "retrieval_scores": [],
            "node_history": state.get("node_history", []) + ["retrieval"],
        }
