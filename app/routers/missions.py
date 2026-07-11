from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models import Mission, User
from app.schemas import MissionOut

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("/{mission_id}", response_model=MissionOut)
def get_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    mission = db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Misi tidak ditemukan")
    return mission
