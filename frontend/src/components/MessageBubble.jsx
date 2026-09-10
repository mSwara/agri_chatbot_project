import { useState } from "react";
import SpeakerButton from "./SpeakerButton";

export default function MessageBubble({ message }) {
  const isUser = message.sender === "user";
  const [showEnglish, setShowEnglish] = useState(false);

  const displayText = showEnglish && message.responseEn ? message.responseEn : message.text;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2 shadow-sm text-sm whitespace-pre-wrap
          ${isUser ? "bg-agri-500 text-white rounded-br-sm" : "bg-gray-200 text-gray-800 rounded-bl-sm"}`}
      >
        <p>{displayText}</p>
        {!isUser && (
          <div className="flex items-center gap-2 mt-1.5">
            <SpeakerButton audioUrl={message.audioUrl} />
            {message.responseEn && (
              <button
                onClick={() => setShowEnglish((s) => !s)}
                className="text-xs underline text-gray-600 hover:text-gray-900"
              >
                {showEnglish ? "Show original" : "Translate to English"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
