# Multi-stage build: compile the React frontend, then serve it together with
# the FastAPI backend from a single container/port. Works on both Hugging
# Face Spaces (Docker SDK, expects port 7860) and Render/other hosts that
# inject a $PORT env var — see the CMD at the bottom.

# ---- Stage 1: build the frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ---- Stage 2: backend + built frontend ----
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Uncomment to include local Whisper (voice input) + sentence-transformers
# (local embeddings) — heavy (PyTorch), needs more RAM than free tiers like
# Render's 512MB typically offer. Without this, the app automatically uses
# the Hugging Face Inference API for embeddings and disables voice input.
# RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
# COPY backend/requirements-full.txt backend/requirements-full.txt
# RUN pip install --no-cache-dir -r backend/requirements-full.txt

COPY backend/ backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Hugging Face Spaces (Docker SDK) expects port 7860; Render (and most other
# hosts) inject their own $PORT — this falls back to 7860 when unset.
ENV PORT=7860
EXPOSE 7860

WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
