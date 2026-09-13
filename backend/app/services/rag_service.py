"""
Shared Retrieval-Augmented Generation utilities.

Embeddings: all-MiniLM-L6-v2 (Hugging Face / SentenceTransformers).
Two backends are supported so the same code runs on both a full local/dev
machine and a memory-constrained free-tier host:
  1. Local `sentence-transformers` (needs PyTorch) — used automatically if
     installed. Best latency, no external calls, matches the original design.
  2. Hugging Face's hosted Inference API (`HF_API_TOKEN`, free) — used as a
     fallback when the local library/PyTorch isn't installed, since PyTorch
     alone is too heavy for some free hosting tiers (e.g. Render's 512MB).

Vector store: local FAISS index by default (no external service required).
If PINECONE_API_KEY is set, a Pinecone index is used instead — this is the
"swap-in" point for the cloud vector DB described in the report.
"""
import pickle
from pathlib import Path

import numpy as np
import requests
from bs4 import BeautifulSoup

from app.config import settings, VECTORSTORE_DIR
from app.logger import get_logger

logger = get_logger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_HF_INFERENCE_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBEDDING_MODEL_NAME}"

_local_embedder = None


def _get_local_embedder():
    """Lazily load sentence-transformers. Returns None if not installed."""
    global _local_embedder
    if _local_embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None
        logger.info("Loading local embedding model all-MiniLM-L6-v2 ...")
        _local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _local_embedder


def _remote_embed(texts: list[str]) -> np.ndarray:
    """Embed via Hugging Face's hosted Inference API (no local PyTorch needed)."""
    if not settings.hf_api_token:
        raise RuntimeError(
            "No embedding backend available: sentence-transformers isn't installed "
            "and HF_API_TOKEN isn't set. Either install sentence-transformers, or "
            "set HF_API_TOKEN (free at huggingface.co/settings/tokens) in backend/.env."
        )
    resp = requests.post(
        _HF_INFERENCE_URL,
        headers={"Authorization": f"Bearer {settings.hf_api_token}"},
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=30,
    )
    resp.raise_for_status()
    vectors = np.array(resp.json(), dtype="float32")
    if vectors.ndim == 3:  # per-token vectors from some models — mean-pool them
        vectors = vectors.mean(axis=1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vectors / norms


def embed(texts: list[str]) -> np.ndarray:
    model = _get_local_embedder()
    if model is not None:
        return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return _remote_embed(texts)


class LocalFaissStore:
    """Minimal FAISS-backed vector store for a named collection of text chunks."""

    def __init__(self, name: str):
        self.name = name
        self.index_path = VECTORSTORE_DIR / f"{name}.faiss"
        self.meta_path = VECTORSTORE_DIR / f"{name}.pkl"
        self._index = None
        self._chunks: list[str] = []

    def _load(self):
        import faiss
        if self.index_path.exists() and self.meta_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self._chunks = pickle.load(f)

    def build(self, chunks: list[str]):
        import faiss
        vectors = embed(chunks)
        dim = vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vectors)
        faiss.write_index(index, str(self.index_path))
        with open(self.meta_path, "wb") as f:
            pickle.dump(chunks, f)
        self._index = index
        self._chunks = chunks
        logger.info("Built FAISS index '%s' with %d chunks.", self.name, len(chunks))

    def ensure_ready(self, chunks_factory):
        if self._index is None:
            self._load()
        if self._index is None:
            self.build(chunks_factory())

    def search(self, query: str, k: int = 4) -> list[str]:
        if self._index is None:
            self._load()
        if self._index is None or not self._chunks:
            return []
        qvec = embed([query])
        scores, idx = self._index.search(qvec, min(k, len(self._chunks)))
        return [self._chunks[i] for i in idx[0] if i != -1]


_DDG_HTML_URL = "https://html.duckduckgo.com/html/"
_DDG_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AgriBot/1.0; +https://github.com)"}


def duckduckgo_search(query: str, max_results: int = 3) -> list[str]:
    """
    Free, dependency-light DuckDuckGo web search used as a fallback retriever.

    Implemented as a direct scrape of the HTML-only endpoint (via `requests`
    + `BeautifulSoup`) rather than the `duckduckgo-search` package, whose
    recent releases depend on a Rust HTTP backend with no prebuilt wheels for
    newer Python versions, and whose older releases hit a removed `proxies`
    kwarg on modern `httpx`. Returns a list of result snippet strings.
    """
    try:
        resp = requests.post(
            _DDG_HTML_URL, data={"q": query}, headers=_DDG_HEADERS, timeout=10,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = [
            el.get_text(" ", strip=True)
            for el in soup.select(".result__snippet")[:max_results]
        ]
        return [s for s in snippets if s]
    except Exception as exc:  # noqa: BLE001
        logger.warning("DuckDuckGo search failed for %r: %s", query, exc)
        return []


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """Simple sliding-window chunker over paragraph-separated text."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
            continue
        start = 0
        while start < len(para):
            chunks.append(para[start:start + chunk_size])
            start += chunk_size - overlap
    return chunks
