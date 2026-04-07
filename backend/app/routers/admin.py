# app/routers/admin.py

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services import db_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Request models ────────────────────────────────────────────────────────────

class StatusUpdate(BaseModel):
    status: str


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats():
    """
    Quick summary counts for the dashboard header.
    Returns today's booking count, open inquiries, and new leads.
    """
    return db_service.get_dashboard_stats()


# ── Bookings ─────────────────────────────────────────────────────────────────

@router.get("/bookings/today")
def get_bookings_today():
    """Returns all home collection bookings created today, ordered by time."""
    return db_service.get_bookings_today()


@router.get("/bookings")
def get_bookings(date: str = Query(default=None, description="Date in YYYY-MM-DD format")):
    """
    Returns bookings for a given date.
    If no date provided, defaults to today.
    """
    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()

    # Basic format validation
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    return db_service.get_bookings_by_date(date)


@router.patch("/bookings/{booking_id}/status")
def update_booking_status(booking_id: str, body: StatusUpdate):
    """
    Update a booking's status.
    Valid statuses: pending, confirmed, completed, cancelled
    """
    valid = {"pending", "confirmed", "completed", "cancelled"}
    if body.status not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid)}"
        )

    try:
        db_service.update_booking_status(booking_id, body.status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update booking: {str(e)}")

    return {"id": booking_id, "status": body.status, "updated": True}


# ── Report Inquiries ──────────────────────────────────────────────────────────

@router.get("/report-inquiries")
def get_report_inquiries(status: str = Query(default="open")):
    """
    Returns report inquiries filtered by status.
    Defaults to open (unresolved) inquiries only.
    """
    if status == "open":
        return db_service.get_open_inquiries()

    # For "all" or "resolved", fetch from Firestore directly
    from app.database import get_db
    db = get_db()
    query = db.collection("report_inquiries").order_by("created_at", direction="DESCENDING")
    if status != "all":
        query = query.where("status", "==", status)
    return [{"id": d.id, **d.to_dict()} for d in query.stream()]


@router.patch("/report-inquiries/{inquiry_id}/resolve")
def resolve_inquiry(inquiry_id: str):
    """Mark a report inquiry as resolved. Staff calls this after calling the patient."""
    try:
        db_service.resolve_inquiry(inquiry_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve inquiry: {str(e)}")

    return {"id": inquiry_id, "status": "resolved", "updated": True}


# ── Leads ─────────────────────────────────────────────────────────────────────

@router.get("/leads")
def get_leads(status: str = Query(default=None)):
    """
    Returns leads, optionally filtered by status.
    Valid statuses: new, contacted, converted, closed
    """
    return db_service.get_all_leads(status=status)


@router.patch("/leads/{lead_id}/status")
def update_lead_status(lead_id: str, body: StatusUpdate):
    """Update a lead's status."""
    valid = {"new", "contacted", "converted", "closed"}
    if body.status not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid)}"
        )

    try:
        db_service.update_lead_status(lead_id, body.status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lead: {str(e)}")

    return {"id": lead_id, "status": body.status, "updated": True}


# ── Call Sessions (transcripts) ───────────────────────────────────────────────

@router.get("/call-sessions")
def get_call_sessions(
    date: str = Query(default=None, description="Date in YYYY-MM-DD format"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Returns call sessions with full message transcripts for the admin panel.
    Ordered newest-first. Optionally filtered by date.
    """
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    return db_service.get_call_sessions(limit=limit, date_str=date)