# app/services/lead_service.py

from app.services.db_service import get_lead_state, update_session_meta, save_lead

LEAD_PROMPTS = {
    "ASK_COMPANY": "Ask for the name of their company.",
    "ASK_SOCIETY": "Ask for the name of their residential society or social group.",
    "ASK_NAME": "Ask for their name or the main contact person's name.",
    "ASK_MOBILE": "Ask for their mobile number.",
    "ASK_EMPLOYEES": "Ask for the approximate number of employees that require the health checkup.",
    "CONFIRM": "Confirm that you have registered their details and state that Dr. Mayank Joshi will contact them shortly to plan the camp and discuss specialized pricing."
}

def is_lead_trigger(category: str) -> bool:
    """Returns True if this message should start a corporate/society lead flow."""
    return category == "CORPORATE"

def advance_lead_state(session_id: str, patient_input: str) -> tuple[str, str, bool]:
    """
    Advance the lead capturing state machine by one step.

    Returns:
        (next_state, step_prompt_for_gemini, is_complete)
    """
    current_state, lead_data = get_lead_state(session_id)
    
    flow_type = lead_data.get("flow_type")
    
    # Starting a fresh lead capture
    if current_state is None:
        import re
        input_lower = patient_input.lower()
        if re.search(r'society|apartment|clubhouse|group|सोसाइटी|ગ્રૂપ|સોસાયટી|फ्लैट', input_lower):
            flow_type = "SOCIETY"
            next_state = "ASK_SOCIETY"
        else:
            flow_type = "CORPORATE"
            next_state = "ASK_COMPANY"
            
        update_session_meta(session_id, lead_state=next_state, lead_data={"flow_type": flow_type})
        return next_state, LEAD_PROMPTS[next_state], False

    # Save patient's answer
    if current_state == "ASK_COMPANY":
        if _is_valid_lead_answer(current_state, patient_input):
            lead_data["organization"] = patient_input.strip()
            next_state = "ASK_NAME"
        else:
            next_state = current_state

    elif current_state == "ASK_SOCIETY":
        if _is_valid_lead_answer(current_state, patient_input):
            lead_data["organization"] = patient_input.strip()
            next_state = "ASK_NAME"
        else:
            next_state = current_state

    elif current_state == "ASK_NAME":
        if _is_valid_lead_answer(current_state, patient_input):
            lead_data["name"] = patient_input.strip()
            next_state = "ASK_MOBILE"
        else:
            next_state = current_state

    elif current_state == "ASK_MOBILE":
        if _is_valid_lead_answer(current_state, patient_input):
            lead_data["mobile"] = _extract_mobile(patient_input)
            if flow_type == "CORPORATE":
                next_state = "ASK_EMPLOYEES"
            else:
                next_state = "CONFIRM"
        else:
            next_state = current_state
            
    elif current_state == "ASK_EMPLOYEES":
        if _is_valid_lead_answer(current_state, patient_input):
            lead_data["employees"] = patient_input.strip()
            next_state = "CONFIRM"
        else:
            next_state = current_state

    elif current_state == "CONFIRM":
        # Save to Firestore
        notes = f"Employee count: {lead_data.get('employees', 'Unknown')}" if flow_type == "CORPORATE" else "Society bulk inquiry"
        save_lead(
            session_id=session_id,
            caller_name=lead_data.get("name", ""),
            mobile_number=lead_data.get("mobile", ""),
            organization_name=lead_data.get("organization", ""),
            inquiry_type=flow_type.lower(),
            notes=notes
        )
        update_session_meta(session_id, lead_state=None, lead_data={})
        return "DONE", "", True

    else:
        next_state = "ASK_COMPANY" if flow_type == "CORPORATE" else "ASK_SOCIETY"

    update_session_meta(session_id, lead_state=next_state, lead_data=lead_data)
    return next_state, LEAD_PROMPTS.get(next_state, ""), False


def _extract_mobile(text: str) -> str:
    import re
    digits = re.sub(r'\D', '', text)
    if len(digits) == 10: return digits
    if len(digits) == 12 and digits.startswith("91"): return digits[2:]
    return digits


def _is_valid_lead_answer(state: str, text: str) -> bool:
    text_lower = text.lower()
    evasions = ["don't know", "dont know", "nahi pata", "malum nahi", "kyu", "why", "kya", "what", "later", "baad me", "wait"]
    if any(e in text_lower for e in evasions) or "?" in text:
        return False
        
    if state in ("ASK_COMPANY", "ASK_SOCIETY", "ASK_NAME"):
        return len(text.strip()) >= 2
    elif state == "ASK_MOBILE":
        import re
        digits = re.sub(r'\D', '', text)
        return len(digits) >= 10
    elif state == "ASK_EMPLOYEES":
        import re
        has_number = bool(re.search(r'\d+', text))
        return has_number
        
    return True
