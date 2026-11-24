import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openrouter import ChatOpenRouter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
message_history = []

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
    documents = vectorstore.as_retriever(search_kwargs={"k": 3}).invoke(question)

    if len(message_history) > 4:
        recent_messages = message_history[-3:]
    else:
        recent_messages = message_history

    context = "\n\n".join(doc.page_content for doc in documents)
    history_str = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in recent_messages)

    llm = ChatOpenRouter(model="openai/gpt-4o-mini", api_key=api_key)
    prompt = (
        "Answer using only the context and conversation history. If the context and conversation history do not provide enough information, say 'I don't know.'\n\n"
        "DAVIET full form is DAV Institute of Engineering and Technology.\n\n"
        f"Conversation History:\n{history_str}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    response = llm.invoke(prompt)

    message_history.append({"role": "user", "content": question})
    message_history.append({"role": "assistant", "content": response.content})
    return response.content, documents
