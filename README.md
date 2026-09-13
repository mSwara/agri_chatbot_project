# AgriBot — AI-Powered Agricultural Assistant
🔗 **[Try the live app](https://agribot-dzdf.onrender.com/)**


AgriBot is a voice-enabled, multilingual chatbot built to help Indian farmers get
quick answers on weather, mandi (market) prices, government agricultural schemes,
and general crop care — all in their own language, by typing or speaking.

- **Backend**: FastAPI + a RAG pipeline (FAISS/Pinecone, Hugging Face embeddings) + Groq LLM + Whisper (speech-to-text, optional) + gTTS (text-to-speech)
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
| `POST /speech-to-text` | Whisper transcription of uploaded audio (needs `requirements-full.txt`) |
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

For real voice input (Whisper) and local embeddings instead of the Hugging
Face Inference API, also install the optional heavy dependencies (PyTorch):
```bash
pip install -r requirements-full.txt
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

Open `http://localhost:5173`. The Vite dev server proxies API calls straight
to the backend on port 8000 (see `vite.config.js`), so no CORS setup is needed
locally.

### One-click local start (Windows)

`start_agribot.bat` (at the project root) launches both servers and opens the
app in your browser in one go — just double-click it. `stop_agribot.bat`
shuts both down.

## Deployment

A `Dockerfile` at the project root builds the frontend and packages it with
the backend into a single container that serves the whole app from one port
— ready for Render, Hugging Face Spaces' Docker SDK, or any other container
host. Environment variables (API keys) are read from the real process
environment at runtime, so they're set via the host's secrets/variables UI
rather than a committed `.env` file.

By default the image is built **without** `requirements-full.txt` (no
PyTorch), so it fits comfortably on free/low-memory tiers. In this mode:
- RAG embeddings use the Hugging Face Inference API instead of a local model
  (set `HF_API_TOKEN` — free at huggingface.co/settings/tokens)
- Voice input (Whisper) is disabled; text chat and voice *output* (gTTS)
  still work normally

To include Whisper + local embeddings instead, uncomment the two extra
`RUN`/`COPY` lines in the `Dockerfile` — needs a host with enough RAM for
PyTorch (Hugging Face Spaces' free CPU tier works; most 512MB free web-host
tiers don't).

## API keys — what's required vs. optional

AgriBot is designed to **run immediately with zero keys**, using free local/offline
equivalents, then upgrade module-by-module as you add keys to `backend/.env`:

| Feature | Works without a key? | Key to add for full functionality |
|---|---|---|
| Language detection & translation | ✅ (`langdetect` + `deep-translator`) | — |
| Text-to-speech | ✅ (`gTTS`, free) | — |
| Speech-to-text | ✅ if `requirements-full.txt` is installed (`openai-whisper`, needs `ffmpeg`); disabled otherwise | — |
| RAG embeddings | ✅ locally if `requirements-full.txt` is installed; else via HF's remote API | `HF_API_TOKEN` (free, only needed without `requirements-full.txt`) |
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
<img width="600" height="300" alt="{C77FCD0F-C450-4954-97BC-E537750C2677}" src="https://github.com/user-attachments/assets/6f2f8cb4-5bc2-4eae-8775-116fda02dada" />
<img width="600" height="300" alt="{C111D785-53E8-4680-924F-8F2F785C4123}" src="https://github.com/user-attachments/assets/f42c8bb2-0a3e-40de-97a6-fe67b70bb9b2" />


