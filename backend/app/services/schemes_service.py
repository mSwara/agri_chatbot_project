"""
Government Schemes Module — Multi-Retriever RAG (report section 4.2c).

1. schemes.txt is chunked and embedded with all-MiniLM-L6-v2, stored in FAISS
   (or Pinecone, if configured).
2. On a query, relevant chunks are retrieved via similarity search.
3. Wikipedia and DuckDuckGo are queried for extra context to enrich the
   answer (works even fully offline on just the embedded knowledge if both
   are unreachable).
4. The LLM synthesizes a final natural-language answer from all retrieved
   context.
"""
from app.config import DATA_DIR
from app.logger import get_logger
from app.services.rag_service import LocalFaissStore, chunk_text, duckduckgo_search
from app.services.llm_service import chat_completion

logger = get_logger(__name__)

SCHEMES_FILE = DATA_DIR / "schemes.txt"
_store = LocalFaissStore("schemes")


def _load_chunks() -> list[str]:
    text = SCHEMES_FILE.read_text(encoding="utf-8")
    return chunk_text(text)


def _wikipedia_context(query: str) -> list[str]:
    try:
        import wikipedia
        wikipedia.set_lang("en")
        titles = wikipedia.search(query + " India scheme agriculture", results=2)
        snippets = []
        for title in titles:
            try:
                snippets.append(wikipedia.summary(title, sentences=3))
            except Exception:  # noqa: BLE001
                continue
        return snippets
    except Exception as exc:  # noqa: BLE001
        logger.warning("Wikipedia retriever unavailable: %s", exc)
        return []


def _duckduckgo_context(query: str) -> list[str]:
    return duckduckgo_search(query + " India government scheme", max_results=3)


def get_scheme_answer(query: str) -> dict:
    _store.ensure_ready(_load_chunks)
    local_chunks = _store.search(query, k=4)
    web_chunks = _wikipedia_context(query) + _duckduckgo_context(query)

    context = "\n\n".join(f"[Source {i+1}] {c}" for i, c in enumerate(local_chunks + web_chunks))
    system_prompt = (
        "You are AgriBot, an assistant helping Indian farmers understand government "
        "agricultural schemes. Use ONLY the provided context to answer. If the context "
        "doesn't cover the question, say what you can and suggest the farmer check the "
        "official scheme portal. Be concise, practical, and mention eligibility/benefit "
        "amounts when available."
    )
    user_prompt = f"Context:\n{context}\n\nFarmer's question: {query}"
    answer = chat_completion(system_prompt, user_prompt)

    sources = ["schemes.txt (local knowledge base)"] if local_chunks else []
    if web_chunks:
        sources.append("Wikipedia / DuckDuckGo web search")
    return {"answer": answer, "sources": sources}
