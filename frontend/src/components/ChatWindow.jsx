import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import TranslateDropdown from "./TranslateDropdown";
import { translateFromEnglish } from "../services/api";

const GREETING_EN =
  "Namaste! I'm AgriBot 🌾 — ask me about weather, mandi prices, government schemes, or crop care, by typing or using the mic.";

export default function ChatWindow({ messages, loading }) {
  const [greeting, setGreeting] = useState(GREETING_EN);
  const [hovering, setHovering] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleGreetingTranslate = async (langCode) => {
    if (langCode === "en") {
      setGreeting(GREETING_EN);
      return;
    }
    try {
      const { translated_text } = await translateFromEnglish(GREETING_EN, langCode);
      setGreeting(translated_text);
    } catch (err) {
      console.error("Greeting translation failed:", err);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 bg-[#f4f7f2]">
      <div
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
        className="flex justify-start mb-3"
      >
        <div className="max-w-[80%] rounded-2xl rounded-bl-sm bg-agri-100 text-agri-800 px-4 py-2 shadow-sm text-sm">
          <p>{greeting}</p>
          <div className={`mt-1.5 transition-opacity ${hovering ? "opacity-100" : "opacity-0"}`}>
            <TranslateDropdown onSelectLanguage={handleGreetingTranslate} />
          </div>
        </div>
      </div>

      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}

      {loading && (
        <div className="flex justify-start mb-3">
          <div className="bg-gray-200 text-gray-500 rounded-2xl rounded-bl-sm px-4 py-2 text-sm">
            AgriBot is thinking…
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
