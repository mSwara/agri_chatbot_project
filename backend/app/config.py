"""
Centralized configuration for AgriBot backend.
All values are read from environment variables (see .env.example).
Nothing here is required to be set for the app to *start* — missing keys
simply disable that module's live-API features and fall back to local logic.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = STATIC_DIR / "audio"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# Built frontend (output of `npm run build` in frontend/), served directly by
# FastAPI in production (e.g. Hugging Face Spaces) so the whole app is one
# deployable unit at one URL. Absent in local dev, where the Vite dev server
# on :5173 serves the frontend instead — see main.py for the fallback.
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # Weather
    openweather_api_key: str = ""

    # Mandi prices
    data_gov_api_key: str = ""
    agmarknet_resource_id: str = "9ef84268-d588-465a-a308-a864a43d0070"

    # Broader search retrievers
    tavily_api_key: str = ""
    serpapi_api_key: str = ""

    # Vector DB
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "agribot-knowledge"

    # Embeddings fallback: used only when sentence-transformers/PyTorch isn't
    # installed locally (e.g. lightweight production deployments) — see
    # services/rag_service.py. Free token at huggingface.co/settings/tokens.
    hf_api_token: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
