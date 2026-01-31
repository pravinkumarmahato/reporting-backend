import weaviate
from weaviate.classes.query import MetadataQuery
from weaviate_store_data import get_embedding

WEAVIATE_HOST = "localhost"
WEAVIATE_PORT = 8080
WEAVIATE_GRPC_PORT = 50051
COLLECTION_NAME = "PDFChunks"
DEFAULT_LIMIT = 5


def get_weaviate_client():
    """Return a connected Weaviate client."""
    return weaviate.connect_to_local(
        host=WEAVIATE_HOST,
        port=WEAVIATE_PORT,
        grpc_port=WEAVIATE_GRPC_PORT,
    )


def search_pdf_chunks(query: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    if not query or not query.strip():
        return []

    query = query.strip()
    embedding = get_embedding(query)

    try:
        client = get_weaviate_client()
        try:
            collection = client.collections.get(COLLECTION_NAME)
            response = collection.query.near_vector(
                near_vector=embedding,
                limit=limit,
                return_metadata=MetadataQuery(distance=True),
            )
            results = []
            for obj in response.objects:
                props = obj.properties
                metadata = getattr(obj, "metadata", None)
                score = None
                if metadata and hasattr(metadata, "distance") and metadata.distance is not None:
                    # For cosine: distance 0 = identical, 2 = opposite; convert to 0-1 score
                    score = max(0, 1.0 - (metadata.distance / 2.0))
                results.append({
                    "content": props.get("content", ""),
                    "source": props.get("source", ""),
                    "chunk_index": props.get("chunk_index"),
                    "score": score,
                })
            return results
        finally:
            client.close()
    except Exception as e:
        raise RuntimeError(f"Weaviate search failed: {e}") from e
