import os

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Use the same embedding model and key as when the vector store was created.
embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
)

vectorstore = FAISS.load_local(
    "vectordb/faiss_index",
    embeddings,
    allow_dangerous_deserialization=True,  # Only load your own trusted index.
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatOpenRouter(
    model="openai/gpt-4o-mini",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

question = input("Ask a question: ")
documents = retriever.invoke(question)
context = "\n\n".join(doc.page_content for doc in documents)

response = llm.invoke(
    "Answer using only the context below. If the answer isn't there, say you don't know.\n\n"
    f"Context:\n{context}\n\nQuestion: {question}"
)

print(response.content)
