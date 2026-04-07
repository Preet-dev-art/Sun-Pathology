// src/components/shared/Header.jsx

import { Link, useLocation } from "react-router-dom";
import { MessageCircle, Phone } from "lucide-react";

export default function Header() {
  const { pathname } = useLocation();

  return (
    <header className="bg-sun-blue text-white shadow-lg">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo + Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
            <span className="text-sun-blue font-bold text-sm">SP</span>
          </div>
          <div>
            <p className="font-semibold text-sm leading-none">Sun Pathology</p>
            <p className="text-xs text-blue-200 leading-none mt-0.5">Sheetal — AI Receptionist</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex gap-2">
          <Link
            to="/chat"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors
              ${pathname === "/chat"
                ? "bg-white text-sun-blue"
                : "text-blue-200 hover:text-white hover:bg-white/10"
              }`}
          >
            <MessageCircle size={15} />
            Chat
          </Link>
          <Link
            to="/voice"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors
              ${pathname === "/voice"
                ? "bg-white text-sun-blue"
                : "text-blue-200 hover:text-white hover:bg-white/10"
              }`}
          >
            <Phone size={15} />
            Voice
          </Link>
        </nav>
      </div>
    </header>
  );
}