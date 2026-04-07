// src/components/admin/CallSessionsTable.jsx

import { useState } from "react";
import { ChevronDown, ChevronRight, MessageSquare, Clock, Globe } from "lucide-react";

const LANG_LABELS = { hi: "Hindi", gu: "Gujarati", en: "English" };

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-IN", {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

/** Single expandable row for one call session */
function SessionRow({ session }) {
  const [expanded, setExpanded] = useState(false);
  const messages = session.messages || [];
  const userMsgs = messages.filter((m) => m.role === "user");
  const lang = LANG_LABELS[session.language] || session.language || "—";

  return (
    <>
      {/* Summary row */}
      <tr
        className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="px-4 py-3 text-gray-400">
          {expanded
            ? <ChevronDown size={16} />
            : <ChevronRight size={16} />
          }
        </td>
        <td className="px-4 py-3 text-xs text-gray-500 font-mono">
          {session.session_id?.slice(0, 8)}…
        </td>
        <td className="px-4 py-3 text-sm text-gray-700">{formatDate(session.created_at)}</td>
        <td className="px-4 py-3">
          <span className="flex items-center gap-1 text-sm text-gray-600">
            <Globe size={13} className="text-gray-400" /> {lang}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {messages.length} turns ({userMsgs.length} from patient)
        </td>
        <td className="px-4 py-3 text-xs text-gray-500">
          {session.query_category || "—"}
        </td>
      </tr>

      {/* Expanded transcript */}
      {expanded && (
        <tr>
          <td colSpan={6} className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            {messages.length === 0 ? (
              <p className="text-sm text-gray-400 italic">No messages recorded.</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-3 ${
                      msg.role === "assistant" ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    <div
                      className={`rounded-xl px-3 py-2 max-w-[75%] text-sm shadow-sm ${
                        msg.role === "user"
                          ? "bg-white border border-gray-200 text-gray-700"
                          : "bg-blue-600 text-white"
                      }`}
                    >
                      <p className="text-[10px] font-semibold mb-0.5 opacity-70">
                        {msg.role === "user" ? "Patient" : "Sheetal"}
                        {msg.timestamp && (
                          <span className="ml-1 font-normal opacity-60">
                            {formatTime(msg.timestamp)}
                          </span>
                        )}
                      </p>
                      <p className="leading-snug">{msg.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

export default function CallSessionsTable({ sessions = [] }) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
        <MessageSquare size={36} strokeWidth={1.5} />
        <p className="text-sm">No call sessions found for this date.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 w-8" />
            <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Session
            </th>
            <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <Clock size={12} className="inline mr-1" />Started
            </th>
            <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Language
            </th>
            <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Messages
            </th>
            <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Category
            </th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((s) => (
            <SessionRow key={s.id || s.session_id} session={s} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
