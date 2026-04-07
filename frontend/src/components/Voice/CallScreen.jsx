// src/components/Voice/CallScreen.jsx

import { useEffect, useRef } from "react";
import { Phone, PhoneOff } from "lucide-react";
import SheetalAvatar from "../shared/SheetalAvatar";
import WaveformVisualizer from "./WaveformVisualizer";
import CallTimer from "./CallTimer";
import LanguageBadge from "../shared/LanguageBadge";

const STATE_LABELS = {
  idle:      "Tap to call Sheetal",
  ringing:   "Calling Sheetal...",
  connected: "Connected",
  listening: "Listening...",
  thinking:  "Sheetal is thinking...",
  speaking:  "Sheetal is speaking",
  ended:     "Call ended",
  error:     "Call failed",
};

function formatTime(date) {
  if (!date) return "";
  return new Date(date).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function CallScreen({
  callState,
  transcript,
  sheetalText,
  messages = [],
  language,
  callDuration,
  error,
  onStartCall,
  onEndCall,
}) {
  const isActive  = ["connected", "listening", "thinking", "speaking"].includes(callState);
  const isIdle    = callState === "idle" || callState === "ended" || callState === "error";
  const isRinging = callState === "ringing";
  const hasLog    = messages.length > 0;

  // Auto-scroll transcript log to bottom as new messages arrive
  const logEndRef = useRef(null);
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col items-center justify-between h-full px-6 py-8 max-w-sm mx-auto w-full">

      {/* ── Top: Avatar + status ───────────────────────────────────── */}
      <div className="flex flex-col items-center gap-4 mt-8">
        <SheetalAvatar size={96} speaking={callState === "speaking"} />

        <div className="text-center">
          <p className="text-xl font-semibold text-sun-blue">Sheetal</p>
          <p className="text-sm text-gray-400">Sun Pathology AI Receptionist</p>
          {language && isActive && (
            <div className="mt-2 flex justify-center">
              <LanguageBadge language={language} />
            </div>
          )}
        </div>

        {/* Call timer */}
        {isActive && <CallTimer seconds={callDuration} />}

        {/* Status label */}
        <div className="flex items-center gap-2">
          {callState === "listening" && (
            <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
          )}
          {callState === "speaking" && (
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          )}
          {callState === "thinking" && (
            <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
          )}
          <span className="text-sm text-gray-500 font-medium">
            {STATE_LABELS[callState] || callState}
          </span>
        </div>
      </div>

      {/* ── Middle: Waveform + transcript log ──────────────────────── */}
      <div className="w-full flex flex-col items-center gap-3 flex-1 overflow-hidden mt-4">
        <WaveformVisualizer active={callState === "listening" || callState === "speaking"} />

        {/* Full conversation log — scrollable */}
        {hasLog && (
          <div className="w-full flex-1 overflow-y-auto space-y-2 pr-1 max-h-64">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${msg.role === "user" ? "items-start" : "items-end"}`}
              >
                <p className="text-[10px] text-gray-400 mb-0.5 px-1">
                  {msg.role === "user" ? "You" : "Sheetal"}
                  {msg.time && (
                    <span className="ml-1 opacity-60">{formatTime(msg.time)}</span>
                  )}
                </p>
                <div
                  className={`rounded-2xl px-3.5 py-2 max-w-[90%] shadow-sm ${
                    msg.role === "user"
                      ? "bg-white border border-gray-100 text-gray-700"
                      : "bg-sun-blue text-white"
                  }`}
                >
                  <p className="text-sm leading-snug">{msg.text}</p>
                </div>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}

        {/* Empty state hints */}
        {!hasLog && callState === "listening" && (
          <p className="text-xs text-gray-400 text-center">
            Speak naturally — Sheetal is listening
          </p>
        )}
        {!hasLog && callState === "speaking" && (
          <p className="text-xs text-gray-400 text-center">
            You can speak to interrupt Sheetal
          </p>
        )}
        {!hasLog && callState === "connected" && (
          <p className="text-xs text-gray-400 text-center">
            Connecting you to Sheetal…
          </p>
        )}

        {/* Interrupt hint when log exists */}
        {hasLog && callState === "speaking" && (
          <p className="text-xs text-gray-400 text-center">
            You can speak to interrupt Sheetal
          </p>
        )}

        {/* Error */}
        {error && (
          <div className="w-full bg-red-50 border border-red-200 rounded-xl px-4 py-2">
            <p className="text-sm text-red-600 text-center">{error}</p>
          </div>
        )}
      </div>

      {/* ── Bottom: Call button ────────────────────────────────────── */}
      <div className="flex flex-col items-center gap-3 mb-4 mt-4">
        {isIdle || isRinging ? (
          <button
            onClick={onStartCall}
            disabled={isRinging}
            className={`w-20 h-20 rounded-full flex items-center justify-center text-white shadow-xl transition-all
              ${isRinging
                ? "bg-green-400 animate-pulse cursor-wait"
                : "bg-green-500 hover:bg-green-600 active:scale-95"
              }`}
          >
            <Phone size={32} />
          </button>
        ) : (
          <button
            onClick={onEndCall}
            className="w-20 h-20 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center text-white shadow-xl transition-all active:scale-95"
          >
            <PhoneOff size={32} />
          </button>
        )}

        <p className="text-xs text-gray-400">
          {isIdle ? "Tap to start call" : isActive ? "Tap to end call" : ""}
        </p>
      </div>
    </div>
  );
}