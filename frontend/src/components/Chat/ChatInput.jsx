// src/components/Chat/ChatInput.jsx

import { useState } from "react";
import { Send } from "lucide-react";

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-end gap-2 p-4 bg-white border-t border-gray-100">
      <textarea
        className="flex-1 resize-none rounded-xl border border-gray-200 px-4 py-2.5 text-sm text-gray-800
          focus:outline-none focus:ring-2 focus:ring-sun-sky focus:border-transparent
          placeholder:text-gray-400 max-h-32 leading-relaxed"
        placeholder="Type in English, हिंदी, or ગુજરાતી..."
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        style={{ minHeight: "44px" }}
      />
      <button
        onClick={handleSubmit}
        disabled={!text.trim() || disabled}
        className="w-11 h-11 rounded-xl bg-sun-blue text-white flex items-center justify-center
          hover:bg-sun-sky transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
      >
        <Send size={18} />
      </button>
    </div>
  );
}