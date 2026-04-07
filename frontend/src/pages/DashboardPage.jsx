import { useState, useEffect, useCallback } from "react";
import { RefreshCw, Calendar, AlertCircle } from "lucide-react";
import StatCard from "../components/admin/StatCard";
import BookingsTable from "../components/admin/BookingsTable";
import InquiriesTable from "../components/admin/InquiriesTable";
import LeadsTable from "../components/admin/LeadsTable";
import CallSessionsTable from "../components/admin/CallSessionsTable";
import {
  getAdminStats,
  getBookingsToday,
  getBookingsByDate,
  getReportInquiries,
  getLeads,
  getCallSessions,
} from "../services/api";

const TABS = [
  { id: "bookings_today", label: "Bookings Today" },
  { id: "inquiries",      label: "Report Inquiries" },
  { id: "leads",          label: "Leads" },
  { id: "all_bookings",   label: "All Bookings" },
  { id: "call_sessions",  label: "Call Sessions" },
];

const todayStr = () => new Date().toISOString().split("T")[0];

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("bookings_today");
  const [stats, setStats] = useState(null);
  const [bookingsToday, setBookingsToday] = useState([]);
  const [inquiries, setInquiries] = useState([]);
  const [leads, setLeads] = useState([]);
  const [allBookings, setAllBookings] = useState([]);
  const [callSessions, setCallSessions] = useState([]);
  const [selectedDate, setSelectedDate] = useState(todayStr());
  const [sessionDate, setSessionDate] = useState(todayStr());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const loadAll = useCallback(async () => {
    setError("");
    try {
      const [statsData, todayData, inquiriesData, leadsData] = await Promise.all([
        getAdminStats(),
        getBookingsToday(),
        getReportInquiries("open"),
        getLeads(),
      ]);
      setStats(statsData);
      setBookingsToday(todayData);
      setInquiries(inquiriesData);
      setLeads(leadsData);
      setLastRefreshed(new Date());
    } catch (e) {
      console.error(e);
      setError("Could not load data. Check backend is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadAllBookingsByDate = useCallback(async (date) => {
    try {
      const data = await getBookingsByDate(date);
      setAllBookings(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const loadCallSessions = useCallback(async (date) => {
    try {
      const data = await getCallSessions(date);
      setCallSessions(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(loadAll, 30_000);
    return () => clearInterval(interval);
  }, [loadAll]);

  // Load all-bookings tab data when date changes
  useEffect(() => {
    if (activeTab === "all_bookings") {
      loadAllBookingsByDate(selectedDate);
    }
    if (activeTab === "call_sessions") {
      loadCallSessions(sessionDate);
    }
  }, [activeTab, selectedDate, sessionDate, loadAllBookingsByDate, loadCallSessions]);

  const handleManualRefresh = () => {
    setLoading(true);
    loadAll();
  };

  const formatRefreshed = () => {
    if (!lastRefreshed) return "";
    return lastRefreshed.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── Admin Header ──────────────────────────────────────────────── */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Sun Pathology — Staff Dashboard</h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Sheetal AI Receptionist · Internal Panel
            </p>
          </div>
          <div className="flex items-center gap-4">
            {lastRefreshed && (
              <p className="text-xs text-gray-400 hidden sm:block">
                Last updated: {formatRefreshed()} · Auto-refreshes every 30s
              </p>
            )}
            <button
              onClick={handleManualRefresh}
              disabled={loading}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* ── Error banner ──────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {/* ── Stats bar ──────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <StatCard
            label="Bookings Today"
            value={stats?.bookings_today}
            color="blue"
          />
          <StatCard
            label="Pending"
            value={stats?.bookings_pending}
            color="orange"
            subtext="awaiting confirmation"
          />
          <StatCard
            label="Confirmed"
            value={stats?.bookings_confirmed}
            color="green"
            subtext="team dispatched"
          />
          <StatCard
            label="Open Inquiries"
            value={stats?.open_inquiries}
            color={stats?.open_inquiries > 0 ? "red" : "gray"}
            subtext="call back required"
          />
          <StatCard
            label="New Leads"
            value={stats?.new_leads}
            color={stats?.new_leads > 0 ? "orange" : "gray"}
            subtext="corporate / society"
          />
        </div>

        {/* ── Tab bar ────────────────────────────────────────────────────── */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
          {TABS.map((tab) => {
            // Show badge counts on tabs with urgent items
            let badge = null;
            if (tab.id === "inquiries" && stats?.open_inquiries > 0)
              badge = stats.open_inquiries;
            if (tab.id === "leads" && stats?.new_leads > 0)
              badge = stats.new_leads;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${activeTab === tab.id
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                  }`}
              >
                {tab.label}
                {badge && (
                  <span className="ml-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center leading-none">
                    {badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* ── Tab content ────────────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">

          {/* Bookings Today */}
          {activeTab === "bookings_today" && (
            <>
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-gray-900">Today's Home Collection Bookings</h2>
                  <p className="text-xs text-gray-400 mt-0.5">{bookingsToday.length} booking{bookingsToday.length !== 1 ? "s" : ""}</p>
                </div>
              </div>
              {loading
                ? <LoadingSkeleton rows={4} cols={9} />
                : <BookingsTable bookings={bookingsToday} onRefresh={loadAll} />
              }
            </>
          )}

          {/* Report Inquiries */}
          {activeTab === "inquiries" && (
            <>
              <div className="px-6 py-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Pending Report Inquiries</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  Call these patients back · click "Mark resolved" once done
                </p>
              </div>
              {loading
                ? <LoadingSkeleton rows={3} cols={5} />
                : <InquiriesTable inquiries={inquiries} onRefresh={loadAll} />
              }
            </>
          )}

          {/* Leads */}
          {activeTab === "leads" && (
            <>
              <div className="px-6 py-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Corporate & Society Leads</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  Forward to Dr. Mayank Joshi (9276843433) for follow-up
                </p>
              </div>
              {loading
                ? <LoadingSkeleton rows={3} cols={8} />
                : <LeadsTable leads={leads} />
              }
            </>
          )}

          {/* All Bookings — date filtered */}
          {activeTab === "all_bookings" && (
            <>
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-3">
                <div>
                  <h2 className="font-semibold text-gray-900">All Bookings</h2>
                  <p className="text-xs text-gray-400 mt-0.5">{allBookings.length} booking{allBookings.length !== 1 ? "s" : ""} on selected date</p>
                </div>
                <label className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar size={15} className="text-gray-400" />
                  <input
                    type="date"
                    value={selectedDate}
                    max={todayStr()}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-sun-sky"
                  />
                </label>
              </div>
              <BookingsTable bookings={allBookings} onRefresh={() => loadAllBookingsByDate(selectedDate)} />
            </>
          )}

          {/* Call Sessions */}
          {activeTab === "call_sessions" && (
            <>
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-3">
                <div>
                  <h2 className="font-semibold text-gray-900">Call Transcripts</h2>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {callSessions.length} session{callSessions.length !== 1 ? "s" : ""} · Click a row to expand the transcript
                  </p>
                </div>
                <label className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar size={15} className="text-gray-400" />
                  <input
                    type="date"
                    value={sessionDate}
                    max={todayStr()}
                    onChange={(e) => setSessionDate(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-sun-sky"
                  />
                </label>
              </div>
              <CallSessionsTable sessions={callSessions} />
            </>
          )}

        </div>
      </div>
    </div>
  );
}


// ── Local helper — skeleton loader ──────────────────────────────────────────

function LoadingSkeleton({ rows = 3, cols = 5 }) {
  return (
    <div className="p-6 space-y-3">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={c}
              className="h-4 bg-gray-100 rounded-full animate-pulse flex-1"
              style={{ animationDelay: `${(r * cols + c) * 40}ms` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}