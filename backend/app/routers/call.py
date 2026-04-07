# app/routers/call.py

import asyncio
import base64
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.call_manager import ActiveCall, register_call, get_call, end_call
from app.services.sarvam_service import transcribe_audio, text_to_speech
from app.services.elevenlabs_service import text_to_speech_english
from app.services import db_service
from app.services.booking_service import is_booking_trigger, advance_booking_state
from app.services.gemini_service import generate_response
from app.knowledge.lab_knowledge import (
    detect_language, classify_query, get_faq_answer
)
from app.knowledge.test_prices import find_test_price
from app.knowledge.system_prompt import (
    build_system_prompt,
    build_price_context,
    build_package_suggestion_context,
)

router = APIRouter(prefix="/api/call", tags=["call"])

# ── Greeting text per language ────────────────────────────────────────────────
GREETINGS = {
    "hi": "नमस्ते! मैं शीतल हूँ, सन पैथोलॉजी की रिसेप्शनिस्ट। बताइए, मैं आपकी कैसे मदद करूँ?",
    "gu": "નમસ્તે! હું શીતળ છું, સન પેથોલૉજીની રિસેપ્શનિસ્ટ. બોલો, હું તમારી શી મદદ કરી શકું?",
    "en": "Hello! I'm Sheetal, the receptionist at Sun Pathology. How can I help you today?",
}


@router.websocket("/ws/{session_id}")
async def call_websocket(websocket: WebSocket, session_id: str):
    """
    Persistent WebSocket connection for the duration of a simulated phone call.

    Messages FROM frontend (JSON):
        { "type": "audio",       "data": "<base64 webm>", "language": "hi" }
        { "type": "interrupt" }   -- user spoke while Sheetal was speaking
        { "type": "end_call" }    -- user hung up

    Messages TO frontend (JSON):
        { "type": "call_connected" }
        { "type": "transcript",   "text": "..." }
        { "type": "tts_audio",    "audio_b64": "...", "language": "hi",
          "mime": "audio/wav",    "reply_text": "..." }
        { "type": "error",        "message": "..." }
        { "type": "call_ended" }
    """
    await websocket.accept()

    # Create Firebase session if it doesn't exist
    db_service.get_or_create_session(session_id)

    # Register this call
    call = register_call(session_id, websocket)

    try:
        # ── Send greeting immediately ─────────────────────────────────────
        await _send_greeting(call)

        # ── Main message loop ─────────────────────────────────────────────
        async for raw in websocket.iter_text():
            if call.ended:
                break

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "audio":
                # Patient finished speaking — process their audio
                if not call.processing:
                    asyncio.create_task(
                        _handle_patient_audio(call, msg)
                    )

            elif msg_type == "interrupt":
                # Patient spoke while Sheetal was talking
                call.sheetal_speaking = False
                # Frontend handles stopping its own audio playback

            elif msg_type == "end_call":
                break

    except WebSocketDisconnect:
        pass
    finally:
        call.ended = True
        end_call(session_id)
        try:
            await websocket.send_text(json.dumps({"type": "call_ended"}))
        except Exception:
            pass


# ── Greeting ──────────────────────────────────────────────────────────────────

async def _send_greeting(call: ActiveCall):
    """Generate greeting TTS and send to client."""
    # Default to Hindi — update after first patient message detects language
    lang = call.language
    greeting_text = GREETINGS.get(lang, GREETINGS["hi"])

    audio_b64, mime = await _synthesize_to_b64(greeting_text, lang)

    await _send_json(call, {
        "type": "tts_audio",
        "audio_b64": audio_b64,
        "mime": mime,
        "language": lang,
        "reply_text": greeting_text,
    })


# ── Audio handler ─────────────────────────────────────────────────────────────

async def _handle_patient_audio(call: ActiveCall, msg: dict):
    """
    Full pipeline for one patient utterance:
    audio → STT → Gemini → TTS → send back
    """
    # Prevent overlapping pipeline calls
    if call.lock.locked():
        return

    async with call.lock:
        call.processing = True

        try:
            # ── Decode audio ──────────────────────────────────────────────
            audio_b64 = msg.get("data", "")
            language_hint = msg.get("language", call.language)

            if not audio_b64:
                return

            audio_bytes = base64.b64decode(audio_b64)

            # ── STT ───────────────────────────────────────────────────────
            transcript = await transcribe_audio(audio_bytes, language=language_hint)

            if not transcript or len(transcript.strip()) < 2:
                # Too short / noise — ignore silently
                return

            # ── Detect language ───────────────────────────────────────────
            detected = detect_language(transcript)
            if detected in ("hi", "gu"):
                call.language = detected
            elif language_hint in ("hi", "gu", "en"):
                call.language = language_hint

            language = call.language

            # ── Send transcript back to frontend immediately ───────────────
            await _send_json(call, {
                "type": "transcript",
                "text": transcript,
                "language": language,
            })

            # ── Save patient message ──────────────────────────────────────
            db_service.append_message(call.session_id, "user", transcript)

            # ── Classify query ────────────────────────────────────────────
            category = classify_query(transcript)

            # ── FAQ shortcut ──────────────────────────────────────────────
            faq_answer = get_faq_answer(transcript)
            if faq_answer:
                db_service.append_message(call.session_id, "assistant", faq_answer)
                db_service.update_session_meta(
                    call.session_id, language=language, query_category=category
                )
                audio_b64_reply, mime = await _synthesize_to_b64(faq_answer, language)
                await _send_tts(call, faq_answer, audio_b64_reply, mime, language)
                return

            # ── Report inquiry flow ───────────────────────────────────────
            if category == "REPORT":
                reply_text = await _handle_report_flow(call, transcript, language)
                audio_b64_reply, mime = await _synthesize_to_b64(reply_text, language)
                await _send_tts(call, reply_text, audio_b64_reply, mime, language)
                return

            # ── Booking flow ──────────────────────────────────────────────
            current_booking_state, _ = db_service.get_booking_state(call.session_id)
            if is_booking_trigger(transcript, category) or current_booking_state:
                reply_text = await _handle_booking_flow(call, transcript, language, category)
                audio_b64_reply, mime = await _synthesize_to_b64(reply_text, language)
                await _send_tts(call, reply_text, audio_b64_reply, mime, language)
                return

            # ── Build context ─────────────────────────────────────────────
            injected_context = ""
            if category in ("PRICING", "TESTS"):
                matches = find_test_price(transcript)
                if matches:
                    injected_context = build_price_context(matches)
                test_names = [t["name"] for t in (matches or [])]
                pkg_ctx = build_package_suggestion_context(test_names)
                if pkg_ctx:
                    injected_context = f"{injected_context}\n{pkg_ctx}".strip()

            # ── Gemini ────────────────────────────────────────────────────
            history = db_service.get_conversation_history(call.session_id)
            system_prompt = build_system_prompt(mode="voice")

            try:
                reply_text = await generate_response(
                    user_message=transcript,
                    conversation_history=history[:-1],
                    system_prompt=system_prompt,
                    injected_context=injected_context,
                )
            except Exception as e:
                print(f"[CALL {call.session_id}] Gemini error: {e}")
                reply_text = _fallback(language)

            # ── Save reply ────────────────────────────────────────────────
            db_service.append_message(call.session_id, "assistant", reply_text)
            db_service.update_session_meta(
                call.session_id, language=language, query_category=category
            )

            # ── TTS → send ────────────────────────────────────────────────
            audio_b64_reply, mime = await _synthesize_to_b64(reply_text, language)
            await _send_tts(call, reply_text, audio_b64_reply, mime, language)

        except Exception as e:
            print(f"[CALL {call.session_id}] Pipeline error: {e}")
            await _send_json(call, {
                "type": "error",
                "message": _fallback(call.language)
            })
        finally:
            call.processing = False


# ── Flow handlers (reuse logic from voice.py) ─────────────────────────────────

async def _handle_report_flow(call: ActiveCall, transcript: str, language: str) -> str:
    import re
    _, booking_data = db_service.get_booking_state(call.session_id)
    state = booking_data.get("report_state")

    if state is None:
        reply = {
            "en": "I'll check that for you. Could you share your mobile number?",
            "hi": "जी। क्या आप अपना मोबाइल नंबर बता सकते हैं?",
            "gu": "જરૂર. તમારો મોબાઈલ નંબર આપશો?"
        }.get(language, "Could you share your mobile number?")
        booking_data["report_state"] = "WAIT_MOBILE"
        db_service.update_session_meta(call.session_id, booking_data=booking_data)

    elif state == "WAIT_MOBILE":
        mobile = re.sub(r'\D', '', transcript)
        booking_data["report_mobile"] = mobile
        booking_data["report_state"] = "WAIT_NAME"
        db_service.update_session_meta(call.session_id, booking_data=booking_data)
        reply = {
            "en": "Thank you. And the patient's name?",
            "hi": "धन्यवाद। मरीज का नाम बताइए?",
            "gu": "આભાર. દર્દીનું નામ શું છે?"
        }.get(language, "And the patient's name?")

    elif state == "WAIT_NAME":
        booking_data["report_name"] = transcript.strip()
        db_service.save_report_inquiry(
            session_id=call.session_id,
            mobile_number=booking_data.get("report_mobile", ""),
            patient_name=booking_data.get("report_name", "")
        )
        booking_data.pop("report_state", None)
        db_service.update_session_meta(call.session_id, booking_data=booking_data)
        reply = {
            "en": "Thank you. Our team will call you back within 5 to 10 minutes.",
            "hi": "धन्यवाद। हमारी टीम 5 से 10 मिनट में आपको कॉल करेगी।",
            "gu": "આભાર. અમારી ટીમ 5 થી 10 મિનિટમાં તમને કૉલ કરશે."
        }.get(language, "Our team will call back in 5 to 10 minutes.")
    else:
        reply = _fallback(language)

    db_service.append_message(call.session_id, "assistant", reply)
    return reply


async def _handle_booking_flow(
    call: ActiveCall, transcript: str, language: str, category: str
) -> str:
    next_state, step_prompt, is_complete = advance_booking_state(call.session_id, transcript)

    if is_complete:
        reply = {
            "en": "Your home collection booking is confirmed. Our team will arrive at the requested time.",
            "hi": "आपकी होम कलेक्शन बुकिंग हो गई है। हमारी टीम तय समय पर पहुंचेगी।",
            "gu": "તમારી હોમ કલેક્શન બુકિંગ થઈ ગઈ. અમારી ટીમ આવશે."
        }.get(language, "Booking confirmed. Thank you.")
        db_service.append_message(call.session_id, "assistant", reply)
        return reply

    system_prompt = build_system_prompt(mode="voice")
    history = db_service.get_conversation_history(call.session_id)
    reply = await generate_response(
        user_message=transcript,
        conversation_history=history[:-1],
        system_prompt=system_prompt,
        injected_context=f"[BOOKING FLOW — CURRENT STEP]: {step_prompt}",
    )
    db_service.append_message(call.session_id, "assistant", reply)
    return reply


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _synthesize_to_b64(text: str, language: str) -> tuple[str, str]:
    """Convert text to audio. Returns (base64_string, mime_type)."""
    if language == "en":
        audio_bytes = await text_to_speech_english(text)
        mime = "audio/mpeg"
    else:
        audio_bytes = await text_to_speech(text, language=language)
        mime = "audio/wav"

    if not audio_bytes:
        return "", mime

    return base64.b64encode(audio_bytes).decode("utf-8"), mime


async def _send_tts(
    call: ActiveCall,
    reply_text: str,
    audio_b64: str,
    mime: str,
    language: str
):
    """Send TTS audio to the frontend. Sets sheetal_speaking flag."""
    call.sheetal_speaking = True
    await _send_json(call, {
        "type": "tts_audio",
        "audio_b64": audio_b64,
        "mime": mime,
        "language": language,
        "reply_text": reply_text,
    })
    # Note: sheetal_speaking is set to False by the frontend when audio ends
    # (via an "audio_ended" message) or by an "interrupt" message


async def _send_json(call: ActiveCall, data: dict):
    """Safe JSON send — ignores if connection is closed."""
    try:
        if not call.ended:
            await call.websocket.send_text(json.dumps(data))
    except Exception:
        pass


def _fallback(language: str) -> str:
    return {
        "en": "Sorry, I couldn't process that. Please call us at 079-67006700.",
        "hi": "माफ़ कीजिए। कृपया 079-67006700 पर कॉल करें।",
        "gu": "માફ કરજો. 079-67006700 પર કૉલ કરો."
    }.get(language, "Please call 079-67006700.")