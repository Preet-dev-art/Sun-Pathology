import asyncio
from app.services.gemini_service import generate_response

async def main():
    try:
        reply = await generate_response(
            user_message="CBC ka price kya hai?",
            conversation_history=[],
            system_prompt="You are Sheetal.",
            injected_context="CBC price is 170 rupees."
        )
        print("REPLY:", reply)
    except Exception as e:
        print("EXCEPTION:", type(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
