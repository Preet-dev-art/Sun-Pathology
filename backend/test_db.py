# Run this as a one-off script: python test_db.py

from app.database import get_db
from app.services.db_service import get_or_create_session, append_message, get_conversation_history

# Test 1: session creation
session = get_or_create_session("test-session-001")
print("Created:", session["session_id"])

# Test 2: message append
append_message("test-session-001", "user", "CBC ka price kya hai?")
append_message("test-session-001", "assistant", "CBC MRP is 350 rupees, Sun Pathology price is 170 rupees.")

# Test 3: history retrieval
history = get_conversation_history("test-session-001")
print("History length:", len(history))
print("Last message:", history[-1]["content"])