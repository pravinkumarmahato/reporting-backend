import weaviate
import requests
from weaviate.classes.config import Configure, Property, DataType
from pdf_operations import extract_full_pdf_text, chunk_text

import os
from dotenv import load_dotenv

load_dotenv()

WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", "8080"))
WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "PDFChunks")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

def get_embedding(text: str):
    response = requests.post(
        f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/embeddings",
        json={
            "model": OLLAMA_EMBEDDING_MODEL,
            "prompt": text
        }
    )
    response.raise_for_status()
    return response.json()["embedding"]

def store_pdf(pdf_path, client):
    full_text = extract_full_pdf_text(pdf_path)

    if not full_text.strip():
        print("text not extracted from pdf")
        return

    chunks = chunk_text(full_text)

    collection = client.collections.get(COLLECTION_NAME)

    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        collection.data.insert(
            properties={
                "content": chunk,
                "source": pdf_path,
                "chunk_index": idx
            },
            vector=embedding
        )

    print(f"Data Inserted Successfully {len(chunks)} chunks in Weaviate")

def main():
    client = weaviate.connect_to_local(
        host = WEAVIATE_HOST,
        port = WEAVIATE_PORT,
        grpc_port = WEAVIATE_GRPC_PORT
    )

    try:
        if not client.collections.exists(COLLECTION_NAME):
            client.collections.create(
                name=COLLECTION_NAME,
                vector_config=Configure.VectorIndex.none(),
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="chunk_index", data_type=DataType.INT)
                ]
            )
        
        store_pdf("files/bank_financials.pdf", client)

    finally:
        client.close()

if __name__ == "__main__":
    main()
