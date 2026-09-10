import { useRef, useState } from "react";
import { speechToText } from "../services/api";

export default function MicButton({ onTranscribed, disabled }) {
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setBusy(true);
        try {
          const { text } = await speechToText(blob);
          if (text) onTranscribed(text);
        } catch (err) {
          console.error("Speech-to-text failed:", err);
        } finally {
          setBusy(false);
        }
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch (err) {
      console.error("Microphone access denied or unavailable:", err);
      alert("Couldn't access your microphone. Please allow mic permission and try again.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const handleClick = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || busy}
      title={recording ? "Stop recording" : "Record voice message"}
      className={`w-10 h-10 shrink-0 rounded-full flex items-center justify-center text-lg transition
        ${recording ? "bg-red-500 text-white animate-pulse" : "bg-agri-100 text-agri-700 hover:bg-agri-200"}
        disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {busy ? "⏳" : recording ? "⏹️" : "🎤"}
    </button>
  );
}
