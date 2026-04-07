# app/services/sarvam_service.py

import httpx
import base64
from app.config import settings

SARVAM_BASE_URL = "https://api.sarvam.ai"

# Language code mapping — Sarvam uses BCP-47 style codes
LANGUAGE_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "gu": "gu-IN",
}

# TTS voice options per language (Sarvam's available speakers)
TTS_VOICES = {
    "en": "priya",    # Indian English female
    "hi": "priya",    # Hindi female
    "gu": "priya",    # Gujarati female
}


async def transcribe_audio(audio_bytes: bytes, language: str = "hi") -> str:
    """
    Convert speech audio to text using Sarvam AI STT.

    Args:
        audio_bytes: raw audio bytes (WebM or WAV from browser)
        language: detected or hinted language ("en", "hi", "gu")

    Returns:
        Transcribed text string. Empty string on failure.
    """
    lang_code = LANGUAGE_CODES.get(language, "hi-IN")

    # Auto-detect format from bytes header:
    # WAV files start with "RIFF", WebM files start with 0x1a45dfa3
    is_wav = audio_bytes[:4] == b"RIFF"
    mime   = "audio/wav" if is_wav else "audio/webm"
    ext    = "audio.wav" if is_wav else "audio.webm"

    # Sarvam expects multipart form: audio file + language_code
    files = {
        "file": (ext, audio_bytes, mime),
    }
    data = {
        "language_code": lang_code,
        "model": "saarika:v2.5",           # Sarvam's latest multilingual STT model
        "with_timestamps": "false",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{SARVAM_BASE_URL}/speech-to-text",
                headers={"api-subscription-key": settings.SARVAM_API_KEY},
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("transcript", "").strip()

        except httpx.HTTPStatusError as e:
            print(f"SARVAM STT ERROR: {e.response.status_code} — {e.response.text}")
            return ""
        except Exception as e:
            print(f"SARVAM STT ERROR: {e}")
            return ""


async def text_to_speech(text: str, language: str = "hi") -> bytes:
    """
    Convert text to speech using Sarvam AI TTS.

    Args:
        text: Sheetal's reply text
        language: "en", "hi", or "gu"

    Returns:
        Audio bytes (WAV). Empty bytes on failure.
    """
    lang_code = LANGUAGE_CODES.get(language, "hi-IN")
    speaker = TTS_VOICES.get(language, "meera")

    payload = {
        "inputs": [text],
        "target_language_code": lang_code,
        "speaker": speaker,
        "pace": 1.1,             # Slightly faster than default — natural receptionist pace
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
        "model": "bulbul:v3",    # Sarvam's TTS model
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{SARVAM_BASE_URL}/text-to-speech",
                headers={
                    "api-subscription-key": settings.SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # Sarvam returns base64-encoded WAV audio
            audio_b64 = result.get("audios", [""])[0]
            return base64.b64decode(audio_b64) if audio_b64 else b""

        except httpx.HTTPStatusError as e:
            print(f"SARVAM TTS ERROR: {e.response.status_code} — {e.response.text}")
            return b""
        except Exception as e:
            print(f"SARVAM TTS ERROR: {e}")
            return b""