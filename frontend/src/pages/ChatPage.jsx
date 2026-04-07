// src/pages/ChatPage.jsx

import { useState, useRef, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { useSession } from "../hooks/useSession";
import { sendMessage } from "../services/api";
import ChatBubble from "../components/Chat/ChatBubble";
import ChatInput from "../components/Chat/ChatInput";
import SuggestedActions from "../components/Chat/SuggestedActions";
import LoadingDots from "../components/shared/LoadingDots";

const WELCOME = {
  role: "assistant",
  content: "Namaste! 🙏 I'm Sheetal, your AI receptionist at Sun Pathology. How can I help you today?\n\nYou can ask me about test prices, home sample collection, report status, or anything about our lab.",
  timestamp: new Date().toISOString(),
  language: "en",
};

export default function ChatPage() {
  const { sessionId, resetSession } = useSession();
  const [messages, setMessages] = useState([WELCOME]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text) => {
    setShowSuggestions(false);

    // Optimistic user message
    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendMessage(sessionId, text);

      const assistantMsg = {
        role: "assistant",
        content: data.reply,
        timestamp: new Date().toISOString(),
        language: data.language,
        category: data.category,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I'm sorry, something went wrong. Please try again or call us at 079-67006700.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    resetSession();
    setMessages([WELCOME]);
    setShowSuggestions(true);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] max-w-2xl mx-auto w-full">

      {/* Chat header bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-gray-500">Sheetal is online</span>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-sun-blue transition-colors"
        >
          <RefreshCw size={13} />
          New conversation
        </button>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {messages.map((msg, i) => (
          <ChatBubble key={i} message={msg} />
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-8 h-8 rounded-full bg-sun-blue text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-1">
              SH
            </div>
            <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-100">
              <LoadingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick suggestions (only on fresh session) */}
      {showSuggestions && !loading && (
        <SuggestedActions onSelect={handleSend} disabled={loading} />
      )}

      {/* Input bar */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}