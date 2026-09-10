import { useState } from "react";
import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import { sendChatMessage } from "./services/api";

let nextId = 1;

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (text) => {
    const userMessage = { id: nextId++, sender: "user", text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const data = await sendChatMessage(text);
      const botMessage = {
        id: nextId++,
        sender: "bot",
        text: data.response,
        responseEn: data.response_en,
        audioUrl: data.audio_url,
        intent: data.intent,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error("Chat request failed:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: nextId++,
          sender: "bot",
          text: "Sorry, I couldn't reach the AgriBot server. Please make sure the backend is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <ChatWindow messages={messages} loading={loading} />
      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
