import streamlit as st
import tempfile
import os
import time
from pathlib import Path

# ── Page config (must be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="DocMind · AI Document Q&A",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

/* ── Root & Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e2e2e8;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar toggle button (reopen button) ── */
[data-testid="collapsedControl"] {
    background: #0f0f18 !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 0 8px 8px 0 !important;
    color: #a78bfa !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="collapsedControl"] svg {
    fill: #a78bfa !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0f0f18 !important;
    border-right: 1px solid #1e1e2e;
}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {
    color: #9090a8 !important;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Logo / Brand ── */
.brand {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}

.brand-sub {
    font-size: 0.7rem;
    color: #4a4a6a;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 24px;
}

/* ── Section headers ── */
.section-label {
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a4a6a;
    margin: 20px 0 8px 0;
    display: flex;
    align-items: center;
    gap: 6px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e1e2e;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #12121e !important;
    border: 1px dashed #2a2a3e !important;
    border-radius: 12px !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #a78bfa !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.03em !important;
    padding: 10px 20px !important;
    width: 100% !important;
    transition: opacity 0.2s, transform 0.1s !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Main header area ── */
.hero {
    text-align: center;
    padding: 48px 0 32px 0;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2.8rem;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    margin-bottom: 10px;
}
.hero p {
    color: #5a5a7a;
    font-size: 1.0rem;
    font-weight: 300;
    letter-spacing: 0.01em;
}

/* ── Status pills ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.05em;
}
.status-ready {
    background: #0d2918;
    color: #34d399;
    border: 1px solid #1a4a30;
}
.status-idle {
    background: #1a1a2e;
    color: #6060a0;
    border: 1px solid #2a2a4a;
}

/* ── Chat messages ── */
.chat-user {
    background: #15152a;
    border: 1px solid #2a2a45;
    border-radius: 14px 14px 4px 14px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #c8c8e0;
    font-size: 0.92rem;
    line-height: 1.6;
}
.chat-assistant {
    background: #0e1f1a;
    border: 1px solid #1a3a2e;
    border-radius: 14px 14px 14px 4px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #a8d8c8;
    font-size: 0.92rem;
    line-height: 1.7;
}
.chat-label {
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
    font-weight: 600;
}
.label-user { color: #6060a0; }
.label-bot { color: #2a7a5a; }

/* ── Source cards ── */
.source-card {
    background: #0c0c18;
    border: 1px solid #1a1a30;
    border-left: 3px solid #4f46e5;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.78rem;
    color: #6a6a90;
    line-height: 1.5;
}
.source-page {
    color: #a78bfa;
    font-weight: 600;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
}

/* ── Chat input ── */
.stChatInput textarea {
    background: #12121e !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 12px !important;
    color: #e2e2e8 !important;
    font-family: 'Inter', sans-serif !important;
}
.stChatInput textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.15) !important;
}

/* ── Sliders ── */
.stSlider [data-baseweb="slider"] {
    padding: 0 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #0f0f1e;
    border: 1px solid #1e1e30;
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] { color: #5a5a8a !important; font-size: 0.7rem !important; }
[data-testid="stMetricValue"] { color: #a78bfa !important; font-size: 1.4rem !important; font-family: 'Syne', sans-serif !important; }

/* ── Spinner ── */
.stSpinner { color: #a78bfa !important; }

/* ── Divider ── */
hr { border-color: #1e1e2e !important; margin: 16px 0 !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 20px;
}
.empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
    filter: grayscale(0.3);
}
.empty-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    color: #3a3a5a;
    margin-bottom: 8px;
}
.empty-sub {
    color: #2a2a4a;
    font-size: 0.85rem;
    line-height: 1.6;
}

/* ── Suggested questions ── */
.suggestion-btn {
    background: #0f0f1e;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 8px 14px;
    color: #7070a0;
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.15s;
    display: block;
    width: 100%;
    text-align: left;
    margin: 4px 0;
}
.suggestion-btn:hover {
    background: #15152a;
    border-color: #a78bfa;
    color: #c0b0ff;
}

/* ── Success / error alerts ── */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #4a4a6a; }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ──────────────────────────────────────
def init_state():
    defaults = {
        "qa_chain": None,
        "chat_history": [],        # list of {"role": "user"|"assistant", "content": str, "sources": [...]}
        "doc_meta": None,          # {"name": str, "pages": int, "chunks": int, "namespace": str}
        "processing": False,
        "total_queries": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand">DocMind</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">AI · Document Intelligence</div>', unsafe_allow_html=True)

    # Status pill
    if st.session_state.qa_chain:
        st.markdown(
            f'<span class="status-pill status-ready">● Ready — {st.session_state.doc_meta["name"]}</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<span class="status-pill status-idle">○ No document loaded</span>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">📄 Document</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your PDF here",
        type=["pdf"],
        help="Upload any PDF — research papers, contracts, manuals, books.",
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.caption(f"📎 {uploaded_file.name}  ·  {uploaded_file.size / 1024:.0f} KB")

    col1, col2 = st.columns(2)
    with col1:
        process_btn = st.button("⚡ Analyse", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑 Clear", use_container_width=True)

    st.markdown('<div class="section-label">⚙️ Settings</div>', unsafe_allow_html=True)

    temperature = st.slider(
        "Creativity", 0.0, 1.0, 0.3, 0.05,
        help="Lower = factual & precise. Higher = creative & verbose."
    )
    top_k = st.slider(
        "Context chunks (k)", 2, 10, 5, 1,
        help="How many document passages to retrieve per query."
    )
    show_sources = st.toggle("Show source passages", value=True)

    # Stats
    if st.session_state.doc_meta:
        st.markdown('<div class="section-label">📊 Document Info</div>', unsafe_allow_html=True)
        m = st.session_state.doc_meta
        st.metric("Pages", m["pages"])
        st.metric("Chunks", m["chunks"])
        st.metric("Queries", st.session_state.total_queries)

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.65rem;color:#2a2a4a;text-align:center;">Powered by Gemini · LangChain · Pinecone</p>',
        unsafe_allow_html=True
    )


# ── Clear handler ──────────────────────────────────────────────
if clear_btn:
    st.session_state.qa_chain = None
    st.session_state.chat_history = []
    st.session_state.doc_meta = None
    st.session_state.total_queries = 0
    st.rerun()


# ── Process PDF ────────────────────────────────────────────────
if process_btn and uploaded_file:
    with st.spinner("🔍 Extracting · Chunking · Embedding · Storing…"):
        try:
            from rag_pipeline import init_pinecone, process_pdf, embed_and_store, build_qa_chain

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            namespace = Path(uploaded_file.name).stem.lower().replace(" ", "-")[:40]

            # Pipeline
            index, index_name = init_pinecone()
            chunks, num_pages = process_pdf(tmp_path)
            embedder = embed_and_store(chunks, index, namespace=namespace)
            chain = build_qa_chain(index, embedder, namespace, temperature=temperature, top_k=top_k)

            # Save state
            st.session_state.qa_chain = chain
            st.session_state.chat_history = []
            st.session_state.doc_meta = {
                "name": uploaded_file.name,
                "pages": num_pages,
                "chunks": len(chunks),
                "namespace": namespace,
            }
            st.session_state.total_queries = 0

            os.unlink(tmp_path)
            st.success(f"✅ Ready! Indexed **{len(chunks)} chunks** across **{num_pages} pages**.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

elif process_btn and not uploaded_file:
    st.sidebar.warning("Please upload a PDF first.")


# ── Main area ──────────────────────────────────────────────────
if not st.session_state.qa_chain:
    # Hero + empty state
    st.markdown("""
    <div class="hero">
        <h1>Ask your documents anything.</h1>
        <p>Upload a PDF · Get instant AI-powered answers · Grounded in your content</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background:#0f0f1e;border:1px solid #1e1e30;border-radius:14px;padding:24px;text-align:center">
            <div style="font-size:2rem;margin-bottom:12px">📚</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:#a78bfa;margin-bottom:8px">Any PDF</div>
            <div style="font-size:0.8rem;color:#4a4a6a;line-height:1.6">Research papers, legal contracts, technical manuals, books — all supported</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:#0f0f1e;border:1px solid #1e1e30;border-radius:14px;padding:24px;text-align:center">
            <div style="font-size:2rem;margin-bottom:12px">🔍</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:#60a5fa;margin-bottom:8px">Semantic Search</div>
            <div style="font-size:0.8rem;color:#4a4a6a;line-height:1.6">Finds relevant passages by meaning, not just keywords — powered by Pinecone</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background:#0f0f1e;border:1px solid #1e1e30;border-radius:14px;padding:24px;text-align:center">
            <div style="font-size:2rem;margin-bottom:12px">💬</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:#34d399;margin-bottom:8px">Conversational</div>
            <div style="font-size:0.8rem;color:#4a4a6a;line-height:1.6">Multi-turn memory — ask follow-ups naturally without repeating context</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🧠</div>
        <div class="empty-title">Upload a PDF to begin</div>
        <div class="empty-sub">Use the sidebar → drop your PDF → click Analyse<br>Then ask any question in the chat below</div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Header bar ──
    meta = st.session_state.doc_meta
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:14px 20px;background:#0f0f18;border:1px solid #1e1e2e;
                    border-radius:12px;margin-bottom:20px">
            <div>
                <span style="font-family:'Syne',sans-serif;font-weight:700;color:#e2e2e8;font-size:1.0rem">
                    {meta['name']}
                </span>
                <span style="color:#3a3a6a;font-size:0.78rem;margin-left:12px">
                    {meta['pages']} pages · {meta['chunks']} chunks
                </span>
            </div>
            <span class="status-pill status-ready">● Live</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Suggested starters (shown only when no history) ──
    if not st.session_state.chat_history:
        st.markdown(
            '<div style="color:#3a3a6a;font-size:0.72rem;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px">💡 Try asking…</div>',
            unsafe_allow_html=True
        )
        suggestions = [
            "Summarise this document in 3 bullet points",
            "What are the main conclusions or findings?",
            "What problem does this document address?",
            "List any key numbers, dates or statistics mentioned",
        ]
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(s, key=f"sug_{i}", use_container_width=True):
                    st.session_state._pending_question = s
                    st.rerun()

    # ── Chat history display ──
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user"><div class="chat-label label-user">You</div>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-assistant"><div class="chat-label label-bot">DocMind</div>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
                if show_sources and msg.get("sources"):
                    with st.expander(f"📎 {len(msg['sources'])} source passage(s)", expanded=False):
                        for doc in msg["sources"]:
                            page = doc.metadata.get("page", "?")
                            snippet = doc.page_content[:300].replace("\n", " ")
                            st.markdown(
                                f'<div class="source-card"><div class="source-page">Page {int(page)+1 if isinstance(page, int) else page}</div>{snippet}…</div>',
                                unsafe_allow_html=True
                            )

    # ── Handle pending question from suggestion buttons ──
    pending = st.session_state.pop("_pending_question", None)

    # ── Chat input ──
    question = st.chat_input("Ask anything about your document…")
    question = question or pending

    if question:
        from rag_pipeline import query_document

        st.session_state.chat_history.append({"role": "user", "content": question, "sources": []})

        with st.spinner("Thinking…"):
            try:
                answer, sources = query_document(st.session_state.qa_chain, question)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
                st.session_state.total_queries += 1
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"⚠️ Error generating answer: {e}",
                    "sources": [],
                })

        st.rerun()