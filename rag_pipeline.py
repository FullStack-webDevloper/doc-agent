import os
import uuid
import time
from dataclasses import dataclass, field
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()


# ── 1. Initialize Pinecone (v9 SDK) ───────────────────────────
def init_pinecone():
    from pinecone import Pinecone, ServerlessSpec

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in .env file.")

    pc = Pinecone(api_key=api_key)
    index_name = os.getenv("PINECONE_INDEX", "doc-qa-index")

    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

    index = pc.Index(index_name)
    return index, index_name


# ── 2. Pure-Python text chunker (no LangChain splitter needed) ─
def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ── 3. Load & chunk PDF ────────────────────────────────────────
def process_pdf(pdf_path: str):
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    if not reader.pages:
        raise ValueError("No content could be extracted from the PDF.")

    # Build (text, page_number) pairs per chunk
    chunks = []   # list of dicts: {text, page}
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue
        for piece in _chunk_text(text, chunk_size=1000, overlap=200):
            piece = piece.strip()
            if piece:
                chunks.append({"text": piece, "page": page_num})

    num_pages = len(reader.pages)
    if not chunks:
        raise ValueError("No readable text could be extracted from the PDF.")
    return chunks, num_pages


# ── 4. Embed chunks and upsert into Pinecone ──────────────────
def embed_and_store(chunks, index, namespace: str = "default"):
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    embedder = GoogleGenerativeAIEmbeddings(
        model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001"),
        google_api_key=api_key,
        output_dimensionality=768,
    )

    texts = [c["text"] for c in chunks if c.get("text", "").strip()]
    if not texts:
        raise ValueError("No non-empty text was found to embed.")

    vectors = embedder.embed_documents(texts)

    records = []
    text_chunks = [c for c in chunks if c.get("text", "").strip()]
    for chunk, vector in zip(text_chunks, vectors):
        records.append({
            "id": str(uuid.uuid4()),
            "values": vector,
            "metadata": {
                "text": chunk["text"],
                "page": chunk["page"],
            },
        })

    batch_size = 100
    for i in range(0, len(records), batch_size):
        index.upsert(vectors=records[i : i + batch_size], namespace=namespace)

    return embedder


# ── 5. Custom retriever (no langchain-pinecone needed) ────────
def retrieve_documents(index, embedder, namespace: str, question: str, top_k: int):
    from langchain_core.documents import Document

    query_vec = embedder.embed_query(question)
    results = index.query(
        vector=query_vec,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )

    docs = []
    for match in results.matches:
        meta = match.metadata or {}
        docs.append(
            Document(
                page_content=meta.get("text", ""),
                metadata={
                    "page": meta.get("page", "?"),
                    "score": round(match.score, 3),
                },
            )
        )
    return docs


@dataclass
class SimpleConversationalQAChain:
    llm: object
    index: object
    embedder: object
    namespace: str
    top_k: int = 5
    chat_history: List[Tuple[str, str]] = field(default_factory=list)

    def __call__(self, inputs):
        return self.invoke(inputs)

    def invoke(self, inputs):
        question = inputs.get("question", "").strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        docs = retrieve_documents(self.index, self.embedder, self.namespace, question, self.top_k)
        context = "\n\n".join(
            f"[Source {i + 1}, page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for i, doc in enumerate(docs)
        )
        history = "\n".join(
            f"User: {q}\nAssistant: {a}" for q, a in self.chat_history[-5:]
        )

        prompt = (
            "You are a document question-answering assistant. Answer only from the "
            "provided context. If the answer is not in the context, say that the "
            "document does not provide enough information.\n\n"
            f"Conversation history:\n{history or 'No previous conversation.'}\n\n"
            f"Context:\n{context or 'No relevant context retrieved.'}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        response = self.llm.invoke(prompt)
        answer = getattr(response, "content", str(response))
        self.chat_history.append((question, answer))
        return {"answer": answer, "source_documents": docs}


# ── 6. Build conversational QA chain ──────────────────────────
def build_qa_chain(index, embedder, namespace: str, temperature: float = 0.3, top_k: int = 5):
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_CHAT_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature,
        convert_system_message_to_human=True,
    )

    return SimpleConversationalQAChain(
        llm=llm,
        index=index,
        embedder=embedder,
        namespace=namespace,
        top_k=top_k,
    )


# ── 7. Query ──────────────────────────────────────────────────
def query_document(chain, question: str):
    result = chain.invoke({"question": question}) if hasattr(chain, "invoke") else chain({"question": question})
    answer = result.get("answer", "No answer returned.")
    sources = result.get("source_documents", [])

    seen = set()
    unique_sources = []
    for doc in sources:
        key = (doc.metadata.get("page", "?"), doc.page_content[:80])
        if key not in seen:
            seen.add(key)
            unique_sources.append(doc)

    return answer, unique_sources
