import weaviate
import requests
from weaviate.classes.config import Configure, Property, DataType
from pdf_operations import extract_full_pdf_text, chunk_text

def get_embedding(text: str):
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
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

    collection = client.collections.get("PDFChunks")

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
        host="localhost",
        port=8080,
        grpc_port=50051
    )

    try:
        if not client.collections.exists("PDFChunks"):
            client.collections.create(
                name="PDFChunks",
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
