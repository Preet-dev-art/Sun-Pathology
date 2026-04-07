# app/services/db_service.py

from datetime import datetime, timezone
from typing import Optional
from app.database import get_db


# ─────────────────────────────────────────
# CHAT SESSIONS
# ─────────────────────────────────────────

def get_or_create_session(session_id: str) -> dict:
    """
    Fetch an existing session or create a new one.
    Returns the session data as a dict.
    """
    db = get_db()
    ref = db.collection("chat_sessions").document(session_id)
    doc = ref.get()

    if doc.exists:
        return doc.to_dict()

    # Create new session
    new_session = {
        "session_id": session_id,
        "messages": [],
        "language": "en",
        "query_category": "GENERAL",
        "booking_state": None,
        "booking_data": {},
        "lead_state": None,
        "lead_data": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    ref.set(new_session)
    return new_session


def append_message(session_id: str, role: str, content: str) -> None:
    """
    Append a single message to the session's messages array.
    role must be "user" or "assistant".
    """
    db = get_db()
    ref = db.collection("chat_sessions").document(session_id)
    doc = ref.get()

    session = doc.to_dict() if doc.exists else get_or_create_session(session_id)
    messages = session.get("messages", [])

    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    ref.update({
        "messages": messages,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })


def update_session_meta(session_id: str, **kwargs) -> None:
    """
    Update metadata fields on the session.
    Valid kwargs: language, query_category, booking_state, booking_data
    """
    db = get_db()
    kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
    db.collection("chat_sessions").document(session_id).update(kwargs)


def get_conversation_history(session_id: str) -> list[dict]:
    """
    Returns the messages list for a session.
    Format: [{"role": "user"|"assistant", "content": "..."}]
    """
    db = get_db()
    doc = db.collection("chat_sessions").document(session_id).get()

    if doc.exists:
        return doc.to_dict().get("messages", [])
    return []


def get_booking_state(session_id: str) -> tuple[Optional[str], dict]:
    """
    Returns (booking_state, booking_data) for the session.
    booking_state is None if no booking is in progress.
    """
    db = get_db()
    doc = db.collection("chat_sessions").document(session_id).get()

    if doc.exists:
        data = doc.to_dict()
        return data.get("booking_state"), data.get("booking_data", {})
    return None, {}


def get_lead_state(session_id: str) -> tuple[Optional[str], dict]:
    """
    Returns (lead_state, lead_data) for the session.
    lead_state is None if no lead collection is in progress.
    """
    db = get_db()
    doc = db.collection("chat_sessions").document(session_id).get()

    if doc.exists:
        data = doc.to_dict()
        return data.get("lead_state"), data.get("lead_data", {})
    return None, {}


# ─────────────────────────────────────────
# HOME COLLECTION BOOKINGS
# ─────────────────────────────────────────

def save_booking(
    session_id: str,
    mobile_number: str,
    patient_name: str,
    address: str,
    time_slot: str,
    landmark: str = "",
    tests_requested: list = None,
    total_amount: int = 0,
    home_collection_charge: int = 0,
) -> dict:
    """Save a completed home collection booking. Returns the created document data."""
    db = get_db()

    total_payable = total_amount + home_collection_charge

    booking = {
        "session_id": session_id,
        "mobile_number": mobile_number,
        "patient_name": patient_name,
        "address": address,
        "landmark": landmark,
        "time_slot": time_slot,
        "tests_requested": tests_requested or [],
        "total_amount": total_amount,
        "home_collection_charge": home_collection_charge,
        "total_payable": total_payable,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Firestore auto-generates the document ID
    _, ref = db.collection("home_collection_bookings").add(booking)
    booking["id"] = ref.id
    return booking


def get_bookings_today() -> list[dict]:
    """Returns all bookings created today, ordered by creation time."""
    db = get_db()
    today = datetime.now(timezone.utc).date().isoformat()

    docs = (
        db.collection("home_collection_bookings")
        .where("created_at", ">=", f"{today}T00:00:00+00:00")
        .where("created_at", "<=", f"{today}T23:59:59+00:00")
        .order_by("created_at")
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]


# ─────────────────────────────────────────
# REPORT INQUIRIES
# ─────────────────────────────────────────

def save_report_inquiry(session_id: str, mobile_number: str, patient_name: str) -> dict:
    """Save a report status inquiry. Returns the created document data."""
    db = get_db()

    inquiry = {
        "session_id": session_id,
        "mobile_number": mobile_number,
        "patient_name": patient_name,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _, ref = db.collection("report_inquiries").add(inquiry)
    inquiry["id"] = ref.id
    return inquiry


def get_open_inquiries() -> list[dict]:
    """Returns all open (unresolved) report inquiries."""
    db = get_db()
    docs = (
        db.collection("report_inquiries")
        .where("status", "==", "open")
        .stream()
    )
    results = [{"id": d.id, **d.to_dict()} for d in docs]
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


def resolve_inquiry(inquiry_id: str) -> None:
    """Mark an inquiry as resolved."""
    db = get_db()
    db.collection("report_inquiries").document(inquiry_id).update({"status": "resolved"})


# ─────────────────────────────────────────
# LEADS
# ─────────────────────────────────────────

def save_lead(
    session_id: str,
    caller_name: str,
    mobile_number: str,
    organization_name: str = "",
    inquiry_type: str = "general",
    notes: str = ""
) -> dict:
    """Save a corporate or society inquiry lead."""
    db = get_db()

    lead = {
        "session_id": session_id,
        "caller_name": caller_name,
        "mobile_number": mobile_number,
        "organization_name": organization_name,
        "inquiry_type": inquiry_type,
        "notes": notes,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _, ref = db.collection("leads").add(lead)
    lead["id"] = ref.id
    return lead


def get_all_leads(status: str = None) -> list[dict]:
    """Returns leads, optionally filtered by status."""
    db = get_db()
    query = db.collection("leads")
    if status:
        query = query.where("status", "==", status)
    docs = query.stream()
    results = [{"id": d.id, **d.to_dict()} for d in docs]
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


# ─────────────────────────────────────────
# ADMIN — BOOKINGS
# ─────────────────────────────────────────

def get_bookings_by_date(date_str: str) -> list[dict]:
    """
    Returns all bookings for a specific date.
    date_str format: "YYYY-MM-DD"
    """
    db = get_db()
    docs = (
        db.collection("home_collection_bookings")
        .where("created_at", ">=", f"{date_str}T00:00:00+00:00")
        .where("created_at", "<=", f"{date_str}T23:59:59+00:00")
        .order_by("created_at")
        .stream()
    )
    return [{"id": d.id, **d.to_dict()} for d in docs]


def update_booking_status(booking_id: str, status: str) -> None:
    """
    Update a booking's status.
    Valid values: "pending", "confirmed", "completed", "cancelled"
    """
    db = get_db()
    db.collection("home_collection_bookings").document(booking_id).update({
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────
# ADMIN — LEADS
# ─────────────────────────────────────────

def update_lead_status(lead_id: str, status: str) -> None:
    """
    Update a lead's status.
    Valid values: "new", "contacted", "converted", "closed"
    """
    db = get_db()
    db.collection("leads").document(lead_id).update({
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────
# ADMIN — STATS SUMMARY
# ─────────────────────────────────────────

def get_dashboard_stats() -> dict:
    """
    Returns a quick summary for the dashboard stats bar.
    Counts are scoped to today where relevant.
    """
    db = get_db()
    today = datetime.now(timezone.utc).date().isoformat()

    # Today's bookings
    bookings_today = (
        db.collection("home_collection_bookings")
        .where("created_at", ">=", f"{today}T00:00:00+00:00")
        .where("created_at", "<=", f"{today}T23:59:59+00:00")
        .stream()
    )
    bookings_today_list = list(bookings_today)

    # Open report inquiries (all time — staff must action these)
    open_inquiries = (
        db.collection("report_inquiries")
        .where("status", "==", "open")
        .stream()
    )

    # New leads (all time — staff must action these)
    new_leads = (
        db.collection("leads")
        .where("status", "==", "new")
        .stream()
    )

    bookings = bookings_today_list
    pending = [b for b in bookings if b.to_dict().get("status") == "pending"]
    confirmed = [b for b in bookings if b.to_dict().get("status") == "confirmed"]

    return {
        "bookings_today": len(bookings_today_list),
        "bookings_pending": len(pending),
        "bookings_confirmed": len(confirmed),
        "open_inquiries": len(list(open_inquiries)),
        "new_leads": len(list(new_leads)),
    }


def get_call_sessions(limit: int = 50, date_str: str = None) -> list[dict]:
    """
    Returns call sessions for the admin panel, newest first.
    Optionally filter by date (YYYY-MM-DD).
    """
    db = get_db()
    query = db.collection("chat_sessions")

    if date_str:
        query = (
            query
            .where("created_at", ">=", f"{date_str}T00:00:00+00:00")
            .where("created_at", "<=", f"{date_str}T23:59:59+00:00")
        )

    docs = query.order_by("created_at", direction="DESCENDING").limit(limit).stream()
    results = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        results.append(data)
    return results