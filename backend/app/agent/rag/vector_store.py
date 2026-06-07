"""Qdrant vector store setup and document ingestion."""
import logging

logger = logging.getLogger(__name__)

# Lazy initialization
_qdrant_client = None
_embeddings = None
COLLECTION_NAME = "andromeda_knowledge"

def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(host="localhost", port=6333) # Hardcoded for now
        except ImportError:
            logger.warning("qdrant-client not installed.")
            return None
    return _qdrant_client

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_openai import OpenAIEmbeddings
            _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        except ImportError:
            pass
    return _embeddings

def init_qdrant_collection():
    client = get_qdrant_client()
    if not client:
        return
    
    from qdrant_client.models import Distance, VectorParams
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

def get_vector_store():
    client = get_qdrant_client()
    embeddings = get_embeddings()
    if not client or not embeddings:
        return None
        
    init_qdrant_collection()
    from langchain_qdrant import QdrantVectorStore
    return QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embeddings)

def ingest_documents(documents: list):
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ". ", " ", ""])
        chunks = text_splitter.split_documents(documents)
        vector_store = get_vector_store()
        if vector_store:
            vector_store.add_documents(chunks)
            return len(chunks)
    except ImportError:
        logger.warning("Failed to import langchain for ingestion.")
    return 0
