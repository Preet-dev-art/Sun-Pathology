// src/components/Admin/StatusBadge.jsx

const STYLES = {
  // Booking statuses
  pending:    "bg-yellow-100 text-yellow-700",
  confirmed:  "bg-blue-100   text-blue-700",
  completed:  "bg-green-100  text-green-700",
  cancelled:  "bg-red-100    text-red-700",
  // Inquiry statuses
  open:       "bg-red-100    text-red-700",
  resolved:   "bg-green-100  text-green-700",
  // Lead statuses
  new:        "bg-purple-100 text-purple-700",
  contacted:  "bg-blue-100   text-blue-700",
  converted:  "bg-green-100  text-green-700",
  closed:     "bg-gray-100   text-gray-600",
};

export default function StatusBadge({ status }) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${STYLES[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}