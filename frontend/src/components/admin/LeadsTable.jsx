// src/components/Admin/LeadsTable.jsx

import { useState } from "react";
import { Phone, ChevronDown } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { updateLeadStatus } from "../../services/api";

const NEXT_STATUSES = {
  new:       ["contacted", "closed"],
  contacted: ["converted", "closed"],
  converted: [],
  closed:    [],
};

function LeadRow({ lead, onStatusChange }) {
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const nextStatuses = NEXT_STATUSES[lead.status] || [];

  const handleAction = async (newStatus) => {
    setLoading(true);
    setOpen(false);
    try {
      await updateLeadStatus(lead.id, newStatus);
      onStatusChange(lead.id, newStatus);
    } catch (e) {
      console.error(e);
      alert("Failed to update. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const time = lead.created_at
    ? new Date(lead.created_at).toLocaleString("en-IN", {
        day: "2-digit", month: "short",
        hour: "2-digit", minute: "2-digit",
      })
    : "—";

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3 text-sm font-medium text-gray-900">{lead.caller_name || "—"}</td>
      <td className="px-4 py-3">
        <a
          href={`tel:${lead.mobile_number}`}
          className="flex items-center gap-1.5 text-sm font-mono text-blue-600 hover:text-blue-800"
        >
          <Phone size={13} />
          {lead.mobile_number || "—"}
        </a>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700">{lead.organization_name || "—"}</td>
      <td className="px-4 py-3">
        <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 capitalize">
          {lead.inquiry_type || "general"}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500 max-w-xs">
        <p className="truncate">{lead.notes || "—"}</p>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400">{time}</td>
      <td className="px-4 py-3">
        <StatusBadge status={lead.status} />
      </td>
      <td className="px-4 py-3">
        {nextStatuses.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setOpen(!open)}
              disabled={loading}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg px-2 py-1 hover:bg-gray-50 disabled:opacity-40"
            >
              Update <ChevronDown size={12} />
            </button>
            {open && (
              <div className="absolute right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-10 min-w-[120px] overflow-hidden">
                {nextStatuses.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleAction(s)}
                    className="block w-full text-left px-3 py-2 text-xs hover:bg-gray-50 text-gray-700 capitalize"
                  >
                    Mark {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

export default function LeadsTable({ leads }) {
  const [localLeads, setLocalLeads] = useState(leads);

  if (leads !== localLeads && leads.length !== localLeads.length) {
    setLocalLeads(leads);
  }

  const handleStatusChange = (id, newStatus) => {
    setLocalLeads(prev =>
      prev.map(l => l.id === id ? { ...l, status: newStatus } : l)
    );
  };

  if (!localLeads.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-sm">No leads found</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b-2 border-gray-100">
            {["Caller", "Mobile", "Organisation", "Type", "Notes", "Received At", "Status", ""].map(h => (
              <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {localLeads.map(l => (
            <LeadRow key={l.id} lead={l} onStatusChange={handleStatusChange} />
          ))}
        </tbody>
      </table>
    </div>
  );
}