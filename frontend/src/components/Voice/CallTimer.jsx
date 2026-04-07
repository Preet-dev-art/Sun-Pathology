// src/components/Voice/CallTimer.jsx

export default function CallTimer({ seconds }) {
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  return (
    <span className="text-sm font-mono text-gray-400 tabular-nums">
      {mins}:{secs}
    </span>
  );
}