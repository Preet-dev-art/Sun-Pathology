# app/services/booking_service.py

from app.services.db_service import get_booking_state, update_session_meta, save_booking
from app.knowledge.test_prices import calculate_home_collection_charge, find_test_price

# The ordered steps of the home collection booking flow
BOOKING_STEPS = ["ASK_MOBILE", "ASK_NAME", "ASK_ADDRESS", "ASK_TIME_SLOT", "CONFIRM"]

# Prompts Sheetal uses at each step (injected as context). Gemini will translate these naturally if speaking Hindi/Gujarati.
STEP_PROMPTS = {
    "ASK_MOBILE":    'Ask for the mobile number using this exact instruction: "May I have your mobile number for the booking?"',
    "ASK_NAME":      'The patient gave their mobile number. Now ask: "Please share the name of the patient who needs the test."',
    "ASK_ADDRESS":   'Now ask for the address using this exact instruction: "Kindly share the complete address along with a nearby landmark."',
    "ASK_TIME_SLOT": (
        'Now ask for their preferred time slot using this exact instruction: '
        '"Which time slot would be convenient for the home collection?" '
        'Ensure they know available slots are hourly: '
        '6-7 AM, 7-8 AM, 8-9 AM, 9-10 AM, 10-11 AM, 11-12 PM, '
        '12-1 PM, 1-2 PM, 2-3 PM, 3-4 PM, 4-5 PM, 5-6 PM, 6-7 PM, 7-8 PM.'
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
        # Initialize booking data with empty test list and zero amount
        initial_data = {"tests": [], "total_amount": 0}
        update_session_meta(session_id, booking_state=next_state, booking_data=initial_data)
        return next_state, STEP_PROMPTS["ASK_MOBILE"], False

    # ── Background Test Collection ──
    # Every time the patient speaks, we scan for test names to update the bill
    found_matches = find_test_price(patient_input)
    if found_matches:
        if "tests" not in booking_data: booking_data["tests"] = []
        if "total_amount" not in booking_data: booking_data["total_amount"] = 0
        
        existing_ids = {t["id"] for t in booking_data["tests"]}
        for match in found_matches:
            if match["id"] not in existing_ids:
                booking_data["tests"].append({
                    "id": match["id"],
                    "name": match["name"],
                    "price": match["price"]
                })
                booking_data["total_amount"] += match["price"]
                existing_ids.add(match["id"])

    # Save patient's answer for the current step
    if current_state == "ASK_MOBILE":
        if _is_valid_answer(current_state, patient_input):
            booking_data["mobile"] = _extract_mobile(patient_input)
            next_state = "ASK_NAME"
        else:
            next_state = current_state

    elif current_state == "ASK_NAME":
        if _is_valid_answer(current_state, patient_input):
            booking_data["name"] = patient_input.strip()
            next_state = "ASK_ADDRESS"
        else:
            next_state = current_state

    elif current_state == "ASK_ADDRESS":
        if _is_valid_answer(current_state, patient_input):
            booking_data["address"] = patient_input.strip()
            next_state = "ASK_TIME_SLOT"
        else:
            next_state = current_state

    elif current_state == "ASK_TIME_SLOT":
        if _is_valid_answer(current_state, patient_input):
            booking_data["time_slot"] = patient_input.strip()
            next_state = "CONFIRM"
        else:
            next_state = current_state

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


def _is_valid_answer(state: str, text: str) -> bool:
    """Validate if the patient's answer satisfies the current step."""
    text_lower = text.lower()
    
    # Common evasions or questions where we shouldn't advance the state
    evasions = ["don't know", "dont know", "nahi pata", "malum nahi", "kyu", "why", "kya", "what", "later", "baad me", "wait"]
    if any(e in text_lower for e in evasions) or "?" in text:
        return False
        
    if state == "ASK_MOBILE":
        import re
        digits = re.sub(r'\D', '', text)
        return len(digits) >= 10
    elif state == "ASK_NAME":
        if len(text.strip()) < 2:
            return False
    elif state == "ASK_ADDRESS":
        if len(text.strip()) < 6:
            return False
    elif state == "ASK_TIME_SLOT":
        import re
        has_time = bool(re.search(r'\d+|am|pm|baje|subah|shaam|morning|evening|afternoon', text_lower))
        if not has_time:
            return False
            
    return True