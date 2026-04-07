// src/components/Admin/InquiriesTable.jsx

import { useState } from "react";
import { Phone, CheckCheck } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { resolveInquiry } from "../../services/api";

function InquiryRow({ inquiry, onResolved }) {
  const [loading, setLoading] = useState(false);

  const handleResolve = async () => {
    setLoading(true);
    try {
      await resolveInquiry(inquiry.id);
      onResolved(inquiry.id);
    } catch (e) {
      console.error(e);
      alert("Failed to resolve. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const time = inquiry.created_at
    ? new Date(inquiry.created_at).toLocaleString("en-IN", {
        day: "2-digit", month: "short",
        hour: "2-digit", minute: "2-digit",
      })
    : "—";

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3 text-sm font-medium text-gray-900">{inquiry.patient_name || "—"}</td>
      <td className="px-4 py-3">
        <a
          href={`tel:${inquiry.mobile_number}`}
          className="flex items-center gap-1.5 text-sm font-mono text-blue-600 hover:text-blue-800"
        >
          <Phone size={13} />
          {inquiry.mobile_number || "—"}
        </a>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">{time}</td>
      <td className="px-4 py-3">
        <StatusBadge status={inquiry.status} />
      </td>
      <td className="px-4 py-3">
        {inquiry.status === "open" && (
          <button
            onClick={handleResolve}
            disabled={loading}
            className="flex items-center gap-1 text-xs text-green-600 border border-green-200 rounded-lg px-2 py-1 hover:bg-green-50 disabled:opacity-40 transition-colors"
          >
            <CheckCheck size={13} />
            {loading ? "Saving..." : "Mark resolved"}
          </button>
        )}
      </td>
    </tr>
  );
}

export default function InquiriesTable({ inquiries, onRefresh }) {
  const [localInquiries, setLocalInquiries] = useState(inquiries);

  if (inquiries !== localInquiries && inquiries.length !== localInquiries.length) {
    setLocalInquiries(inquiries);
  }

  const handleResolved = (id) => {
    setLocalInquiries(prev => prev.filter(i => i.id !== id));
  };

  if (!localInquiries.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-sm">No open inquiries — all clear! ✓</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b-2 border-gray-100">
            {["Patient Name", "Mobile", "Received At", "Status", ""].map(h => (
              <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {localInquiries.map(i => (
            <InquiryRow key={i.id} inquiry={i} onResolved={handleResolved} />
          ))}
        </tbody>
      </table>
    </div>
  );
}