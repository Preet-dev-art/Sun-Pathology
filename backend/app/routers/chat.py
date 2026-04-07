# app/routers/chat.py

from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.gemini_service import generate_response
from app.services import db_service
from app.services.booking_service import is_booking_trigger, advance_booking_state
from app.knowledge.lab_knowledge import (
    detect_language,
    classify_query,
    get_faq_answer,
)
from app.knowledge.test_prices import find_test_price
from app.knowledge.system_prompt import (
    build_system_prompt,
    build_price_context,
    build_package_suggestion_context,
)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    session_id = request.session_id
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # ── Step 1: Ensure session exists ──────────────────────────────────────
    db_service.get_or_create_session(session_id)

    # ── Step 2: Detect language ────────────────────────────────────────────
    language = request.language_hint or detect_language(user_message)

    # ── Step 3: Classify query ─────────────────────────────────────────────
    category = classify_query(user_message)

    # ── Step 4: Try FAQ shortcut (skip Gemini for simple questions) ────────
    faq_answer = get_faq_answer(user_message)
    if faq_answer:
        db_service.append_message(session_id, "user", user_message)
        db_service.append_message(session_id, "assistant", faq_answer)
        db_service.update_session_meta(session_id, language=language, query_category=category)

        return ChatResponse(
            session_id=session_id,
            reply=faq_answer,
            category=category,
            language=language,
        )

    # ── Step 5: Handle REPORT inquiry flow ─────────────────────────────────
    if category == "REPORT":
        return await _handle_report_inquiry(session_id, user_message, language, category)

    # ── Step 6: Handle BOOKING flow ────────────────────────────────────────
    current_booking_state, _ = db_service.get_booking_state(session_id)
    if is_booking_trigger(user_message, category) or current_booking_state is not None:
        return await _handle_booking_flow(session_id, user_message, language, category)

    # ── Step 7: Build context for Gemini ──────────────────────────────────
    injected_context = ""

    # Inject verified price data if this is a pricing/test query
    if category in ("PRICING", "TESTS"):
        matched_tests = find_test_price(user_message)
        if matched_tests:
            injected_context = build_price_context(matched_tests)

        # Also check for package suggestions
        test_names = _extract_test_names_from_message(user_message)
        package_context = build_package_suggestion_context(test_names)
        if package_context:
            injected_context = f"{injected_context}\n{package_context}".strip()

    # ── Step 8: Get conversation history ──────────────────────────────────
    history = db_service.get_conversation_history(session_id)

    # ── Step 9: Call Gemini ────────────────────────────────────────────────
    system_prompt = build_system_prompt(mode="chat")

    try:
        reply = await generate_response(
            user_message=user_message,
            conversation_history=history,
            system_prompt=system_prompt,
            injected_context=injected_context,
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("====== GEMINI ERROR ======", flush=True)
        print(f"Error Message: {e}", flush=True)
        print(f"Traceback:\n{error_details}", flush=True)
        print("==========================", flush=True)
        # Graceful degradation — Sheetal apologises and gives contact number
        reply = _fallback_response(language)

    # ── Step 10: Save to Firestore ─────────────────────────────────────────
    db_service.append_message(session_id, "user", user_message)
    db_service.append_message(session_id, "assistant", reply)
    db_service.update_session_meta(session_id, language=language, query_category=category)

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        category=category,
        language=language,
    )


# ── Sub-handlers ────────────────────────────────────────────────────────────

async def _handle_report_inquiry(session_id, user_message, language, category) -> ChatResponse:
    """
    Multi-step report inquiry flow.
    State is tracked via session booking_data (reused field, no new collection needed).
    """
    import re
    _, booking_data = db_service.get_booking_state(session_id)
    current_state = booking_data.get("report_state")

    db_service.append_message(session_id, "user", user_message)

    if current_state is None:
        # Step 1: Ask for mobile
        reply = {
            "en": "I'll check that for you right away. Could you please share your mobile number?",
            "hi": "जी बिल्कुल। क्या आप अपना मोबाइल नंबर बता सकते हैं?",
            "gu": "જરૂર. તમારો મોબાઈલ નંબર આપશો?"
        }.get(language, "Could you please share your mobile number?")

        booking_data["report_state"] = "WAIT_MOBILE"
        db_service.update_session_meta(session_id, booking_data=booking_data)

    elif current_state == "WAIT_MOBILE":
        mobile = re.sub(r'\D', '', user_message)
        booking_data["report_mobile"] = mobile
        booking_data["report_state"] = "WAIT_NAME"
        db_service.update_session_meta(session_id, booking_data=booking_data)

        reply = {
            "en": "Thank you. And the patient's name?",
            "hi": "धन्यवाद। मरीज का नाम बताइए?",
            "gu": "આભાર. દર્દીનું નામ શું છે?"
        }.get(language, "And the patient's name?")

    elif current_state == "WAIT_NAME":
        booking_data["report_name"] = user_message.strip()
        booking_data["report_state"] = None

        # Save inquiry to Firestore
        db_service.save_report_inquiry(
            session_id=session_id,
            mobile_number=booking_data.get("report_mobile", ""),
            patient_name=booking_data.get("report_name", "")
        )

        # Clear report flow state
        booking_data.pop("report_state", None)
        db_service.update_session_meta(session_id, booking_data=booking_data)

        reply = {
            "en": "Thank you. Our team will call you back within 5 to 10 minutes.",
            "hi": "धन्यवाद। हमारी टीम 5 से 10 मिनट में आपको कॉल करेगी।",
            "gu": "આભાર. અમારી ટીમ 5 થી 10 મિનિટમાં તમને કૉલ કરશે."
        }.get(language, "Our team will call you back within 5 to 10 minutes.")

    else:
        reply = _fallback_response(language)

    db_service.append_message(session_id, "assistant", reply)
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        category=category,
        language=language,
        suggested_action="REPORT_INQUIRY_SAVED" if booking_data.get("report_name") else None
    )


async def _handle_booking_flow(session_id, user_message, language, category) -> ChatResponse:
    """Delegate to the booking state machine."""
    from app.services.booking_service import advance_booking_state

    db_service.append_message(session_id, "user", user_message)

    next_state, step_prompt, is_complete = advance_booking_state(session_id, user_message)

    if is_complete:
        reply = {
            "en": "Your home collection booking is confirmed! Our team will arrive at the requested time. Thank you for choosing Sun Pathology.",
            "hi": "आपकी होम कलेक्शन बुकिंग हो गई है! हमारी टीम तय समय पर पहुंचेगी। सन पैथोलॉजी चुनने के लिए धन्यवाद।",
            "gu": "તમારી હોમ કલેક્શન બુકિંગ થઈ ગઈ! અમારી ટીમ નક્કી સમય પર આવશે. સન પેથોલૉજી પસંદ કરવા આભાર."
        }.get(language, "Booking confirmed! Our team will arrive at the requested time.")

        db_service.append_message(session_id, "assistant", reply)
        return ChatResponse(
            session_id=session_id,
            reply=reply,
            category=category,
            language=language,
            booking_state=None,
            suggested_action="BOOKING_COMPLETE"
        )

    # Use Gemini to generate a natural response for this booking step
    system_prompt = build_system_prompt(mode="chat")
    history = db_service.get_conversation_history(session_id)

    reply = await generate_response(
        user_message=user_message,
        conversation_history=history[:-1],  # exclude the message we just added
        system_prompt=system_prompt,
        injected_context=f"[BOOKING FLOW — CURRENT STEP]: {step_prompt}"
    )

    db_service.append_message(session_id, "assistant", reply)

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        category=category,
        language=language,
        booking_state=next_state,
    )


def _extract_test_names_from_message(message: str) -> list[str]:
    """
    Simple test name extractor for package matching.
    Returns a list of likely test keywords found in the message.
    """
    known_tests = [
        "CBC", "Lipid Profile", "SGPT", "SGOT", "TSH", "T3", "T4",
        "HbA1c", "Vitamin D", "B12", "KFT", "LFT", "Uric Acid",
        "Creatinine", "Hemoglobin", "Sugar", "Thyroid", "Calcium",
        "Iron", "Ferritin", "Cortisol", "FSH", "LH", "Prolactin"
    ]
    message_lower = message.lower()
    return [t for t in known_tests if t.lower() in message_lower]


def _fallback_response(language: str) -> str:
    return {
        "en": "I'm sorry, I couldn't process that right now. Please call us at 079-67006700 and we'll be happy to help.",
        "hi": "माफ़ कीजिए, अभी जवाब देने में दिक्कत हो रही है। कृपया 079-67006700 पर कॉल करें।",
        "gu": "માફ કરજો, અત્યારે જવાબ આપવામાં તકલીફ પડી. કૃપા કરી 079-67006700 પર કૉલ કરો."
    }.get(language, "Please call us at 079-67006700.")