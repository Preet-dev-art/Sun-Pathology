import asyncio
from app.services.sarvam_service import transcribe_audio

async def main():
    try:
        # Just send some dummy bytes to get an API error about the model or audio
        audio = b"dummy audio data dummy dummy dummy"
        transcript = await transcribe_audio(audio, language="hi")
        print(f"Transcript: {transcript}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
