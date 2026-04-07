// src/hooks/useSession.js

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";

export function useSession() {
  const [sessionId, setSessionId] = useState(() => {
    const stored = localStorage.getItem("sheetal_session_id");
    if (stored) return stored;
    const newId = uuidv4();
    localStorage.setItem("sheetal_session_id", newId);
    return newId;
  });

  const resetSession = () => {
    const newId = uuidv4();
    localStorage.setItem("sheetal_session_id", newId);
    setSessionId(newId);
  };

  return { sessionId, resetSession };
}