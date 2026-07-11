from __future__ import annotations

import datetime as dt
import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Role(str, enum.Enum):
    user = "user"
    validator = "validator"
    admin = "admin"


class EntryType(str, enum.Enum):
    kata = "kata"
    frasa = "frasa"
    kalimat = "kalimat"
    cerita = "cerita"


class EntryStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    validated = "validated"
    rejected = "rejected"


class SpeakerRole(str, enum.Enum):
    native = "native"
    learner = "learner"


class Language(Base):
    __tablename__ = "languages"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)  # 'tnt'
    name: Mapped[str] = mapped_column(String(128))                          # 'Tontemboan'
    status: Mapped[str] = mapped_column(String(32), default="pilot")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Entry(Base):
    __tablename__ = "entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), index=True)
    text_daerah: Mapped[str] = mapped_column(Text)
    text_indonesia: Mapped[str] = mapped_column(Text)
    type: Mapped[EntryType] = mapped_column(Enum(EntryType), default=EntryType.kata)
    status: Mapped[EntryStatus] = mapped_column(Enum(EntryStatus), default=EntryStatus.pending, index=True)
    contributor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    validator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    validator_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    language: Mapped[Language] = relationship()
    audio_files: Mapped[list["AudioFile"]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class AudioFile(Base):
    __tablename__ = "audio_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"), index=True)
    r2_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    speaker_role: Mapped[SpeakerRole] = mapped_column(Enum(SpeakerRole), default=SpeakerRole.native)
    # Diisi kode pronunciation scoring (Salman). Nullable karena tak selalu ada.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entry: Mapped[Entry] = relationship(back_populates="audio_files")


class QuizProgress(Base):
    __tablename__ = "quiz_progress"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    streak_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Mission(Base):
    __tablename__ = "missions"
    id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    dialog_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class GameProgress(Base):
    __tablename__ = "game_progress"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="in_progress")
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
