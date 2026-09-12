from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings, STATIC_DIR, FRONTEND_DIST_DIR
from app.logger import get_logger
from app.routers import chat, translate, language, intent, weather, mandi, schemes, agriculture, speech

logger = get_logger(__name__)

app = FastAPI(
    title="AgriBot API",
    description="AI-Powered Agricultural Assistant — voice-enabled, multilingual backend "
                "for weather, mandi prices, government schemes, and crop care.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(chat.router)
app.include_router(translate.router)
app.include_router(language.router)
app.include_router(intent.router)
app.include_router(weather.router)
app.include_router(mandi.router)
app.include_router(schemes.router)
app.include_router(agriculture.router)
app.include_router(speech.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# In production (e.g. Hugging Face Spaces / Docker), the frontend is built
# ahead of time (`npm run build`) and served by this same FastAPI app at "/",
# so the deployed app is a single URL with no separate frontend host or CORS
# setup needed. In local dev, frontend/dist won't exist — the Vite dev server
# on :5173 serves the frontend instead, and "/" here just confirms the API.
if FRONTEND_DIST_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")),
        name="frontend-assets",
    )

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": "AgriBot API",
            "status": "running",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
