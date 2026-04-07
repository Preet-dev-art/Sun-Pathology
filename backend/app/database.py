# app/database.py

import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings

_db = None

def get_db():
    """
    Returns the Firestore client singleton.
    Call this wherever you need DB access.
    """
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.get_firebase_credentials_path())
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db