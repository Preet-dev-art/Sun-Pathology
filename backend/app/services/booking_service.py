# app/services/booking_service.py

from app.services.db_service import get_booking_state, update_session_meta, save_booking
from app.knowledge.test_prices import calculate_home_collection_charge

# The ordered steps of the home collection booking flow
BOOKING_STEPS = ["ASK_MOBILE", "ASK_NAME", "ASK_ADDRESS", "ASK_TIME_SLOT", "CONFIRM"]

# Prompts Sheetal uses at each step (injected as context, not hardcoded responses)
STEP_PROMPTS = {
    "ASK_MOBILE":    "Ask the patient for their mobile number. Just that, nothing else.",
    "ASK_NAME":      "The patient gave their mobile number. Now ask for the patient's name only.",
    "ASK_ADDRESS":   "Now ask for the complete address with a nearby landmark.",
    "ASK_TIME_SLOT": (
        "Now ask for their preferred time slot. Available slots are: "
        "6-7 AM, 7-8 AM, 8-9 AM, 9-10 AM, 10-11 AM, 11-12 PM, "
        "12-1 PM, 1-2 PM, 2-3 PM, 3-4 PM, 4-5 PM, 5-6 PM, 6-7 PM, 7-8 PM."
    ),
    "CONFIRM": "Confirm the booking with all details and state the total amount including home collection charge.",
}


def is_booking_trigger(message: str, category: str) -> bool:
    """Returns True if this message should start a home collection booking flow."""
    return category == "BOOKING"


def advance_booking_state(session_id: str, patient_input: str) -> tuple[str, str, bool]:
    """
    Advance the booking state machine by one step.

    Args:
        session_id: the chat session
        patient_input: what the patient just said

    Returns:
        (next_state, step_prompt_for_gemini, is_complete)
    """
    current_state, booking_data = get_booking_state(session_id)

    # Starting a fresh booking
    if current_state is None:
        next_state = "ASK_MOBILE"
        update_session_meta(session_id, booking_state=next_state, booking_data={})
        return next_state, STEP_PROMPTS["ASK_MOBILE"], False

    # Save patient's answer for the current step
    if current_state == "ASK_MOBILE":
        booking_data["mobile"] = _extract_mobile(patient_input)
        next_state = "ASK_NAME"

    elif current_state == "ASK_NAME":
        booking_data["name"] = patient_input.strip()
        next_state = "ASK_ADDRESS"

    elif current_state == "ASK_ADDRESS":
        booking_data["address"] = patient_input.strip()
        next_state = "ASK_TIME_SLOT"

    elif current_state == "ASK_TIME_SLOT":
        booking_data["time_slot"] = patient_input.strip()
        next_state = "CONFIRM"

    elif current_state == "CONFIRM":
        # Booking is complete — save to Firestore
        charge_info = calculate_home_collection_charge(booking_data.get("total_amount", 0))

        save_booking(
            session_id=session_id,
            mobile_number=booking_data.get("mobile", ""),
            patient_name=booking_data.get("name", ""),
            address=booking_data.get("address", ""),
            time_slot=booking_data.get("time_slot", ""),
            tests_requested=booking_data.get("tests", []),
            total_amount=booking_data.get("total_amount", 0),
            home_collection_charge=charge_info["charge"],
        )

        # Clear booking state from session
        update_session_meta(session_id, booking_state=None, booking_data={})
        return "DONE", "", True

    else:
        next_state = "ASK_MOBILE"

    update_session_meta(session_id, booking_state=next_state, booking_data=booking_data)
    return next_state, STEP_PROMPTS.get(next_state, ""), False


def _extract_mobile(text: str) -> str:
    """Extract a 10-digit mobile number from freeform text."""
    import re
    digits = re.sub(r'\D', '', text)
    if len(digits) == 10:
        return digits
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    return digits  # return whatever was given — Sheetal will handle naturally