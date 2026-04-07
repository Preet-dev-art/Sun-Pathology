// src/components/Chat/SuggestedActions.jsx

const SUGGESTIONS = [
  { label: "CBC price", value: "CBC ka price kya hai?" },
  { label: "Home collection", value: "Ghar pe sample collection chahiye" },
  { label: "Report status", value: "Meri report kab aayegi?" },
  { label: "Timings", value: "Lab ki timing kya hai?" },
  { label: "Sunday open?", value: "Sunday ko lab khuli hai?" },
];

export default function SuggestedActions({ onSelect, disabled }) {
  return (
    <div className="flex gap-2 flex-wrap px-4 pb-2">
      {SUGGESTIONS.map((s) => (
        <button
          key={s.value}
          onClick={() => onSelect(s.value)}
          disabled={disabled}
          className="px-3 py-1.5 rounded-full text-xs font-medium bg-white border border-sun-sky
            text-sun-sky hover:bg-sun-sky hover:text-white transition-colors
            disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}