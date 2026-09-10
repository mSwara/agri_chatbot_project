"""
Crop Care & Agricultural Advice Module — Multi-Retriever RAG (report section 4.2d).

Retrievers: WikipediaRetriever, TavilySearchAPIRetriever (if TAVILY_API_KEY is
set), SerpAPIWrapper (if SERPAPI_API_KEY is set), with DuckDuckGo as a free
always-available fallback. The LLM is prompted to answer like a Krishi Vigyan
Kendra (KVK) expert.
"""
from app.config import settings
from app.logger import get_logger
from app.services.llm_service import chat_completion
from app.services.rag_service import duckduckgo_search

logger = get_logger(__name__)


def _wikipedia_context(query: str) -> list[str]:
    try:
        import wikipedia
        wikipedia.set_lang("en")
        titles = wikipedia.search(query, results=2)
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


def _tavily_context(query: str) -> list[str]:
    if not settings.tavily_api_key:
        return []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        result = client.search(query=f"{query} crop agriculture India", max_results=3)
        return [r.get("content", "") for r in result.get("results", []) if r.get("content")]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily retriever failed: %s", exc)
        return []


def _serpapi_context(query: str) -> list[str]:
    if not settings.serpapi_api_key:
        return []
    try:
        from serpapi import GoogleSearch
        search = GoogleSearch({
            "q": f"{query} crop agriculture India",
            "api_key": settings.serpapi_api_key,
        })
        results = search.get_dict()
        snippets = [r.get("snippet", "") for r in results.get("organic_results", [])]
        return [s for s in snippets if s]
    except Exception as exc:  # noqa: BLE001
        logger.warning("SerpAPI retriever failed: %s", exc)
        return []


def _duckduckgo_context(query: str) -> list[str]:
    return duckduckgo_search(f"{query} crop agriculture India", max_results=3)


def get_crop_care_answer(query: str) -> dict:
    contexts: list[str] = []
    sources: list[str] = []

    wiki = _wikipedia_context(query)
    if wiki:
        contexts += wiki
        sources.append("Wikipedia")

    tavily = _tavily_context(query)
    if tavily:
        contexts += tavily
        sources.append("Tavily Search")

    serp = _serpapi_context(query)
    if serp:
        contexts += serp
        sources.append("SerpAPI")

    if not tavily and not serp:
        ddg = _duckduckgo_context(query)
        if ddg:
            contexts += ddg
            sources.append("DuckDuckGo Search")

    context_block = "\n\n".join(f"[Source {i+1}] {c}" for i, c in enumerate(contexts))
    system_prompt = (
        "You are AgriBot, acting as an expert from a Krishi Vigyan Kendra (KVK) advising "
        "an Indian farmer. Give clear, practical, step-by-step guidance on crop diseases, "
        "fertilizers, farm equipment, sowing schedules, or pest control as asked. Use the "
        "provided context where relevant, but you may also rely on your general agronomy "
        "knowledge. Keep the answer actionable and under 150 words."
    )
    user_prompt = (
        f"Context:\n{context_block}\n\nFarmer's question: {query}"
        if context_block else f"Farmer's question: {query}"
    )
    answer = chat_completion(system_prompt, user_prompt)
    return {"answer": answer, "sources": sources}
