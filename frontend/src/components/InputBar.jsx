import { useState } from "react";
import MicButton from "./MicButton";

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState("");

  const submit = (e) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <form
      onSubmit={submit}
      className="flex items-center gap-2 border-t bg-white px-3 py-3 shrink-0"
    >
      <MicButton disabled={disabled} onTranscribed={(t) => onSend(t)} />
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask about weather, mandi prices, schemes, or crop care..."
        disabled={disabled}
        className="flex-1 rounded-full border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-agri-500 disabled:bg-gray-100"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="w-10 h-10 shrink-0 rounded-full bg-agri-600 text-white flex items-center justify-center hover:bg-agri-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Send"
      >
        ➤
      </button>
    </form>
  );
}
