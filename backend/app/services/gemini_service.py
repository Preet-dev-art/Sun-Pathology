# app/services/gemini_service.py

import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

# Use gemini-1.5-flash — fastest, cheapest, 1M context window
# Perfect for passing full conversation history every turn
_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=None  # we inject system prompt differently, see below
)


def build_gemini_history(messages: list[dict]) -> list[dict]:
    """
    Convert our DB message format to Gemini's expected format.

    Our format:    {"role": "user"|"assistant", "content": "..."}
    Gemini format: {"role": "user"|"model",     "parts": ["..."]}
    """
    gemini_history = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({
            "role": role,
            "parts": [msg["content"]]
        })
    return gemini_history


async def generate_response(
    user_message: str,
    conversation_history: list[dict],
    system_prompt: str,
    injected_context: str = ""
) -> str:
    """
    Generate Sheetal's response.

    Args:
        user_message: the patient's current message
        conversation_history: all previous messages from DB
        system_prompt: the full Sheetal system prompt
        injected_context: price data or package suggestion context (optional)

    Returns:
        Sheetal's reply as a plain string.
    """
    # Build model with native system instruction — avoids 2 fake turns per call
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt,
    )

    # Build the enriched user message
    if injected_context:
        enriched_message = f"{injected_context}\n\nPatient message: {user_message}"
    else:
        enriched_message = user_message

    # Convert DB history to Gemini format
    gemini_history = build_gemini_history(conversation_history)

    # Start chat with history and send current message
    chat = model.start_chat(history=gemini_history)
    response = await chat.send_message_async(enriched_message)

    return response.text.strip()