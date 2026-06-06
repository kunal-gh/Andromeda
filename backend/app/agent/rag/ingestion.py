"""Document ingestion pipeline for RAG."""
from pathlib import Path
from app.agent.rag.vector_store import ingest_documents

def ingest_refund_policy():
    policy_path = Path("app/data/arcashop_refund_policy.md")
    if not policy_path.exists():
        return 0
    try:
        from langchain.schema import Document
        with open(policy_path, "r", encoding="utf-8") as f:
            content = f.read()
        doc = Document(page_content=content, metadata={"source": "arcashop_refund_policy.md", "type": "policy"})
        return ingest_documents([doc])
    except ImportError:
        return 0

def ingest_faq_documents():
    try:
        from langchain.schema import Document
        faq_docs = [
            Document(page_content="How do I wash my ArcaShop jacket?\nMachine wash cold with like colors. Tumble dry low. Do not bleach.\nOur jackets are pre-shrunk but may tighten slightly after first wash.", metadata={"source": "faq_washing.md", "type": "faq", "category": "care"}),
            Document(page_content="What is your shipping policy?\nStandard shipping: 5-7 business days, free over $50.\nExpress shipping: 2-3 business days, $12.99.\nInternational: 10-15 business days, calculated at checkout.", metadata={"source": "faq_shipping.md", "type": "faq", "category": "shipping"}),
            Document(page_content="How do I find my size?\nRefer to our size chart at arcashop.com/sizing.\nOur apparel runs true to size. If between sizes, we recommend sizing up.", metadata={"source": "faq_sizing.md", "type": "faq", "category": "product"}),
            Document(page_content="Can I exchange an item instead of returning it?\nYes! Exchanges follow the same eligibility rules as returns.\nInitiate an exchange through your order history page.", metadata={"source": "faq_exchange.md", "type": "faq", "category": "policy"}),
        ]
        return ingest_documents(faq_docs)
    except ImportError:
        return 0

def run_full_ingestion():
    total = 0
    total += ingest_refund_policy()
    total += ingest_faq_documents()
    print(f"Ingested {total} document chunks into Qdrant")
    return total
