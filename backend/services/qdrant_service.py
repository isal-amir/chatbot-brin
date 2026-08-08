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

import uuid
from qdrant_client.http.models import PointStruct

async def add_documents_to_qdrant(chunks: list[str], embeddings: list[list[float]], doc_id: int, title: str):
    """Adds document chunks and their embeddings to Qdrant."""
    try:
        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "text": chunk,
                        "document_id": doc_id,
                        "title": title,
                        "chunk_index": i
                    }
                )
            )
            
        if points:
            await client.upsert(
                collection_name=settings.COLLECTION_NAME,
                points=points
            )
            print(f"Added {len(points)} chunks for document '{title}' to Qdrant.")
    except Exception as e:
        print(f"Error adding to Qdrant: {e}")
        raise

from qdrant_client.http.models import Filter, FieldCondition, MatchValue

async def delete_document_from_qdrant(doc_id: int):
    """Deletes all chunks of a document from Qdrant by document_id."""
    try:
        await client.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
        )
        print(f"Deleted document {doc_id} from Qdrant.")
    except Exception as e:
        print(f"Error deleting from Qdrant: {e}")
        raise
