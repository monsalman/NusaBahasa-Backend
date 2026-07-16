from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_current_user_optional
from app.db import get_db
from app.models import Entry, EntryStatus, EntryType, Language, QuizProgress, Role, User
from app.services import storage
from app.schemas import EntryCreate, EntryOut, EntryUpdate, LanguageOut

router = APIRouter(tags=["entries"])


@router.get("/languages", response_model=list[LanguageOut])
def list_languages(db: Session = Depends(get_db)):
    return db.scalars(select(Language)).all()


@router.get("/entries", response_model=list[EntryOut])
def list_entries(
    db: Session = Depends(get_db),
    lang: str | None = None,
    status: EntryStatus | None = None,
    q: str | None = None,
    type: EntryType | None = None,
    mine: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User | None = Depends(get_current_user_optional),
):
    stmt = select(Entry)
    if mine:
        # "Kontribusi Saya": semua entri milik user login, apa pun statusnya.
        if user is None:
            raise HTTPException(status_code=401, detail="Login dulu untuk melihat kontribusimu")
        stmt = stmt.where(Entry.contributor_id == user.id)
        if status:
            stmt = stmt.where(Entry.status == status)
    else:
        stmt = stmt.where(Entry.status == (status or EntryStatus.validated))
    if lang:
        stmt = stmt.join(Language).where(Language.code == lang)
    if type:
        stmt = stmt.where(Entry.type == type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Entry.text_daerah.ilike(like) | Entry.text_indonesia.ilike(like))
    stmt = stmt.order_by(Entry.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return db.scalars(stmt).unique().all()


@router.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")
    return entry


@router.post("/entries", response_model=EntryOut, status_code=201)
def create_entry(
    payload: EntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Language, payload.language_id):
        raise HTTPException(status_code=400, detail="language_id tidak valid")
    entry = Entry(
        language_id=payload.language_id,
        text_daerah=payload.text_daerah,
        text_indonesia=payload.text_indonesia,
        type=payload.type,
        status=EntryStatus.pending,
        contributor_id=user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _can_edit(entry: Entry, user: User) -> bool:
    # Keputusan bagian 9 PRD: kontributor boleh edit selama pending; admin kapan saja.
    if user.role == Role.admin:
        return True
    return entry.contributor_id == user.id and entry.status == EntryStatus.pending


@router.patch("/entries/{entry_id}", response_model=EntryOut)
def update_entry(
    entry_id: int,
    payload: EntryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")
    if not _can_edit(entry, user):
        raise HTTPException(
            status_code=403,
            detail="Hanya kontributor (selama pending) atau admin yang boleh mengubah entri",
        )
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")
    for field, value in data.items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Hanya admin yang boleh menghapus entri")

    # Keputusan bagian 9 PRD: hapus entri = hapus juga objek audionya di R2.
    # Best-effort: kegagalan R2 (belum dikonfigurasi / objek hilang) tidak membatalkan hapus DB.
    if settings.r2_configured:
        for af in entry.audio_files:
            if af.r2_object_key:
                try:
                    storage.delete_object(af.r2_object_key)
                except Exception:
                    pass

    # quiz_progress ber-FK ke entries tanpa cascade — bersihkan dulu agar delete tidak gagal.
    db.query(QuizProgress).filter(QuizProgress.entry_id == entry_id).delete()
    db.delete(entry)  # audio_files ikut terhapus (cascade delete-orphan)
    db.commit()
