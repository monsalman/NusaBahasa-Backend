"""Router audio — R2 upload (Task 5). PIC: Salman.

Dua jalur upload:
1. `/audio/presign` + `/audio/confirm` — HP upload LANGSUNG ke R2 (file tidak lewat
   FastAPI). Butuh CORS pada bucket R2.
2. `/audio/upload` — file lewat FastAPI lalu diteruskan ke R2. Tidak butuh CORS,
   dipakai dashboard & sebagai fallback. Sekaligus menghitung durasi + embedding.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db import get_db
from app.models import AudioFile, Entry, SpeakerRole, User
from app.services import scoring, storage
from app.services.audio_utils import AudioError, duration_seconds, to_mono16k

router = APIRouter(tags=["audio"])

_EXT = {
    "audio/webm": "webm", "audio/ogg": "ogg", "audio/wav": "wav",
    "audio/x-wav": "wav", "audio/mpeg": "mp3", "audio/mp4": "m4a",
}


class PresignIn(BaseModel):
    entry_id: int
    content_type: str = "audio/webm"


class PresignOut(BaseModel):
    upload_url: str
    object_key: str


class ConfirmIn(BaseModel):
    entry_id: int
    object_key: str
    duration: float | None = None
    speaker_role: SpeakerRole = SpeakerRole.native


class AudioOut(BaseModel):
    audio_file_id: int
    playback_url: str
    duration: float | None
    embedding_computed: bool


def _ext_for(content_type: str | None, filename: str | None) -> str:
    """Tentukan ekstensi objek: dari content-type, fallback ke sufiks nama file."""
    if content_type and content_type in _EXT:
        return _EXT[content_type]
    if filename and "." in filename:
        suffix = filename.rsplit(".", 1)[-1].lower()
        if suffix in set(_EXT.values()):
            return suffix
    return "webm"


def _require_r2():
    if not settings.r2_configured:
        raise HTTPException(status_code=503, detail="R2 belum dikonfigurasi (set R2_* di .env)")


def _get_entry(db: Session, entry_id: int) -> Entry:
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")
    return entry


def _persist(db: Session, entry_id: int, object_key: str, speaker_role: SpeakerRole,
             audio_bytes: bytes | None, duration: float | None) -> AudioOut:
    """Buat baris audio_files; hitung embedding bila audio penutur asli & model tersedia."""
    af = AudioFile(
        entry_id=entry_id,
        r2_object_key=object_key,
        duration=duration,
        speaker_role=speaker_role,
    )
    embedding_computed = False
    if speaker_role == SpeakerRole.native:
        try:
            data = audio_bytes if audio_bytes is not None else storage.get_object_bytes(object_key)
            af.embedding = scoring.embed(data)
            embedding_computed = True
        except scoring.AIUnavailable:
            pass  # model AI belum dipasang → embedding menyusul
        except Exception:
            pass
    db.add(af)
    db.commit()
    db.refresh(af)
    return AudioOut(
        audio_file_id=af.id,
        playback_url=storage.public_url(object_key),
        duration=af.duration,
        embedding_computed=embedding_computed,
    )


@router.post("/audio/presign", response_model=PresignOut)
def presign(payload: PresignIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    _require_r2()
    _get_entry(db, payload.entry_id)
    ext = _EXT.get(payload.content_type, "webm")
    key = storage.new_object_key(payload.entry_id, ext)
    return PresignOut(upload_url=storage.presign_put(key, payload.content_type), object_key=key)


@router.post("/audio/confirm", response_model=AudioOut)
def confirm(payload: ConfirmIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    _require_r2()
    _get_entry(db, payload.entry_id)
    return _persist(db, payload.entry_id, payload.object_key, payload.speaker_role, None, payload.duration)


@router.post("/audio/upload", response_model=AudioOut)
async def upload(
    entry_id: int = Form(...),
    speaker_role: SpeakerRole = Form(SpeakerRole.native),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Upload via server (tanpa CORS). Menghitung durasi + embedding sekaligus."""
    _require_r2()
    _get_entry(db, entry_id)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File audio kosong")

    try:
        dur = duration_seconds(to_mono16k(data))
    except AudioError:
        dur = None  # tetap simpan; durasi opsional

    ext = _ext_for(file.content_type, file.filename)
    key = storage.new_object_key(entry_id, ext)
    storage.put_object_bytes(key, data, file.content_type or "application/octet-stream")

    return _persist(db, entry_id, key, speaker_role, data, dur)


@router.get("/audio/{audio_file_id}/url")
def playback_url(audio_file_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    af = db.get(AudioFile, audio_file_id)
    if not af or not af.r2_object_key:
        raise HTTPException(status_code=404, detail="Audio tidak ditemukan")
    return {"url": storage.public_url(af.r2_object_key)}
