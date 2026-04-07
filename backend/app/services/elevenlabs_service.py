# app/services/elevenlabs_service.py

import httpx
from app.config import settings

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Sheetal's voice — use ElevenLabs Voice ID for a professional Indian female voice.
# Recommended: "Rachel" (en-US) or clone a custom voice via ElevenLabs dashboard.
# Set ELEVENLABS_VOICE_ID in your .env
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"   # Default: Rachel — replace with your Voice ID


async def text_to_speech_english(text: str) -> bytes:
    """
    Convert English text to speech using ElevenLabs.

    Args:
        text: Sheetal's English reply

    Returns:
        MP3 audio bytes. Empty bytes on failure.
    """
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{VOICE_ID}"

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                url,
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.content   # raw MP3 bytes

        except httpx.HTTPStatusError as e:
            print(f"ELEVENLABS TTS ERROR: {e.response.status_code} — {e.response.text}")
            return b""
        except Exception as e:
            print(f"ELEVENLABS TTS ERROR: {e}")
            return b""