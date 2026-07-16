from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import EntryStatus, EntryType, Role, SpeakerRole


# ---------- Auth ----------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


# ---------- Language ----------
class LanguageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    status: str


# ---------- Audio ----------
class AudioFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    r2_object_key: str | None
    duration: float | None
    speaker_role: SpeakerRole


# ---------- Entries ----------
class EntryCreate(BaseModel):
    language_id: int
    text_daerah: str
    text_indonesia: str
    type: EntryType = EntryType.kata


class EntryUpdate(BaseModel):
    text_daerah: str | None = None
    text_indonesia: str | None = None
    type: EntryType | None = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    language_id: int
    text_daerah: str
    text_indonesia: str
    type: EntryType
    status: EntryStatus
    contributor_id: int | None
    validator_id: int | None
    validator_note: str | None
    validated_at: dt.datetime | None
    created_at: dt.datetime
    audio_files: list[AudioFileOut] = []


# ---------- Admin ----------
class EntryValidate(BaseModel):
    status: EntryStatus  # validated | rejected
    validator_note: str | None = None


class StatsOut(BaseModel):
    total_entries: int
    by_status: dict[str, int]
    total_audio: int
    active_contributors: int


class LeaderboardRow(BaseModel):
    user_id: int
    name: str
    validated_count: int


# ---------- Missions ----------
class MissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    language_id: int
    title: str
    dialog_json: dict | None


# ---------- Quiz progress ----------
class QuizProgressIn(BaseModel):
    entry_id: int
    score: float
    streak_data: dict | None = None


class QuizProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entry_id: int
    score: float
    streak_data: dict | None
    updated_at: dt.datetime
