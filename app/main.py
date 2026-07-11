from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import admin, ai, audio, auth, entries, missions, quiz

app = FastAPI(title="NusaBahasa API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# --- Bagian Nadhif (backend non-AI) ---
app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(admin.router)
app.include_router(missions.router)
app.include_router(quiz.router)

# --- Bagian Salman (AI + audio R2) ---
app.include_router(audio.router)
app.include_router(ai.router)
