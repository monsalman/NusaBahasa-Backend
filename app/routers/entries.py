from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import Entry, EntryStatus, EntryType, Language, User
from app.schemas import EntryCreate, EntryOut, LanguageOut

router = APIRouter(tags=["entries"])


@router.get("/languages", response_model=list[LanguageOut])
def list_languages(db: Session = Depends(get_db)):
    return db.scalars(select(Language)).all()


@router.get("/entries", response_model=list[EntryOut])
def list_entries(
    db: Session = Depends(get_db),
    lang: str | None = None,
    status: EntryStatus = EntryStatus.validated,
    q: str | None = None,
    type: EntryType | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    stmt = select(Entry).where(Entry.status == status)
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
