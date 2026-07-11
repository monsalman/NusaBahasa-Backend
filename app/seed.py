"""Seed data minimal: bahasa Tontemboan, 1 admin, 1 validator, 1 user, contoh entri.

Jalankan: python -m app.seed
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Entry, EntryStatus, EntryType, Language, Mission, Role, User


def run():
    db = SessionLocal()
    try:
        lang = db.scalar(select(Language).where(Language.code == "tnt"))
        if not lang:
            lang = Language(code="tnt", name="Tontemboan", status="pilot")
            db.add(lang)
            db.flush()

        seeds = [
            ("admin@nusabahasa.id", "Admin", Role.admin, "admin123"),
            ("validator@nusabahasa.id", "Validator", Role.validator, "validator123"),
            ("user@nusabahasa.id", "User Demo", Role.user, "user123"),
        ]
        users = {}
        for email, name, role, pw in seeds:
            u = db.scalar(select(User).where(User.email == email))
            if not u:
                u = User(name=name, email=email, password_hash=hash_password(pw), role=role)
                db.add(u)
                db.flush()
            users[role] = u

        if not db.scalar(select(Entry)):
            db.add_all(
                [
                    Entry(language_id=lang.id, text_daerah="Tabea", text_indonesia="Halo",
                          type=EntryType.kata, status=EntryStatus.validated,
                          contributor_id=users[Role.user].id, validator_id=users[Role.validator].id),
                    Entry(language_id=lang.id, text_daerah="Kura'kanmo", text_indonesia="Terima kasih",
                          type=EntryType.frasa, status=EntryStatus.pending,
                          contributor_id=users[Role.user].id),
                ]
            )

        db.flush()

        # Demo mission "Beli di Warung" — dialog dari entri tervalidasi.
        if not db.scalar(select(Mission)):
            validated = db.scalars(
                select(Entry).where(Entry.status == EntryStatus.validated)
            ).all()
            steps = [
                {
                    "npc": "Tabea! Mo beli apa di warung?" if i == 0 else "Bagus! Ucapkan ini:",
                    "entry_id": e.id,
                    "text_daerah": e.text_daerah,
                    "text_indonesia": e.text_indonesia,
                    "instruction": f'Ucapkan: "{e.text_daerah}"',
                }
                for i, e in enumerate(validated[:3])
            ]
            db.add(
                Mission(
                    language_id=lang.id,
                    title="Beli di Warung",
                    dialog_json={"npc_name": "Opa Warung", "steps": steps},
                )
            )

        db.commit()
        print("Seed selesai. Login: admin@nusabahasa.id / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
