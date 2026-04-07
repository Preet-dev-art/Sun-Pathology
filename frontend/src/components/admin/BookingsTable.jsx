// src/components/Admin/BookingsTable.jsx

import { useState } from "react";
import { CheckCircle, Truck, XCircle, ChevronDown } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { updateBookingStatus } from "../../services/api";

const STATUS_ACTIONS = {
  pending:   [{ label: "Confirm",  value: "confirmed", icon: CheckCircle, color: "text-blue-600"  },
              { label: "Cancel",   value: "cancelled", icon: XCircle,     color: "text-red-500"   }],
  confirmed: [{ label: "Complete", value: "completed", icon: Truck,       color: "text-green-600" },
              { label: "Cancel",   value: "cancelled", icon: XCircle,     color: "text-red-500"   }],
  completed: [],
  cancelled: [],
};

function BookingRow({ booking, onStatusChange }) {
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const actions = STATUS_ACTIONS[booking.status] || [];

  const handleAction = async (newStatus) => {
    setLoading(true);
    setOpen(false);
    try {
      await updateBookingStatus(booking.id, newStatus);
      onStatusChange(booking.id, newStatus);
    } catch (e) {
      console.error(e);
      alert("Failed to update. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const time = booking.created_at
    ? new Date(booking.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
    : "—";

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3 text-sm font-medium text-gray-900">{booking.patient_name || "—"}</td>
      <td className="px-4 py-3 text-sm text-gray-600 font-mono">{booking.mobile_number || "—"}</td>
      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs">
        <p className="truncate">{booking.address || "—"}</p>
        {booking.landmark && <p className="text-xs text-gray-400 truncate">Near: {booking.landmark}</p>}
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">{booking.time_slot || "—"}</td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {booking.tests_requested?.length
          ? booking.tests_requested.join(", ")
          : "Not specified"}
      </td>
      <td className="px-4 py-3 text-sm text-right">
        <p className="font-semibold text-gray-900">₹{booking.total_payable ?? "—"}</p>
        {booking.home_collection_charge > 0 && (
          <p className="text-xs text-gray-400">incl. ₹{booking.home_collection_charge} charge</p>
        )}
        {booking.home_collection_charge === 0 && (
          <p className="text-xs text-green-500">Free collection</p>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-400">{time}</td>
      <td className="px-4 py-3">
        <StatusBadge status={booking.status} />
      </td>
      <td className="px-4 py-3">
        {actions.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setOpen(!open)}
              disabled={loading}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg px-2 py-1 hover:bg-gray-50 disabled:opacity-40"
            >
              Action <ChevronDown size={12} />
            </button>
            {open && (
              <div className="absolute right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-10 min-w-[130px] overflow-hidden">
                {actions.map((a) => (
                  <button
                    key={a.value}
                    onClick={() => handleAction(a.value)}
                    className={`flex items-center gap-2 w-full px-3 py-2 text-xs hover:bg-gray-50 ${a.color}`}
                  >
                    <a.icon size={13} />
                    {a.label}
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

export default function BookingsTable({ bookings, onRefresh }) {
  const [localBookings, setLocalBookings] = useState(bookings);

  // Sync when parent refreshes data
  if (bookings !== localBookings && bookings.length !== localBookings.length) {
    setLocalBookings(bookings);
  }

  const handleStatusChange = (id, newStatus) => {
    setLocalBookings(prev =>
      prev.map(b => b.id === id ? { ...b, status: newStatus } : b)
    );
  };

  if (!localBookings.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-sm">No bookings found</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b-2 border-gray-100">
            {["Patient", "Mobile", "Address", "Time Slot", "Tests", "Amount", "Booked At", "Status", ""].map(h => (
              <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {localBookings.map(b => (
            <BookingRow key={b.id} booking={b} onStatusChange={handleStatusChange} />
          ))}
        </tbody>
      </table>
    </div>
  );
}