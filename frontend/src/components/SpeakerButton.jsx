import { useRef, useState } from "react";

// Module-level registry so only one audio element plays across the whole app.
let currentAudio = null;

export default function SpeakerButton({ audioUrl }) {
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);

  if (!audioUrl) return null;

  const handleClick = () => {
    if (!audioRef.current) {
      audioRef.current = new Audio(audioUrl);
      audioRef.current.onended = () => setPlaying(false);
    }

    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
      return;
    }

    if (currentAudio && currentAudio !== audioRef.current) {
      currentAudio.pause();
    }
    currentAudio = audioRef.current;
    audioRef.current.play();
    setPlaying(true);
  };

  return (
    <button
      onClick={handleClick}
      title={playing ? "Pause audio" : "Play audio"}
      className="inline-flex items-center justify-center w-7 h-7 rounded-full hover:bg-black/10 transition"
    >
      {playing ? "⏸️" : "🔊"}
    </button>
  );
}
