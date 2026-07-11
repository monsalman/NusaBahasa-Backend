import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db import get_db
from app.models import AudioFile, Entry, EntryStatus, Role, User
from app.schemas import EntryOut, EntryValidate, LeaderboardRow, StatsOut

router = APIRouter(prefix="/admin", tags=["admin"])

validator_or_admin = require_roles(Role.validator, Role.admin)
admin_only = require_roles(Role.admin)


@router.get("/entries", response_model=list[EntryOut])
def validation_queue(
    status: EntryStatus = EntryStatus.pending,
    db: Session = Depends(get_db),
    _: User = Depends(validator_or_admin),
):
    stmt = select(Entry).where(Entry.status == status).order_by(Entry.created_at.asc())
    return db.scalars(stmt).unique().all()


@router.patch("/entries/{entry_id}", response_model=EntryOut)
def validate_entry(
    entry_id: int,
    payload: EntryValidate,
    db: Session = Depends(get_db),
    user: User = Depends(validator_or_admin),
):
    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri tidak ditemukan")
    if payload.status not in (EntryStatus.validated, EntryStatus.rejected):
        raise HTTPException(status_code=400, detail="status harus validated atau rejected")
    entry.status = payload.status
    entry.validator_id = user.id
    entry.validator_note = payload.validator_note
    entry.validated_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    by_status = dict(
        db.execute(select(Entry.status, func.count()).group_by(Entry.status)).all()
    )
    return StatsOut(
        total_entries=db.scalar(select(func.count()).select_from(Entry)) or 0,
        by_status={k.value: v for k, v in by_status.items()},
        total_audio=db.scalar(select(func.count()).select_from(AudioFile)) or 0,
        active_contributors=db.scalar(select(func.count(func.distinct(Entry.contributor_id)))) or 0,
    )


@router.get("/leaderboard", response_model=list[LeaderboardRow])
def leaderboard(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    rows = db.execute(
        select(User.id, User.name, func.count(Entry.id))
        .join(Entry, Entry.contributor_id == User.id)
        .where(Entry.status == EntryStatus.validated)
        .group_by(User.id, User.name)
        .order_by(func.count(Entry.id).desc())
        .limit(20)
    ).all()
    return [LeaderboardRow(user_id=r[0], name=r[1], validated_count=r[2]) for r in rows]
