# AgriBot — AI-Powered Agricultural Assistant

AgriBot is a voice-enabled, multilingual chatbot built to help Indian farmers get
quick answers on weather, mandi (market) prices, government agricultural schemes,
and general crop care — all in their own language, by typing or speaking.

- **Backend**: FastAPI + a RAG pipeline (FAISS/Pinecone) + Groq LLM + Whisper (speech-to-text) + gTTS (text-to-speech)
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

## API endpoints

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

| Feature | Works without a key? | Key to add for full functionality |
|---|---|---|
| Language detection & translation | ✅ (`langdetect` + `deep-translator`) | — |
| Text-to-speech | ✅ (`gTTS`, free) | — |
| Speech-to-text | ✅ (`openai-whisper`, runs locally; needs `ffmpeg` installed) | — |
| Chat / intent / RAG answer generation | ⚠️ returns a placeholder message | `GROQ_API_KEY` (free tier at console.groq.com) |
| Weather | ⚠️ returns "no live data" message | `OPENWEATHER_API_KEY` |
| Mandi prices | ✅ (bundled `mandi_sample.csv` demonstrates the fallback logic) | `DATA_GOV_API_KEY` (free, data.gov.in) |
| Government schemes RAG | ✅ (local `schemes.txt` + FAISS + Wikipedia) | `PINECONE_API_KEY` to swap FAISS → Pinecone |
| Crop care RAG | ✅ (Wikipedia) | `TAVILY_API_KEY`, `SERPAPI_API_KEY` for broader retrieval |

**Minimum to see the full chat intelligence working: just set `GROQ_API_KEY`.**

## How it works

- The weather and mandi modules use an LLM call to pull out entities (city, crop,
  state, district) from whatever the user types, instead of relying on rigid
  form fields.
- Mandi price lookups fall back gracefully: district → state → all-India, and
  finally list available crops if nothing matches.
- Government schemes and crop care are both handled with a multi-retriever RAG
  setup — local vector search over a knowledge base combined with live web
  retrieval — so answers stay grounded and specific instead of generic.
- The chat UI opens with a friendly greeting that can be translated on hover,
  keeps user/bot messages visually distinct, and lets you play back any bot
  reply as audio or flip a non-English reply back to English.



<img width="600" height="300" alt="{F91692BD-005F-44A7-B33F-71C906709277}" src="https://github.com/user-attachments/assets/5c6f9574-26d3-4519-8742-1191be78e3ca" />
<img width="815" height="401" alt="{C77FCD0F-C450-4954-97BC-E537750C2677}" src="https://github.com/user-attachments/assets/6f2f8cb4-5bc2-4eae-8775-116fda02dada" />
<img width="806" height="399" alt="{C111D785-53E8-4680-924F-8F2F785C4123}" src="https://github.com/user-attachments/assets/f42c8bb2-0a3e-40de-97a6-fe67b70bb9b2" />


