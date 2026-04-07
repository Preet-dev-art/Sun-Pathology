# app/services/call_manager.py

import asyncio
from dataclasses import dataclass, field
from typing import Optional
from fastapi import WebSocket


@dataclass
class ActiveCall:
    session_id: str
    websocket: WebSocket
    language: str = "gu"              # detected/updated as call progresses
    sheetal_speaking: bool = False    # True while TTS audio is being sent to client
    processing: bool = False          # True while STT+Gemini is running
    ended: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


# Registry: session_id → ActiveCall
_calls: dict[str, ActiveCall] = {}


def register_call(session_id: str, websocket: WebSocket) -> ActiveCall:
    call = ActiveCall(session_id=session_id, websocket=websocket)
    _calls[session_id] = call
    return call


def get_call(session_id: str) -> Optional[ActiveCall]:
    return _calls.get(session_id)


def end_call(session_id: str) -> None:
    _calls.pop(session_id, None)