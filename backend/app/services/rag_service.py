"""
Shared Retrieval-Augmented Generation utilities.

Embeddings: all-MiniLM-L6-v2 (SentenceTransformers), matching the report.
Vector store: local FAISS index by default (no external service required).
If PINECONE_API_KEY is set, a Pinecone index is used instead — this is the
"swap-in" point for the cloud vector DB described in the report.
"""
import pickle
from pathlib import Path

import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from app.config import settings, VECTORSTORE_DIR
from app.logger import get_logger

logger = get_logger(__name__)

_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("Loading embedding model all-MiniLM-L6-v2 ...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def embed(texts: list[str]) -> np.ndarray:
    return get_embedder().encode(texts, convert_to_numpy=True, normalize_embeddings=True)


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
