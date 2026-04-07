# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import chat, voice, admin, call

app = FastAPI(
    title="Sun Pathology AI Receptionist",
    description="Sheetal — 24/7 AI receptionist for Sun Pathology",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(admin.router)
app.include_router(call.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Sun Pathology AI Receptionist"}