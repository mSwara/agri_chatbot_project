# Multi-stage build: compile the React frontend, then serve it together with
# the FastAPI backend from a single container/port (what Hugging Face Spaces'
# Docker SDK expects).

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

# ffmpeg is required by openai-whisper to decode uploaded audio
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Hugging Face Spaces (Docker SDK) expects the app on port 7860
ENV APP_PORT=7860
EXPOSE 7860

WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
