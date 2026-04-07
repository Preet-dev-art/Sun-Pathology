# Phase 7 — Implementation Plan
## Simulated Real Phone Call (Based on Your Actual Code)

**Status of your uploaded files:**
- `call.py` ✅ complete
- `call_manager.py` ✅ complete
- `useCallSession.js` ✅ complete
- `VoicePage.jsx` ✅ complete
- `CallScreen.jsx` ✅ complete
- `CallButton.jsx` ✅ exists (Phase 5 fallback)
- `db_service.py` ✅ complete (already has `get_call_sessions`)
- `api.js` ✅ complete (already has `getCallSessions`)
- `voice.py` ✅ complete (kept as-is)

**What this plan tells you to do:** The files above are written. You now need to place them correctly, create two missing files, add two missing endpoints, and wire everything together.

---

## Step 1 — Place Backend Files

Copy your uploaded files into the project at exactly these paths:

```
backend/app/
├── routers/
│   └── call.py                      ← place here (your uploaded call.py)
├── services/
│   └── call_manager.py              ← place here (your uploaded call_manager.py)
```

`db_service.py` already exists from Phase 2 — your uploaded version is the updated one with `get_call_sessions` added at the bottom. Replace the existing file with this version.

---

## Step 2 — Register the Call Router in `main.py`

Open `app/main.py` and make two changes:

**Change 1 — add the import:**
```python
# Before (Phase 4 state):
from app.routers import chat, voice

# After:
from app.routers import chat, voice, call
```

**Change 2 — register the router:**
```python
# Add this line after the existing voice router line:
app.include_router(call.router)
```

Your `main.py` router section should look like this when done:
```python
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(call.router)    # ← new
```

---

## Step 3 — Add `/call-sessions` to `admin.py`

Your `api.js` calls `GET /api/admin/call-sessions` and your `db_service.py` already has `get_call_sessions()`. The only missing piece is the actual route in `admin.py`.

Open `app/routers/admin.py` and add this endpoint:

```python
# Add this import at the top of admin.py if not already there:
from typing import Optional

# Add this route anywhere in the file:
@router.get("/call-sessions")
def get_call_sessions(date: Optional[str] = None, limit: int = 50):
    """
    Returns recent chat/call sessions for the admin panel.
    Optionally filter by date (YYYY-MM-DD).
    """
    return db_service.get_call_sessions(limit=limit, date_str=date)
```

---

## Step 4 — Create `CallTimer.jsx`

`CallScreen.jsx` imports this component but it was not included in the Phase 5 files. Create it now:

**File path:** `frontend/src/components/Voice/CallTimer.jsx`

```jsx
// src/components/Voice/CallTimer.jsx

export default function CallTimer({ seconds }) {
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  return (
    <span className="text-sm font-mono text-gray-400 tabular-nums">
      {mins}:{secs}
    </span>
  );
}
```

---

## Step 5 — Place Frontend Files

Copy your uploaded files into the project at exactly these paths:

```
frontend/src/
├── hooks/
│   └── useCallSession.js                    ← place here
├── pages/
│   └── VoicePage.jsx                        ← REPLACE existing Phase 5 version
└── components/Voice/
    ├── CallScreen.jsx                        ← place here (new file)
    ├── CallTimer.jsx                         ← created in Step 4
    └── CallButton.jsx                        ← already exists from Phase 5, no change needed
```

`WaveformVisualizer.jsx`, `SheetalAvatar.jsx`, `LanguageBadge.jsx`, and `useSession.js` already exist from Phase 5. Do not touch them.

---

## Step 6 — Verify `VITE_API_URL` for WebSocket

Your `useCallSession.js` derives the WebSocket URL from `VITE_API_URL`:

```javascript
const API_WS_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .replace("https://", "wss://")
  .replace("http://", "ws://");
```

Open `frontend/.env` and confirm:
```
VITE_API_URL=http://localhost:8000
```

For production, when your backend is on HTTPS (Railway/Render), this automatically becomes `wss://` which is correct. No code change needed for deployment.

---

## Step 7 — Verify `requirements.txt`

No new Python packages are needed for Phase 7. `call.py` and `call_manager.py` use only packages already in your requirements from previous phases. Confirm these are present:

```
fastapi
uvicorn[standard]
websockets
```

`asyncio` is part of Python's standard library — no install needed.

---

## Step 8 — Full File Structure After Phase 7

```
backend/app/
├── main.py                          ← updated (Step 2)
├── config.py                        ✅ unchanged
├── database.py                      ✅ unchanged
├── routers/
│   ├── chat.py                      ✅ Phase 3, unchanged
│   ├── voice.py                     ✅ Phase 4, unchanged
│   ├── call.py                      ← Phase 7, new (Step 1)
│   └── admin.py                     ← updated (Step 3)
├── services/
│   ├── gemini_service.py            ✅ Phase 3, unchanged
│   ├── booking_service.py           ✅ Phase 3, unchanged
│   ├── db_service.py                ← updated (Step 1, get_call_sessions added)
│   ├── sarvam_service.py            ✅ Phase 4, unchanged
│   ├── elevenlabs_service.py        ✅ Phase 4, unchanged
│   └── call_manager.py              ← Phase 7, new (Step 1)
├── models/
│   ├── chat.py                      ✅ unchanged
│   └── voice.py                     ✅ unchanged
└── knowledge/
    ├── lab_knowledge.py             ✅ Phase 1, unchanged
    ├── test_prices.py               ✅ Phase 1, unchanged
    └── system_prompt.py             ✅ Phase 1, unchanged

frontend/src/
├── App.jsx                          ✅ unchanged (VoicePage already routed)
├── services/
│   └── api.js                       ← updated (Step 1, getCallSessions already added)
├── hooks/
│   ├── useSession.js                ✅ Phase 5, unchanged
│   └── useCallSession.js            ← Phase 7, new (Step 5)
├── pages/
│   ├── ChatPage.jsx                 ✅ unchanged
│   └── VoicePage.jsx                ← Phase 7, replaced (Step 5)
└── components/
    ├── shared/
    │   ├── Header.jsx               ✅ unchanged
    │   ├── SheetalAvatar.jsx        ✅ Phase 5, unchanged
    │   ├── LanguageBadge.jsx        ✅ Phase 5, unchanged
    │   └── LoadingDots.jsx          ✅ unchanged
    └── Voice/
        ├── WaveformVisualizer.jsx   ✅ Phase 5, unchanged
        ├── CallButton.jsx           ✅ Phase 5, unchanged (no longer used in VoicePage but keep it)
        ├── CallScreen.jsx           ← Phase 7, new (Step 5)
        └── CallTimer.jsx            ← Phase 7, new (Step 4)
```

---

## Step 9 — Start and Test

```bash
# Terminal 1 — backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

### Quick WebSocket smoke test (before opening the browser)

Paste this in your browser console while the backend is running:

```javascript
const ws = new WebSocket("ws://localhost:8000/api/call/ws/test-call-001");
ws.onopen  = () => console.log("✅ Connected");
ws.onmessage = (e) => console.log("📩 Message:", JSON.parse(e.data));
ws.onerror = (e) => console.log("❌ Error:", e);
```

Expected within 3 seconds:
```json
{ "type": "tts_audio", "audio_b64": "...", "mime": "audio/wav", "language": "hi", "reply_text": "नमस्ते!..." }
```

If you see this, the backend pipeline (WebSocket → greeting generation → Sarvam TTS → base64 response) is working end-to-end.

### Full call test checklist

| Test | What to check |
|---|---|
| Open `/voice` page | Green call button visible, state shows "Tap to call Sheetal" |
| Click call button | State changes `idle → ringing → connected`, timer starts at 00:00 |
| Greeting plays automatically | Sheetal's voice heard within 3s, her text appears in the log |
| Speak a question in Hindi | State goes `listening → thinking → speaking`, your transcript appears, then Sheetal's reply |
| Speak in Gujarati | Language badge updates to ગુજરાતી, Sheetal replies in Gujarati |
| Speak while Sheetal is talking | Her audio stops immediately, state returns to listening |
| Ask price: "CBC ka price kya hai?" | Reply contains "170 rupees" and "350 rupees", no ₹ symbol |
| Ask for report: "Meri report kab aayegi?" | Flows through 3 turns, Firebase `report_inquiries` collection gets a new document |
| Click red end call button | Timer stops, state shows "Call ended", mic releases |
| Open admin panel | `/api/admin/call-sessions` returns session data for the call just made |
| Firebase check | `chat_sessions` collection has a document with all messages from the call |

---

## What Each File Does (Summary)

| File | Role |
|---|---|
| `call.py` | WebSocket endpoint — receives audio, runs STT/Gemini/TTS pipeline, sends audio back |
| `call_manager.py` | In-memory registry of active calls — stores state (language, speaking flag, lock) per session |
| `useCallSession.js` | Frontend hook — manages WebSocket, microphone, RMS-based VAD, audio playback, interruption |
| `VoicePage.jsx` | Page component — connects `useCallSession` to `CallScreen`, no logic of its own |
| `CallScreen.jsx` | UI component — call button, avatar, waveform, scrollable conversation log, status labels |
| `CallTimer.jsx` | Displays MM:SS duration while call is active |

---

## Phase 7 Checklist

**Backend**
- [ ] `call.py` placed at `app/routers/call.py`
- [ ] `call_manager.py` placed at `app/services/call_manager.py`
- [ ] `db_service.py` replaced with updated version (includes `get_call_sessions`)
- [ ] `main.py` updated — `call` imported and `app.include_router(call.router)` added
- [ ] `admin.py` updated — `/call-sessions` endpoint added
- [ ] WebSocket smoke test passes (greeting received in browser console)

**Frontend**
- [ ] `useCallSession.js` placed at `src/hooks/useCallSession.js`
- [ ] `VoicePage.jsx` replaced at `src/pages/VoicePage.jsx`
- [ ] `CallScreen.jsx` placed at `src/components/Voice/CallScreen.jsx`
- [ ] `CallTimer.jsx` created at `src/components/Voice/CallTimer.jsx`
- [ ] `VITE_API_URL` confirmed in `frontend/.env`

**End-to-End**
- [ ] Call connects and greeting plays within 3 seconds
- [ ] Hindi speech transcribed and answered in Hindi
- [ ] Gujarati speech answered in Gujarati
- [ ] Interruption stops Sheetal mid-sentence
- [ ] Multi-turn conversation (3+ turns) works without manual tapping
- [ ] Report inquiry flow completes over call, saved to Firebase
- [ ] End call button releases microphone and closes WebSocket
- [ ] Admin panel `/call-sessions` shows the call session

---

*Sun Pathology Laboratory & Research Institute — AI Receptionist System*
*Phase 7 — Simulated Real Phone Call*
