"""
rag.py
Module 3 - RAG Pipeline.

Turns extracted document text into a searchable vector index:
  1. chunk_text         - split raw text into overlapping chunks
  2. get_embedder        - load a local sentence-transformers embedding model
  3. build_vectorstore   - embed all chunks and save a FAISS index to disk
  4. load_vectorstore    - reload a previously saved FAISS index
  5. semantic_search     - embed a query and return the top-k closest chunks

Design choices (worth knowing if asked about them in review):
- Chunking uses LangChain's RecursiveCharacterTextSplitter rather than a
  naive fixed-size split, because it tries to break on paragraph, then
  sentence, then word boundaries first - so chunks stay semantically
  coherent instead of getting cut off mid-sentence.
- Embeddings run locally via sentence-transformers (all-MiniLM-L6-v2).
  No external API call needed, so this works fully offline once the
  model has been downloaded and cached once.
- The embedding model is loaded lazily and cached in a module-level
  variable, since loading it from disk takes a second or two and we
  don't want to pay that cost on every single request.
- One FAISS index per document (not one shared index for everything).
  This keeps semantic search for Module 4 scoped to "search only inside
  the document the user is currently chatting with", which is simpler
  and more correct than filtering a giant shared index by metadata.
"""

import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document as LangchainDocument

VECTORSTORE_DIR = "vectorstores"
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_embedder = None  # lazy-loaded, module-level cache so we only load once per process


def get_embedder() -> HuggingFaceEmbeddings:
    """
    Returns a cached HuggingFaceEmbeddings instance, loading the model
    from disk only the first time it's actually needed.
    """
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedder


def chunk_text(text: str) -> list[str]:
    """
    Splits raw document text into overlapping chunks small enough to
    embed meaningfully, while keeping enough overlap (50 chars) that
    we don't lose context that happens to span a chunk boundary.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [c for c in chunks if c.strip()]


def build_vectorstore(document_id: int, text: str) -> str:
    """
    Chunks the document text, embeds every chunk, and saves a FAISS
    index to disk under vectorstores/doc_<document_id>/.

    Returns the path the index was saved to - this is what gets
    stored in Document.vectorstore_path so the index can be reloaded
    later (Module 4 chat) without re-embedding anything.
    """
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No chunks produced from document text - nothing to index")

    docs = [
        LangchainDocument(
            page_content=chunk,
            metadata={"document_id": document_id, "chunk_index": i},
        )
        for i, chunk in enumerate(chunks)
    ]

    embedder = get_embedder()
    vectorstore = FAISS.from_documents(docs, embedder)

    path = os.path.join(VECTORSTORE_DIR, f"doc_{document_id}")
    vectorstore.save_local(path)
    return path


def load_vectorstore(vectorstore_path: str) -> FAISS:
    """
    Reloads a previously saved FAISS index from disk.

    allow_dangerous_deserialization=True is safe here specifically
    because we only ever load indexes *we* wrote to disk in
    build_vectorstore above - never an index from an untrusted source.
    """
    embedder = get_embedder()
    return FAISS.load_local(
        vectorstore_path, embedder, allow_dangerous_deserialization=True
    )


def semantic_search(vectorstore_path: str, query: str, k: int = 4) -> list[str]:
    """
    Embeds the query and returns the k chunks whose embeddings are
    closest to it - i.e. the most relevant pieces of the document to
    hand to the LLM as context. This is what Module 4 (chat) will call.
    """
    vectorstore = load_vectorstore(vectorstore_path)
    results = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
