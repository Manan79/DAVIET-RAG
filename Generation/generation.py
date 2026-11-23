import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openrouter import ChatOpenRouter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def answer_question(question: str) -> tuple[str, list]:
    """Return an answer and the documents used as context."""
    api_key = os.environ["OPENROUTER_API_KEY"]
    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )
    vectorstore = FAISS.load_local(
        str(PROJECT_ROOT / "vectordb" / "faiss_index"),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    documents = vectorstore.as_retriever(search_kwargs={"k": 4}).invoke(question)
    context = "\n\n".join(doc.page_content for doc in documents)

    llm = ChatOpenRouter(model="openai/gpt-4o-mini", api_key=api_key)
    response = llm.invoke(
        "Answer using only the context below. If the answer isn't there, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    return response.content, documents
