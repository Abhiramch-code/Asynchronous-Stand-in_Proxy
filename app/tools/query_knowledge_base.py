# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Knowledge Base Query Tool
#
# Uses ChromaDB as a local vector store with text-embedding-004 embeddings.
# All embedding API calls are wrapped with tenacity exponential backoff
# to handle the 15 RPM free-tier rate limit on the Gemini API.

from __future__ import annotations

import hashlib
import logging
import os
import pathlib
from typing import Optional

import chromadb
from google import genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "models/gemini-embedding-2"
COLLECTION_NAME = "standin_knowledge_base"
CHUNK_SIZE = 500  # characters per chunk (small for free-tier efficiency)
CHUNK_OVERLAP = 50  # overlap between chunks for context continuity
TOP_K = 2  # number of results to return

# Path to the /docs directory (relative to project root)
DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "docs"
CHROMA_PERSIST_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / ".chromadb"

# ---------------------------------------------------------------------------
# Singleton state — initialized once, reused across tool calls
# ---------------------------------------------------------------------------
_chroma_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None
_genai_client: Optional[genai.Client] = None
_initialized: bool = False


def _get_genai_client() -> genai.Client:
    """Get or create the Google GenAI client."""
    global _genai_client
    if _genai_client is None:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "No API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env"
            )
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


# ---------------------------------------------------------------------------
# Retry predicate — only retry TRANSIENT errors, not permanent ones
# ---------------------------------------------------------------------------
def _is_retryable_error(exception: BaseException) -> bool:
    """Return True only for transient/rate-limit errors that are worth retrying.

    Retries on:
      - 429 Resource Exhausted (rate limit — the main free-tier concern)
      - 503 Service Unavailable (transient server issue)
      - ConnectionError / TimeoutError (network glitches)

    Does NOT retry on:
      - 400 Bad Request (invalid API key, malformed request — permanent)
      - 401/403 Unauthorized/Forbidden (auth issues — permanent)
      - 404 Not Found (wrong model name — permanent)
    """
    # google.api_core exceptions (used by google-genai under the hood)
    if isinstance(exception, (ResourceExhausted, ServiceUnavailable)):
        return True

    # Network-level transient errors
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return True

    # google-genai raises generic errors with status codes in the message
    error_str = str(exception).lower()
    if "429" in error_str or "resource exhausted" in error_str:
        return True
    if "503" in error_str or "service unavailable" in error_str:
        return True

    return False


# ---------------------------------------------------------------------------
# Tenacity-wrapped embedding call — exponential backoff for 429 errors
# ---------------------------------------------------------------------------
@retry(
    retry=retry_if_exception(_is_retryable_error),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=lambda retry_state: logger.warning(
        f"Transient API error (likely rate limit). Retrying in "
        f"{retry_state.next_action.sleep:.1f}s "  # type: ignore[union-attr]
        f"(attempt {retry_state.attempt_number}/5)..."
    ),
    reraise=True,
)
def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using text-embedding-004 with retry/backoff.

    This function is wrapped with tenacity to handle 429 Resource Exhausted
    errors from the Gemini API free tier (15 RPM limit). It uses exponential
    backoff: 4s → 8s → 16s → 32s → 60s between retries, up to 5 attempts.

    Permanent errors (400 Bad Request, 401 Unauthorized, etc.) are NOT retried
    and will raise immediately.
    """
    client = _get_genai_client()
    contents = [genai.types.Content(parts=[genai.types.Part.from_text(text=t)]) for t in texts]
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=contents,
    )
    return [list(emb.values) for emb in response.embeddings]


# ---------------------------------------------------------------------------
# Document chunking
# ---------------------------------------------------------------------------
def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks


def _content_hash(text: str) -> str:
    """Generate a deterministic hash for content deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Document ingestion pipeline
# ---------------------------------------------------------------------------
def _load_and_index_docs() -> None:
    """Load markdown files from /docs, chunk, embed, and store in ChromaDB.

    This is called once during initialization. It reads all .md and .txt files
    from the docs directory, chunks them, generates embeddings via the Gemini API
    (with tenacity backoff), and upserts them into the ChromaDB collection.
    """
    global _collection

    if _collection is None:
        raise RuntimeError("ChromaDB collection not initialized")

    # Check if docs directory exists
    if not DOCS_DIR.exists():
        logger.warning(f"Docs directory not found at {DOCS_DIR}")
        return

    # Collect all document files
    doc_files = list(DOCS_DIR.glob("**/*.md")) + list(DOCS_DIR.glob("**/*.txt"))
    # Exclude README.md (it's just instructions, not knowledge)
    doc_files = [f for f in doc_files if f.name != "README.md"]

    if not doc_files:
        logger.warning("No document files found in /docs directory")
        return

    logger.info(f"Found {len(doc_files)} document(s) to index")

    all_ids: list[str] = []
    all_chunks: list[str] = []
    all_metadatas: list[dict] = []

    for doc_path in doc_files:
        text = doc_path.read_text(encoding="utf-8")
        chunks = _chunk_text(text)
        filename = doc_path.name

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{_content_hash(chunk)}_{i}"
            all_ids.append(chunk_id)
            all_chunks.append(chunk)
            all_metadatas.append({
                "source_file": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

    if not all_chunks:
        logger.warning("No text chunks extracted from documents")
        return

    # Embed all chunks (batched, with tenacity backoff)
    logger.info(f"Embedding {len(all_chunks)} chunks with {EMBEDDING_MODEL}...")
    batch_size = 5  # Small batches to stay within free-tier limits
    all_embeddings: list[list[float]] = []

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        embeddings = _embed_texts(batch)
        all_embeddings.extend(embeddings)
        logger.info(
            f"  Embedded batch {i // batch_size + 1}/"
            f"{(len(all_chunks) + batch_size - 1) // batch_size}"
        )

    # Upsert into ChromaDB
    _collection.upsert(
        ids=all_ids,
        embeddings=all_embeddings,
        documents=all_chunks,
        metadatas=all_metadatas,
    )

    logger.info(
        f"Indexed {len(all_chunks)} chunks from {len(doc_files)} document(s) "
        f"into ChromaDB collection '{COLLECTION_NAME}'"
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
def initialize_knowledge_base() -> None:
    """Initialize ChromaDB and index documents from /docs.

    Call this once at application startup. It creates a persistent ChromaDB
    collection and ingests all documents from the /docs directory.
    """
    global _chroma_client, _collection, _initialized

    if _initialized:
        logger.info("Knowledge base already initialized, skipping.")
        return

    logger.info(f"Initializing ChromaDB at {CHROMA_PERSIST_DIR}...")
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    _chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
    )

    # Index documents
    _load_and_index_docs()
    _initialized = True
    logger.info("Knowledge base initialization complete.")


# ---------------------------------------------------------------------------
# The ADK Tool function — this is what agents call
# ---------------------------------------------------------------------------
def query_knowledge_base(query: str) -> dict:
    """Searches the local knowledge base for information relevant to the query.

    Uses ChromaDB with text-embedding-004 embeddings to perform semantic search
    over project documentation and meeting notes stored in the /docs directory.
    Returns the top 2 most relevant text passages.

    Args:
        query: A natural language question or search query about the project.

    Returns:
        A dictionary with 'status' and 'results' containing relevant passages,
        or an error message if the knowledge base is not initialized.
    """
    global _collection, _initialized

    if not _initialized or _collection is None:
        # Try to initialize on first call if not done yet
        try:
            initialize_knowledge_base()
        except Exception as e:
            return {
                "status": "error",
                "results": f"Knowledge base not initialized: {e}",
            }

    try:
        # Embed the query (with tenacity backoff)
        query_embedding = _embed_texts([query])[0]

        # Query ChromaDB for top-K results
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            return {
                "status": "no_results",
                "results": "No relevant information found in the knowledge base.",
            }

        # Format results
        passages = []
        for doc, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            passages.append({
                "text": doc,
                "source": metadata.get("source_file", "unknown"),
                "relevance_score": round(1.0 - distance, 4),  # Convert distance to similarity
            })

        return {
            "status": "success",
            "results": passages,
            "query": query,
        }

    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return {
            "status": "error",
            "results": f"Error searching knowledge base: {e}",
        }
