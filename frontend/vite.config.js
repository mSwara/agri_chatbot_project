import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In production, FastAPI serves this app's built files itself, so the
// frontend calls the backend at the same origin with no prefix (see
// src/services/api.js). In dev, we proxy those same exact paths straight
// to the backend on :8000 so the code doesn't need to know the difference.
const BACKEND_PATHS = [
  "/chat",
  "/translate-to-english",
  "/translate-from-english",
  "/detect-language",
  "/detect-intent",
  "/get-weather",
  "/get-mandi-prices",
  "/get-scheme-info",
  "/get-agriculture-info",
  "/speech-to-text",
  "/text-to-speech",
  "/static",
];

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      BACKEND_PATHS.map((path) => [path, { target: "http://localhost:8000", changeOrigin: true }])
    ),
  },
});
