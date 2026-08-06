from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams
from core.config import settings

client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

async def init_qdrant():
    """Initializes the Qdrant collection if it doesn't exist."""
    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if settings.COLLECTION_NAME not in collection_names:
        print(f"Creating collection '{settings.COLLECTION_NAME}'...")
        await client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print(f"Collection '{settings.COLLECTION_NAME}' created.")
    else:
        print(f"Collection '{settings.COLLECTION_NAME}' already exists.")

async def search_documents(query_vector: list[float], limit: int = 3) -> list[str]:
    """Searches Qdrant for similar documents given a query vector."""
    try:
        search_result = await client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit
        )
        
        # Assuming the payload has a 'text' field containing the document content
        contexts = [hit.payload.get("text", "") for hit in search_result if hit.payload]
        return contexts
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return []
