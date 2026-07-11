"""Router AI — transcribe / score / tts (Task 6-7). PIC: Salman.

Semua CPU-only. Bila deps/model belum terpasang, endpoint balas HTTP 503
dengan pesan cara memasang (requirements-ai.txt) — frontend tetap bisa dites.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import AudioFile, Entry, SpeakerRole, User
from app.services import asr, scoring, storage, tts
from app.services.audio_utils import AudioError

router = APIRouter(tags=["ai"])


class TranscribeOut(BaseModel):
    text: str


class ScoreOut(BaseModel):
    score: float
    label: str


def _unavailable(detail: str):
    return HTTPException(status_code=503, detail=detail)


@router.post("/ai/transcribe", response_model=TranscribeOut)
async def transcribe(file: UploadFile = File(...), _: User = Depends(get_current_user)):
    data = await file.read()
    try:
        text = asr.transcribe(data, language="id")
    except asr.AIUnavailable as e:
        raise _unavailable(str(e))
    except AudioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TranscribeOut(text=text)


@router.post("/ai/score", response_model=ScoreOut)
async def score(
    entry_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")

    # Cari embedding referensi (penutur asli) untuk entri ini.
    ref = db.scalar(
        select(AudioFile).where(
            AudioFile.entry_id == entry_id,
            AudioFile.speaker_role == SpeakerRole.native,
            AudioFile.embedding.isnot(None),
        )
    )
    ref_embedding = list(ref.embedding) if ref is not None else None

    # Fallback: hitung embedding referensi dari objek R2 bila ada.
    if ref_embedding is None:
        native = db.scalar(
            select(AudioFile).where(
                AudioFile.entry_id == entry_id,
                AudioFile.speaker_role == SpeakerRole.native,
                AudioFile.r2_object_key.isnot(None),
            )
        )
        if native is None:
            raise HTTPException(status_code=400, detail="Belum ada audio referensi penutur asli untuk entri ini")
        try:
            ref_bytes = storage.get_object_bytes(native.r2_object_key)
            ref_embedding = scoring.embed(ref_bytes)
            native.embedding = ref_embedding  # simpan agar lain kali cepat
            db.commit()
        except scoring.AIUnavailable as e:
            raise _unavailable(str(e))

    learner_bytes = await file.read()
    try:
        result = scoring.score_against(ref_embedding, learner_bytes)
    except scoring.AIUnavailable as e:
        raise _unavailable(str(e))
    except AudioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ScoreOut(**result)


@router.get("/ai/tts")
def synth_tts(
    entry_id: int = Query(...),
    lang: str = Query("tnt"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")
    # 'ind' -> teks Indonesia; bahasa daerah -> teks daerah
    text = entry.text_indonesia if lang == "ind" else entry.text_daerah
    try:
        path = tts.synthesize(text, lang)
    except tts.AIUnavailable as e:
        raise _unavailable(str(e))
    except Exception as e:  # model bahasa mungkin tak tersedia di MMS
        raise HTTPException(status_code=400, detail=f"TTS gagal untuk lang '{lang}': {e}")
    return FileResponse(path, media_type="audio/wav", filename=f"tts-{entry_id}-{lang}.wav")
