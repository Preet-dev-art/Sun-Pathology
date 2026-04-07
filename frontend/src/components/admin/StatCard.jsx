// src/components/Admin/StatCard.jsx

export default function StatCard({ label, value, color = "blue", subtext = "" }) {
  const colors = {
    blue:   "bg-blue-50  text-blue-700  border-blue-200",
    green:  "bg-green-50 text-green-700 border-green-200",
    orange: "bg-orange-50 text-orange-700 border-orange-200",
    red:    "bg-red-50   text-red-700   border-red-200",
    gray:   "bg-gray-50  text-gray-700  border-gray-200",
  };

  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <p className="text-sm font-medium opacity-70">{label}</p>
      <p className="text-3xl font-bold mt-1">{value ?? "—"}</p>
      {subtext && <p className="text-xs mt-1 opacity-60">{subtext}</p>}
    </div>
  );
}