from pathlib import Path
import sys

# Add the repository root so sibling packages work when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openai import OpenAI
from Ingestion.chunking_docs import chunk_docs
from langchain_openai import OpenAIEmbeddings
import faiss
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os
load_dotenv() 



embeddings_model = "openai/text-embedding-3-small"

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
)
# model = ChatOpenRouter(model = "gpt-4o-mini")

def create_vectorstore():
    # Load the chunked documents
    chunked_documents = chunk_docs()

    # Create a FAISS vector store from the chunked documents
    vectorstore = FAISS.from_documents(chunked_documents, embeddings)

    # Save the vector store to disk
    vectorstore.save_local("vectordb/faiss_index")
    print("Vector store created and saved to 'vectordb/faiss_index'.")


if __name__ == "__main__":
    create_vectorstore()