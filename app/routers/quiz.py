from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import QuizProgress, User
from app.schemas import QuizProgressIn, QuizProgressOut

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/progress", response_model=list[QuizProgressOut])
def get_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(QuizProgress).where(QuizProgress.user_id == user.id)).all()


@router.post("/progress", response_model=QuizProgressOut)
def save_progress(
    payload: QuizProgressIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.scalar(
        select(QuizProgress).where(
            QuizProgress.user_id == user.id, QuizProgress.entry_id == payload.entry_id
        )
    )
    if row:
        row.score = payload.score
        row.streak_data = payload.streak_data
    else:
        row = QuizProgress(
            user_id=user.id,
            entry_id=payload.entry_id,
            score=payload.score,
            streak_data=payload.streak_data,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
