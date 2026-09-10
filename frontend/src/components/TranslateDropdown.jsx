import { useState } from "react";
import { SUPPORTED_LANGUAGES } from "../services/api";

export default function TranslateDropdown({ onSelectLanguage }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-xs px-2 py-1 rounded-full border border-agri-600 text-agri-700 hover:bg-agri-50 transition"
      >
        🌐 Translate
      </button>
      {open && (
        <div className="absolute z-10 mt-1 w-40 bg-white border rounded-lg shadow-lg max-h-56 overflow-y-auto">
          {SUPPORTED_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                onSelectLanguage(lang.code);
                setOpen(false);
              }}
              className="block w-full text-left px-3 py-1.5 text-sm hover:bg-agri-50"
            >
              {lang.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
