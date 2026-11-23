from langchain_core.documents import Document
from pathlib import Path
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter


splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=80,
)


data_path = Path(__file__).resolve().with_name("processed_documents.json")
with data_path.open("r", encoding="utf-8") as file:
    data = json.load(file)
# print(data)


def chunk_docs():
    # Split the documents into chunks
    chunked_documents = []
    for doc in data:
        document = Document(
            page_content=doc["page_content"],
            metadata=doc["metadata"]
        )
        chunks = splitter.split_documents([document])
        chunked_documents.extend(chunks)


    return chunked_documents