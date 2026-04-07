import asyncio
from app.services.sarvam_service import text_to_speech

async def main():
    try:
        audio = await text_to_speech("नमस्ते", language="hi")
        print(f"Result length: {len(audio)}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
