// src/App.jsx

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import VoicePage from "./pages/VoicePage";
import Header from "./components/shared/Header";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-sun-light">
        <Header />
        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/voice" element={<VoicePage />} />
            <Route path="/admin-sp" element={<DashboardPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}