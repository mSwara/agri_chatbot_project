# AgriBot — AI-Powered Agricultural Assistant

A voice-enabled, multilingual AI chatbot that helps Indian farmers with weather
forecasts, mandi (market) prices, government agricultural schemes, and general
crop care — rebuilt from the AgriBot project report.

- **Backend**: FastAPI + LangChain-style RAG (FAISS/Pinecone) + Groq LLM + Whisper (STT) + gTTS (TTS)
- **Frontend**: React + Vite + Tailwind CSS, with mic input and voice playback

## Project layout

```
agri_chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + routes
│   │   ├── config.py          # env-driven settings
│   │   ├── models/schemas.py  # request/response models
│   │   ├── routers/           # one file per endpoint group
│   │   └── services/          # weather, mandi, schemes(RAG), crop care(RAG), speech, LLM
│   ├── data/                  # schemes.txt, mandi_sample.csv, FAISS index cache
│   ├── static/audio/          # generated TTS mp3s served at /static/audio/
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/        # Header, ChatWindow, MessageBubble, InputBar, MicButton, SpeakerButton, TranslateDropdown
    │   └── services/api.js
    ├── index.html
    └── package.json
```

## API endpoints (mirrors the report's API summary)

| Endpoint | Purpose |
|---|---|
| `POST /chat` | End-to-end: language detect → translate → intent → module → translate back → TTS |
| `POST /translate-to-english`, `/translate-from-english` | Bidirectional translation |
| `POST /detect-language` | Identify input language |
| `POST /detect-intent` | Classify query into weather / mandi_price / scheme_info / crop_care / greeting / general |
| `POST /get-weather` | Localized weather + crop-protection advice |
| `POST /get-mandi-prices` | Market prices with district→state→all-India fallback |
| `POST /get-scheme-info` | RAG over government schemes knowledge base |
| `POST /get-agriculture-info` | RAG over crop-care / pest / fertilizer knowledge |
| `POST /speech-to-text` | Whisper transcription of uploaded audio |
| `POST /text-to-speech` | gTTS-generated `.mp3`, returns URL |

Interactive Swagger docs: `http://localhost:8000/docs`

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and add whichever keys you have (see below). Then run:

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` and `/static`
to the backend on port 8000 (see `vite.config.js`), so no CORS setup is needed
locally.

## API keys — what's required vs. optional

AgriBot is designed to **run immediately with zero keys**, using free local/offline
equivalents, then upgrade module-by-module as you add keys to `backend/.env`:

| Feature | Works without a key? | Key to add for the "real" report version |
|---|---|---|
| Language detection & translation | ✅ (`langdetect` + `deep-translator`) | `GOOGLE_APPLICATION_CREDENTIALS` (Google Cloud Translate) |
| Text-to-speech | ✅ (`gTTS`, free) | — already matches report |
| Speech-to-text | ✅ (`openai-whisper`, runs locally; needs `ffmpeg` installed) | — already matches report |
| Chat / intent / RAG answer generation | ⚠️ returns a placeholder message | `GROQ_API_KEY` (free tier at console.groq.com) |
| Weather | ⚠️ returns "no live data" message | `OPENWEATHER_API_KEY` |
| Mandi prices | ✅ (bundled `mandi_sample.csv` demonstrates the fallback logic) | `DATA_GOV_API_KEY` (free, data.gov.in) |
| Government schemes RAG | ✅ (local `schemes.txt` + FAISS + Wikipedia/DuckDuckGo) | `PINECONE_API_KEY` to swap FAISS → Pinecone |
| Crop care RAG | ✅ (Wikipedia + DuckDuckGo) | `TAVILY_API_KEY`, `SERPAPI_API_KEY` for broader retrieval |

**Minimum to see the full chat intelligence working: just set `GROQ_API_KEY`.**

## Notes on fidelity to the report

- Weather & mandi modules use an LLM call to extract entities (city/crop/state/district) from free text, exactly as described.
- Mandi module implements the district → state → all-India → "list available crops" fallback chain.
- Schemes and Crop Care modules are both multi-retriever RAG pipelines (local vector search + web retrievers), answering in the style of a PM-KISAN helpdesk / Krishi Vigyan Kendra expert respectively.
- Frontend chat UI matches the described flow: hardcoded English greeting with a hover-revealed Translate dropdown (not spoken aloud), user bubbles in green on the right, bot bubbles in gray on the left with a speaker icon (only one audio plays at a time) and a "Translate to English" toggle when the reply isn't in English.
