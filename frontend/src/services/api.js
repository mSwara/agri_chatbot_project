const BASE_URL = "/api";

async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  return res.json();
}

export function sendChatMessage(message, sessionId = "default") {
  return postJSON("/chat", { message, session_id: sessionId });
}

export function translateToEnglish(text) {
  return postJSON("/translate-to-english", { text });
}

export function translateFromEnglish(text, targetLanguage) {
  return postJSON("/translate-from-english", { text, target_language: targetLanguage });
}

export function detectLanguage(text) {
  return postJSON("/detect-language", { text });
}

export async function speechToText(blob) {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  const res = await fetch(`${BASE_URL}/speech-to-text`, { method: "POST", body: form });
  if (!res.ok) throw new Error("speech-to-text failed");
  return res.json();
}

export function textToSpeech(text, language = "en") {
  return postJSON("/text-to-speech", { text, language });
}

export const SUPPORTED_LANGUAGES = [
  { code: "en", name: "English" },
  { code: "hi", name: "Hindi" },
  { code: "mr", name: "Marathi" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "kn", name: "Kannada" },
  { code: "gu", name: "Gujarati" },
  { code: "bn", name: "Bengali" },
  { code: "pa", name: "Punjabi" },
  { code: "ml", name: "Malayalam" },
];
