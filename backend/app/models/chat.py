# app/models/chat.py

from pydantic import BaseModel, Field
from typing import Optional
import uuid


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1, max_length=2000)
    language_hint: Optional[str] = None   # "en", "hi", "gu" — override auto-detect


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    category: str                          # what type of query this was
    language: str                          # detected language
    booking_state: Optional[str] = None   # current booking step if in progress
    suggested_action: Optional[str] = None # "BOOKING_COMPLETE", "REPORT_INQUIRY_SAVED", etc.