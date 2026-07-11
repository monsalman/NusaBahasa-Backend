"""Import entri kosakata (+ audio opsional) dari CSV hasil sesi rekaman komunitas.

Dipakai untuk memenuhi target ≥100 entri tervalidasi ber-audio asli.
JANGAN mengarang kosakata — isi CSV harus berasal dari penutur asli.

Format CSV (header wajib):
    text_daerah,text_indonesia,type,audio_path,status
    Tabea,Halo,kata,rekaman/tabea.wav,validated
    Kura'kanmo,Terima kasih,frasa,,pending

- `type`      : kata | frasa | kalimat | cerita   (default: kata)
- `audio_path`: path file audio lokal (opsional). Bila diisi → di-upload ke R2
                dan embedding pelafalan dihitung.
- `status`    : pending | validated              (default: pending)

Jalankan:
    python -m app.import_csv data/tontemboan.csv --lang tnt --contributor user@nusabahasa.id
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import AudioFile, Entry, EntryStatus, EntryType, Language, SpeakerRole, User


def _upload_audio(db, entry_id: int, path: str) -> tuple[bool, str]:
    """Upload ke R2 + hitung embedding. Return (sukses, pesan)."""
    from app.core.config import settings
    from app.services import scoring, storage
    from app.services.audio_utils import AudioError, duration_seconds, to_mono16k

    if not settings.r2_configured:
        return False, "R2 belum dikonfigurasi"
    if not os.path.exists(path):
        return False, f"file tidak ada: {path}"

    data = open(path, "rb").read()
    try:
        dur = duration_seconds(to_mono16k(data))
    except AudioError as e:
        return False, f"audio tak terbaca: {e}"

    ext = path.rsplit(".", 1)[-1].lower()
    key = storage.new_object_key(entry_id, ext)
    storage.put_object_bytes(key, data, f"audio/{ext}")

    af = AudioFile(entry_id=entry_id, r2_object_key=key, duration=dur, speaker_role=SpeakerRole.native)
    try:
        af.embedding = scoring.embed(data)
        emb = "embedding ✅"
    except scoring.AIUnavailable:
        emb = "embedding ⏭ (model AI belum dipasang)"
    db.add(af)
    return True, f"audio {dur}s, {emb}"


def run(csv_path: str, lang_code: str, contributor_email: str, validator_email: str | None) -> int:
    db = SessionLocal()
    try:
        lang = db.scalar(select(Language).where(Language.code == lang_code))
        if not lang:
            print(f"❌ Bahasa '{lang_code}' tidak ada di tabel languages.")
            return 1

        contributor = db.scalar(select(User).where(User.email == contributor_email))
        if not contributor:
            print(f"❌ Kontributor '{contributor_email}' tidak ditemukan.")
            return 1

        validator = None
        if validator_email:
            validator = db.scalar(select(User).where(User.email == validator_email))
            if not validator:
                print(f"❌ Validator '{validator_email}' tidak ditemukan.")
                return 1

        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        dibuat = dilewati = 0
        for i, row in enumerate(rows, start=2):  # baris 1 = header
            daerah = (row.get("text_daerah") or "").strip()
            indo = (row.get("text_indonesia") or "").strip()
            if not daerah or not indo:
                print(f"  baris {i}: ⏭ dilewati (teks kosong)")
                dilewati += 1
                continue

            # idempoten: jangan gandakan entri yang sama
            sudah = db.scalar(
                select(Entry).where(Entry.language_id == lang.id, Entry.text_daerah == daerah)
            )
            if sudah:
                print(f"  baris {i}: ⏭ '{daerah}' sudah ada (#{sudah.id})")
                dilewati += 1
                continue

            status = EntryStatus((row.get("status") or "pending").strip() or "pending")
            entry = Entry(
                language_id=lang.id,
                text_daerah=daerah,
                text_indonesia=indo,
                type=EntryType((row.get("type") or "kata").strip() or "kata"),
                status=status,
                contributor_id=contributor.id,
            )
            if status == EntryStatus.validated and validator:
                entry.validator_id = validator.id
                entry.validated_at = dt.datetime.now(dt.timezone.utc)

            db.add(entry)
            db.flush()  # butuh entry.id untuk object key audio

            pesan = ""
            audio_path = (row.get("audio_path") or "").strip()
            if audio_path:
                sukses, info = _upload_audio(db, entry.id, audio_path)
                pesan = f" — {'✅' if sukses else '⚠️'} {info}"

            print(f"  baris {i}: ✅ #{entry.id} {daerah} / {indo}{pesan}")
            dibuat += 1

        db.commit()
        print(f"\nSelesai: {dibuat} entri dibuat, {dilewati} dilewati.")
        return 0
    finally:
        db.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Import entri kosakata dari CSV")
    p.add_argument("csv_path", help="path file CSV")
    p.add_argument("--lang", default="tnt", help="kode bahasa (default: tnt)")
    p.add_argument("--contributor", default="user@nusabahasa.id", help="email kontributor")
    p.add_argument("--validator", default=None, help="email validator (untuk status=validated)")
    a = p.parse_args()
    return run(a.csv_path, a.lang, a.contributor, a.validator)


if __name__ == "__main__":
    sys.exit(main())
