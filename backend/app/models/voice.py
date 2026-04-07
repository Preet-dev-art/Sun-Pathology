# app/models/voice.py

from pydantic import BaseModel
from typing import Optional


class VoiceResponse(BaseModel):
    session_id: str
    transcript: str           # what the patient said (transcribed)
    reply_text: str           # Sheetal's text reply
    language: str             # detected language
    category: str             # query category
    booking_state: Optional[str] = None
    suggested_action: Optional[str] = None
    # audio_base64 is returned separately as a file response, not in this model