// src/components/Chat/ChatBubble.jsx

import LanguageBadge from "../shared/LanguageBadge";

export default function ChatBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : "flex-row"} mb-3`}>

      {/* Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-sun-blue text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-1">
          SH
        </div>
      )}

      {/* Bubble */}
      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
            ${isUser
              ? "bg-sun-blue text-white rounded-tr-sm"
              : "bg-white text-gray-800 shadow-sm rounded-tl-sm border border-gray-100"
            }`}
        >
          {message.content}
        </div>

        {/* Metadata row */}
        <div className={`flex items-center gap-2 px-1 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
          <span className="text-xs text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {message.language && <LanguageBadge language={message.language} />}
        </div>
      </div>
    </div>
  );
}