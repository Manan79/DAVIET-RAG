from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Generation.generation import answer_question

st.set_page_config(page_title="Daviet RAG Chatbot", page_icon="💬")
st.title("💬 DAViet RAG Chatbot")
st.caption("Ask questions about DAViet using the indexed website content.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("context"):
            with st.expander("Retrieved context"):
                for index, document in enumerate(message["context"], start=1):
                    st.markdown(f"**Source {index}**")
                    st.write(document.page_content)
                    if document.metadata:
                        st.caption(f"Metadata: {document.metadata}")

question = st.chat_input("Ask a question")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching and generating an answer..."):
            try:
                answer, documents = answer_question(question)
                st.markdown(answer)
                with st.expander("Retrieved context"):
                    for index, document in enumerate(documents, start=1):
                        st.markdown(f"**Source {index}**")
                        st.write(document.page_content)
                        if document.metadata:
                            st.caption(f"Metadata: {document.metadata}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "context": documents}
                )
            except Exception as error:
                st.error(f"Could not generate a response: {error}")
