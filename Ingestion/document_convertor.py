
from pathlib import Path
# from langchain_core.document_loaders import TextLoader
from langchain_core.documents import Document
import json

documents = []

RAW_DIR = Path("data/raw")

for file_path in RAW_DIR.glob("*.txt"):
    content = file_path.read_text(encoding="utf-8")

    # Extract metadata from the first few lines
    lines = content.splitlines()
    url_line = next((line for line in lines if line.startswith("URL: ")), None)
    title_line = next((line for line in lines if line.startswith("TITLE: ")), None)
    description_line = next((line for line in lines if line.startswith("DESCRIPTION: ")), None)

    url = url_line[5:].strip() if url_line else ""
    title = title_line[7:].strip() if title_line else ""
    description = description_line[12:].strip() if description_line else ""

    # Remove metadata lines from the content
    content_without_metadata = "\n".join(line for line in lines if not (line.startswith("URL: ") or line.startswith("TITLE: ") or line.startswith("DESCRIPTION: ")))

    # Create a Document object with the content and metadata
    print(f"Processing file: {file_path.name}")
    document = Document(
        page_content=content_without_metadata,
        metadata={
            "source": str(file_path),
            "url": url,
            "title": title,
            "description": description
        }
    )
    documents.append(document)

# Save all documents to a single JSON file
with open("Ingestion/processed_documents.json", "w", encoding="utf-8") as f:
    json.dump([doc.model_dump() for doc in documents], f, indent=4, ensure_ascii=False)
