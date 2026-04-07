// src/services/api.js

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,   // 30s for voice processing
});


// ── Chat ──────────────────────────────────────────────────────────────────

export const sendMessage = async (sessionId, message, languageHint = "") => {
  const response = await api.post("/api/chat", {
    session_id: sessionId,
    message,
    language_hint: languageHint || undefined,
  });
  return response.data;
  // Returns: { session_id, reply, category, language, booking_state, suggested_action }
};


// ── Voice ─────────────────────────────────────────────────────────────────

export const processVoice = async (sessionId, audioBlob, languageHint = "") => {
  const formData = new FormData();
  formData.append("audio", audioBlob, "audio.webm");
  formData.append("session_id", sessionId);
  if (languageHint) formData.append("language_hint", languageHint);

  const response = await api.post("/api/voice/process", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
  // Returns: { session_id, transcript, reply_text, language, category, audio_base64 }
};


// ── Health check ──────────────────────────────────────────────────────────

export const checkHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

// ── Admin ──────────────────────────────────────────────────────────────────

export const getAdminStats = () =>
  api.get("/api/admin/stats").then(r => r.data);

export const getBookingsToday = () =>
  api.get("/api/admin/bookings/today").then(r => r.data);

export const getBookingsByDate = (date) =>
  api.get(`/api/admin/bookings?date=${date}`).then(r => r.data);

export const updateBookingStatus = (bookingId, status) =>
  api.patch(`/api/admin/bookings/${bookingId}/status`, { status }).then(r => r.data);

export const getReportInquiries = (status = "open") =>
  api.get(`/api/admin/report-inquiries?status=${status}`).then(r => r.data);

export const resolveInquiry = (inquiryId) =>
  api.patch(`/api/admin/report-inquiries/${inquiryId}/resolve`).then(r => r.data);

export const getLeads = (status = null) =>
  api.get(`/api/admin/leads${status ? `?status=${status}` : ""}`).then(r => r.data);

export const updateLeadStatus = (leadId, status) =>
  api.patch(`/api/admin/leads/${leadId}/status`, { status }).then(r => r.data);

export const getCallSessions = (date = null, limit = 50) =>
  api.get(`/api/admin/call-sessions?limit=${limit}${date ? `&date=${date}` : ""}`).then(r => r.data);