from pypdf import PdfReader


def extract_full_pdf_text(file_path):
    reader = PdfReader(file_path)
    parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)

    return "\n\n".join(parts) if parts else ""


def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # overlap

    return chunks
