"""Streamlit UI. Run with: doctalk ui"""
import tempfile
from pathlib import Path

import streamlit as st

from doctalk.rag import cited_numbers, stream_answer
from doctalk.store import Store

st.set_page_config(page_title="DocTalk", page_icon="📚")
st.title("📚 DocTalk")
st.caption("Chat with your documents. Every answer cites its sources.")


@st.cache_resource
def get_store() -> Store:
    return Store(".chroma")


store = get_store()

with st.sidebar:
    st.header("Documents")
    uploads = st.file_uploader(
        "Add files", type=["pdf", "md", "txt"], accept_multiple_files=True
    )
    if uploads and st.button("Index uploads"):
        with tempfile.TemporaryDirectory() as tmp:
            for up in uploads:
                (Path(tmp) / up.name).write_bytes(up.getvalue())
            counts = store.ingest(tmp)
        st.success(f"Indexed {len(counts)} file(s), {sum(counts.values())} chunks")
    for s in store.sources():
        st.write(f"• {s}")
    k = st.slider("Passages to retrieve", 1, 10, 5)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for label, text in m.get("sources", []):
            with st.expander(label):
                st.write(text)

if q := st.chat_input("Ask about your documents"):
    if store.count() == 0:
        st.warning("Index some documents first (sidebar).")
        st.stop()
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        hits, tokens = stream_answer(q, store, k=k)
        text = st.write_stream(tokens)
        used = cited_numbers(text, len(hits))
        sources = [(f"[{i}] {hits[i-1].label}", hits[i - 1].text) for i in used]
        for label, body in sources:
            with st.expander(label):
                st.write(body)
    st.session_state.messages.append(
        {"role": "assistant", "content": text, "sources": sources}
    )
