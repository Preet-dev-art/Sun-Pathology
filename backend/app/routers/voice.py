# app/routers/voice.py

import base64
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from app.services.sarvam_service import transcribe_audio, text_to_speech
from app.services.elevenlabs_service import text_to_speech_english
from app.services import db_service
from app.services.booking_service import is_booking_trigger, advance_booking_state
from app.services.gemini_service import generate_response
from app.knowledge.lab_knowledge import detect_language, classify_query, get_faq_answer
from app.knowledge.test_prices import find_test_price
from app.knowledge.system_prompt import (
    build_system_prompt,
    build_price_context,
    build_package_suggestion_context,
)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# File size guard — reject audio over 10MB
MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/process")
async def process_voice(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    language_hint: str = Form(default=""),
):
    """
    Full voice turn pipeline:
    1. Read uploaded audio
    2. Transcribe via Sarvam STT
    3. Run through the same chat pipeline as /api/chat
    4. Convert reply to audio via ElevenLabs (English) or Sarvam TTS (Hindi/Gujarati)
    5. Return JSON with transcript + reply_text + audio_base64
    """

    # ── Guard: file size ───────────────────────────────────────────────────
    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large. Max 10MB.")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file received.")

    # ── Step 1: Transcribe ─────────────────────────────────────────────────
    # Use language hint for STT if provided (improves accuracy)
    stt_language = language_hint if language_hint in ("en", "hi", "gu") else "hi"
    transcript = await transcribe_audio(audio_bytes, language=stt_language)

    if not transcript:
        # STT failed — return a graceful error in audio
        fallback_text = _fallback_response(stt_language)
        audio_b64 = await _synthesize(fallback_text, stt_language)
        return JSONResponse({
            "session_id": session_id,
            "transcript": "",
            "reply_text": fallback_text,
            "language": stt_language,
            "category": "GENERAL",
            "audio_base64": audio_b64,
        })

    # ── Step 2: Detect language from transcript ────────────────────────────
    language = language_hint if language_hint in ("en", "hi", "gu") else detect_language(transcript)

    # ── Step 3: Classify query ─────────────────────────────────────────────
    category = classify_query(transcript)

    # ── Step 4: Ensure session exists ─────────────────────────────────────
    db_service.get_or_create_session(session_id)

    # ── Step 5: FAQ shortcut ───────────────────────────────────────────────
    faq_answer = get_faq_answer(transcript)
    if faq_answer:
        db_service.append_message(session_id, "user", transcript)
        db_service.append_message(session_id, "assistant", faq_answer)
        db_service.update_session_meta(session_id, language=language, query_category=category)
        audio_b64 = await _synthesize(faq_answer, language)
        return JSONResponse({
            "session_id": session_id,
            "transcript": transcript,
            "reply_text": faq_answer,
            "language": language,
            "category": category,
            "audio_base64": audio_b64,
        })

    # ── Step 6: Report inquiry flow ────────────────────────────────────────
    if category == "REPORT":
        reply_text, suggested_action = await _handle_report_voice(
            session_id, transcript, language, category
        )
        audio_b64 = await _synthesize(reply_text, language)
        return JSONResponse({
            "session_id": session_id,
            "transcript": transcript,
            "reply_text": reply_text,
            "language": language,
            "category": category,
            "suggested_action": suggested_action,
            "audio_base64": audio_b64,
        })

    # ── Step 7: Booking flow ───────────────────────────────────────────────
    current_booking_state, _ = db_service.get_booking_state(session_id)
    if is_booking_trigger(transcript, category) or current_booking_state is not None:
        reply_text, booking_state, suggested_action = await _handle_booking_voice(
            session_id, transcript, language, category
        )
        audio_b64 = await _synthesize(reply_text, language)
        return JSONResponse({
            "session_id": session_id,
            "transcript": transcript,
            "reply_text": reply_text,
            "language": language,
            "category": category,
            "booking_state": booking_state,
            "suggested_action": suggested_action,
            "audio_base64": audio_b64,
        })

    # ── Step 8: Build Gemini context ──────────────────────────────────────
    injected_context = ""
    if category in ("PRICING", "TESTS"):
        matched_tests = find_test_price(transcript)
        if matched_tests:
            injected_context = build_price_context(matched_tests)

        test_names = _extract_test_names(transcript)
        pkg_ctx = build_package_suggestion_context(test_names)
        if pkg_ctx:
            injected_context = f"{injected_context}\n{pkg_ctx}".strip()

    # ── Step 9: Call Gemini ────────────────────────────────────────────────
    history = db_service.get_conversation_history(session_id)
    system_prompt = build_system_prompt(mode="voice")   # slightly shorter for voice

    try:
        reply_text = await generate_response(
            user_message=transcript,
            conversation_history=history,
            system_prompt=system_prompt,
            injected_context=injected_context,
        )
    except Exception as e:
        print(f"GEMINI ERROR (voice): {e}")
        reply_text = _fallback_response(language)

    # ── Step 10: Save messages ─────────────────────────────────────────────
    db_service.append_message(session_id, "user", transcript)
    db_service.append_message(session_id, "assistant", reply_text)
    db_service.update_session_meta(session_id, language=language, query_category=category)

    # ── Step 11: Synthesize reply to audio ────────────────────────────────
    audio_b64 = await _synthesize(reply_text, language)

    return JSONResponse({
        "session_id": session_id,
        "transcript": transcript,
        "reply_text": reply_text,
        "language": language,
        "category": category,
        "audio_base64": audio_b64,
    })


# ── TTS router — language decides which service ─────────────────────────────

async def _synthesize(text: str, language: str) -> str:
    """
    Convert text to audio. Returns base64-encoded audio string.
    - English → ElevenLabs (MP3)
    - Hindi / Gujarati → Sarvam (WAV)
    Empty string on total failure.
    """
    if language == "en":
        audio_bytes = await text_to_speech_english(text)
    else:
        audio_bytes = await text_to_speech(text, language=language)

    if not audio_bytes:
        return ""
    return base64.b64encode(audio_bytes).decode("utf-8")


# ── Sub-handlers (mirror of chat.py) ────────────────────────────────────────

async def _handle_report_voice(session_id, transcript, language, category):
    """Report inquiry state machine for voice. Returns (reply_text, suggested_action)."""
    import re
    _, booking_data = db_service.get_booking_state(session_id)
    current_state = booking_data.get("report_state")

    db_service.append_message(session_id, "user", transcript)

    if current_state is None:
        reply = {
            "en": "I'll check that for you. Could you please share your mobile number?",
            "hi": "जी। क्या आप अपना मोबाइल नंबर बता सकते हैं?",
            "gu": "જરૂર. તમારો મોબાઈલ નંબર આપશો?"
        }.get(language, "Could you share your mobile number?")
        booking_data["report_state"] = "WAIT_MOBILE"
        db_service.update_session_meta(session_id, booking_data=booking_data)
        db_service.append_message(session_id, "assistant", reply)
        return reply, None

    elif current_state == "WAIT_MOBILE":
        mobile = re.sub(r'\D', '', transcript)
        booking_data["report_mobile"] = mobile
        booking_data["report_state"] = "WAIT_NAME"
        db_service.update_session_meta(session_id, booking_data=booking_data)
        reply = {
            "en": "Thank you. And the patient's name please?",
            "hi": "धन्यवाद। मरीज का नाम बताइए?",
            "gu": "આભાર. દર્દીનું નામ શું છે?"
        }.get(language, "And the patient's name?")
        db_service.append_message(session_id, "assistant", reply)
        return reply, None

    elif current_state == "WAIT_NAME":
        booking_data["report_name"] = transcript.strip()
        db_service.save_report_inquiry(
            session_id=session_id,
            mobile_number=booking_data.get("report_mobile", ""),
            patient_name=booking_data.get("report_name", "")
        )
        booking_data.pop("report_state", None)
        db_service.update_session_meta(session_id, booking_data=booking_data)
        reply = {
            "en": "Thank you. Our team will call you back within 5 to 10 minutes.",
            "hi": "धन्यवाद। हमारी टीम 5 से 10 मिनट में आपको कॉल करेगी।",
            "gu": "આભાર. અમારી ટીમ 5 થી 10 મિનિટમાં તમને કૉલ કરશે."
        }.get(language, "Our team will call you back in 5 to 10 minutes.")
        db_service.append_message(session_id, "assistant", reply)
        return reply, "REPORT_INQUIRY_SAVED"

    return _fallback_response(language), None


async def _handle_booking_voice(session_id, transcript, language, category):
    """Booking state machine for voice. Returns (reply_text, booking_state, suggested_action)."""
    db_service.append_message(session_id, "user", transcript)
    next_state, step_prompt, is_complete = advance_booking_state(session_id, transcript)

    if is_complete:
        reply = {
            "en": "Your home collection booking is confirmed. Our team will arrive at the requested time. Thank you for choosing Sun Pathology.",
            "hi": "आपकी होम कलेक्शन बुकिंग हो गई है। हमारी टीम तय समय पर पहुंचेगी। धन्यवाद।",
            "gu": "તમારી હોમ કલેક્શન બુકિંગ થઈ ગઈ. અમારી ટીમ આવશે. આભાર."
        }.get(language, "Booking confirmed. Thank you.")
        db_service.append_message(session_id, "assistant", reply)
        return reply, None, "BOOKING_COMPLETE"

    system_prompt = build_system_prompt(mode="voice")
    history = db_service.get_conversation_history(session_id)
    reply = await generate_response(
        user_message=transcript,
        conversation_history=history[:-1],
        system_prompt=system_prompt,
        injected_context=f"[BOOKING FLOW — CURRENT STEP]: {step_prompt}",
    )
    db_service.append_message(session_id, "assistant", reply)
    return reply, next_state, None


def _extract_test_names(message: str) -> list[str]:
    known = [
        "CBC", "Lipid Profile", "SGPT", "SGOT", "TSH", "T3", "T4",
        "HbA1c", "Vitamin D", "B12", "KFT", "LFT", "Uric Acid",
        "Creatinine", "Hemoglobin", "Sugar", "Thyroid", "Calcium",
        "Iron", "Ferritin", "Cortisol", "FSH", "LH", "Prolactin"
    ]
    ml = message.lower()
    return [t for t in known if t.lower() in ml]


def _fallback_response(language: str) -> str:
    return {
        "en": "I'm sorry, I couldn't process that. Please call us at 079-67006700.",
        "hi": "माफ़ कीजिए। कृपया 079-67006700 पर कॉल करें।",
        "gu": "માફ કરજો. 079-67006700 પર કૉલ કરો."
    }.get(language, "Please call us at 079-67006700.")