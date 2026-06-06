"""Hybrid RAG query combining vector search and knowledge graph."""
from app.agent.rag.vector_store import get_vector_store
from app.agent.rag.knowledge_graph import get_knowledge_graph

async def hybrid_query(question: str, customer_email: str | None = None) -> dict:
    vector_store = get_vector_store()
    vector_results = []
    if vector_store:
        try:
            vector_results = vector_store.similarity_search(question, k=3)
        except Exception:
            pass
            
    kg = get_knowledge_graph()
    kg_context = []
    
    if customer_email:
        customers = kg.query_subgraph(entity_type="customer", email=customer_email)
        if customers:
            customer_id = customers[0]["id"]
            orders = kg.get_related_entities(customer_id, "purchased")
            kg_context.append(f"Customer has {len(orders)} orders: {', '.join([o['item'] for o in orders])}")
            
    vector_context = "\n\n".join([doc.page_content for doc in vector_results])
    kg_context_text = "\n".join(kg_context) if kg_context else ""
    
    return {
        "vector_results": vector_results, 
        "kg_context": kg_context, 
        "combined_context": f"{kg_context_text}\n\n{vector_context}"
    }
