# app/config.py

import json
import os
import tempfile
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str

    # ElevenLabs
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM" 

    # Sarvam speech
    SARVAM_API_KEY: str

    # Firebase — file path (local dev) OR raw JSON string (Render cloud)
    FIREBASE_CREDENTIALS_PATH: str = "sunpathalogy-firebase-adminsdk-fbsvc-b80c0428bd.json"
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None

    # CORS — override via env var on Render, e.g. '["https://your-app.vercel.app"]'
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_firebase_credentials_path(self) -> str:
        """
        If FIREBASE_CREDENTIALS_JSON env var is set (Render deployment),
        write the JSON to a temp file and return its path.
        Otherwise fall back to FIREBASE_CREDENTIALS_PATH (local dev).
        """
        if self.FIREBASE_CREDENTIALS_JSON:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            tmp.write(self.FIREBASE_CREDENTIALS_JSON)
            tmp.close()
            return tmp.name
        return self.FIREBASE_CREDENTIALS_PATH

settings = Settings()