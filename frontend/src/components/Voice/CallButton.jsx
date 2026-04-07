// src/components/Voice/CallButton.jsx

import { Mic, MicOff, Phone, PhoneOff } from "lucide-react";

const CONFIG = {
  idle: {
    icon: <Mic size={32} />,
    label: "Tap to speak",
    bg: "bg-sun-blue hover:bg-sun-sky",
    ring: "",
  },
  listening: {
    icon: <MicOff size={32} />,
    label: "Listening... tap to stop",
    bg: "bg-red-500 hover:bg-red-600",
    ring: "ring-4 ring-red-300 animate-pulse",
  },
  processing: {
    icon: <Phone size={32} />,
    label: "Processing...",
    bg: "bg-gray-400 cursor-wait",
    ring: "",
  },
  speaking: {
    icon: <PhoneOff size={32} />,
    label: "Sheetal is speaking...",
    bg: "bg-green-500",
    ring: "ring-4 ring-green-300 animate-pulse",
  },
  error: {
    icon: <Mic size={32} />,
    label: "Tap to retry",
    bg: "bg-sun-blue hover:bg-sun-sky",
    ring: "",
  },
};

export default function CallButton({ status, onClick }) {
  const cfg = CONFIG[status] || CONFIG.idle;
  const isDisabled = status === "processing" || status === "speaking";

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={onClick}
        disabled={isDisabled}
        className={`w-24 h-24 rounded-full text-white flex items-center justify-center transition-all
          ${cfg.bg} ${cfg.ring} shadow-xl disabled:opacity-60`}
      >
        {cfg.icon}
      </button>
      <p className="text-sm text-gray-500 font-medium">{cfg.label}</p>
    </div>
  );
}