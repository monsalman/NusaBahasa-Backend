"""Seed data minimal: bahasa Tontemboan & Jawa, 1 admin, 1 validator, 1 user, contoh entri.

Jalankan: python -m app.seed
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Entry, EntryStatus, EntryType, Language, Mission, Role, User


def run():
    db = SessionLocal()
    try:
        # 1. Setup Bahasa Tontemboan
        lang_tnt = db.scalar(select(Language).where(Language.code == "tnt"))
        if not lang_tnt:
            lang_tnt = Language(code="tnt", name="Tontemboan", status="pilot")
            db.add(lang_tnt)
            db.flush()

        # 2. Setup Bahasa Jawa
        lang_jav = db.scalar(select(Language).where(Language.code == "jav"))
        if not lang_jav:
            lang_jav = Language(code="jav", name="Jawa", status="pilot")
            db.add(lang_jav)
            db.flush()

        # 3. Setup Users
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

        # 4. Kosakata & Entri Tontemboan
        tnt_entries = [
            ("Tabea", "Halo", EntryType.kata, EntryStatus.validated),
            ("Kura'kanmo", "Terima kasih", EntryType.frasa, EntryStatus.validated),
            ("Sapa ngaranmu?", "Siapa namamu?", EntryType.kalimat, EntryStatus.validated),
            ("Esa", "Satu", EntryType.kata, EntryStatus.validated),
            ("Rua", "Dua", EntryType.kata, EntryStatus.validated),
            ("Telu", "Tiga", EntryType.kata, EntryStatus.validated),
            ("Pat", "Empat", EntryType.kata, EntryStatus.validated),
            ("Lima", "Lima", EntryType.kata, EntryStatus.validated),
            ("Wewene", "Perempuan", EntryType.kata, EntryStatus.validated),
            ("Tuama", "Laki-laki", EntryType.kata, EntryStatus.validated),
            ("Karia", "Teman", EntryType.kata, EntryStatus.validated),
            ("Kulo", "Putih", EntryType.kata, EntryStatus.validated),
            ("Rerem", "Hitam", EntryType.kata, EntryStatus.validated),
            ("Siang", "Merah", EntryType.kata, EntryStatus.validated),
            ("Rano", "Air", EntryType.kata, EntryStatus.validated),
            ("Tana", "Tanah", EntryType.kata, EntryStatus.validated),
            ("Kelew", "Kucing", EntryType.kata, EntryStatus.validated),
            ("Asu", "Anjing", EntryType.kata, EntryStatus.validated),
            ("Koki", "Ayam", EntryType.kata, EntryStatus.validated),
            ("Sapi", "Sapi", EntryType.kata, EntryStatus.validated),
            ("Kukus", "Monyet", EntryType.kata, EntryStatus.validated),
            ("Witu", "Bintang", EntryType.kata, EntryStatus.validated),
            ("Sendo", "Sendok", EntryType.kata, EntryStatus.validated),
            ("Piring", "Piring", EntryType.kata, EntryStatus.validated),
            ("Meja", "Meja", EntryType.kata, EntryStatus.validated),
            ("Korsi", "Kursi", EntryType.kata, EntryStatus.validated),
            ("Rumah", "Wale", EntryType.kata, EntryStatus.validated),
            ("Mangan", "Makan", EntryType.kata, EntryStatus.validated),
            ("Minum", "Telen", EntryType.kata, EntryStatus.validated),
            ("Tidur", "Tudo", EntryType.kata, EntryStatus.validated),
        ]

        # 5. Kosakata & Entri Jawa
        jav_entries = [
            ("Sugeng enjang", "Selamat pagi", EntryType.frasa, EntryStatus.validated),
            ("Matur nuwun", "Terima kasih", EntryType.frasa, EntryStatus.validated),
            ("Kula nuwun", "Permisi", EntryType.frasa, EntryStatus.validated),
            ("Sinten asmanipun?", "Siapa namamu?", EntryType.kalimat, EntryStatus.validated),
            ("Pripun kabare?", "Bagaimana kabarnya?", EntryType.kalimat, EntryStatus.validated),
            ("Siji", "Satu", EntryType.kata, EntryStatus.validated),
            ("Loro", "Dua", EntryType.kata, EntryStatus.validated),
            ("Telu", "Tiga", EntryType.kata, EntryStatus.validated),
            ("Papat", "Empat", EntryType.kata, EntryStatus.validated),
            ("Lima", "Lima", EntryType.kata, EntryStatus.validated),
            ("Nem", "Enam", EntryType.kata, EntryStatus.validated),
            ("Pitu", "Tujuh", EntryType.kata, EntryStatus.validated),
            ("Wolu", "Delapan", EntryType.kata, EntryStatus.validated),
            ("Sanga", "Sembilan", EntryType.kata, EntryStatus.validated),
            ("Sepuluh", "Sepuluh", EntryType.kata, EntryStatus.validated),
            ("Bapak", "Ayah", EntryType.kata, EntryStatus.validated),
            ("Ibu", "Ibu", EntryType.kata, EntryStatus.validated),
            ("Simbah", "Kakek/Nenek", EntryType.kata, EntryStatus.validated),
            ("Putra", "Anak", EntryType.kata, EntryStatus.validated),
            ("Kanca", "Teman", EntryType.kata, EntryStatus.validated),
            ("Putih", "Putih", EntryType.kata, EntryStatus.validated),
            ("Ireng", "Hitam", EntryType.kata, EntryStatus.validated),
            ("Abang", "Merah", EntryType.kata, EntryStatus.validated),
            ("Ijo", "Hijau", EntryType.kata, EntryStatus.validated),
            ("Kuning", "Kuning", EntryType.kata, EntryStatus.validated),
            ("Banyu", "Air", EntryType.kata, EntryStatus.validated),
            ("Sego", "Nasi", EntryType.kata, EntryStatus.validated),
            ("Mangan", "Makan", EntryType.kata, EntryStatus.validated),
            ("Ngembe", "Minum", EntryType.kata, EntryStatus.validated),
            ("Turu", "Tidur", EntryType.kata, EntryStatus.validated),
        ]

        # Simpan entries Tontemboan jika belum ada
        for text_daerah, text_indonesia, type_, status_ in tnt_entries:
            exists = db.scalar(
                select(Entry).where(Entry.language_id == lang_tnt.id, Entry.text_daerah == text_daerah)
            )
            if not exists:
                db.add(
                    Entry(
                        language_id=lang_tnt.id,
                        text_daerah=text_daerah,
                        text_indonesia=text_indonesia,
                        type=type_,
                        status=status_,
                        contributor_id=users[Role.user].id,
                        validator_id=users[Role.validator].id
                    )
                )

        # Simpan entries Jawa jika belum ada
        for text_daerah, text_indonesia, type_, status_ in jav_entries:
            exists = db.scalar(
                select(Entry).where(Entry.language_id == lang_jav.id, Entry.text_daerah == text_daerah)
            )
            if not exists:
                db.add(
                    Entry(
                        language_id=lang_jav.id,
                        text_daerah=text_daerah,
                        text_indonesia=text_indonesia,
                        type=type_,
                        status=status_,
                        contributor_id=users[Role.user].id,
                        validator_id=users[Role.validator].id
                    )
                )

        db.flush()

        # 6. Setup Mission Tontemboan
        if not db.scalar(select(Mission).where(Mission.language_id == lang_tnt.id)):
            validated = db.scalars(
                select(Entry).where(Entry.language_id == lang_tnt.id, Entry.status == EntryStatus.validated)
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
                    language_id=lang_tnt.id,
                    title="Beli di Warung",
                    dialog_json={"npc_name": "Opa Warung", "steps": steps},
                )
            )

        # 7. Setup Mission Jawa
        if not db.scalar(select(Mission).where(Mission.language_id == lang_jav.id)):
            validated = db.scalars(
                select(Entry).where(Entry.language_id == lang_jav.id, Entry.status == EntryStatus.validated)
            ).all()
            steps = [
                {
                    "npc": "Kula nuwun! Wonten nopo?" if i == 0 else "Nggih, cobi ucapaken iki:",
                    "entry_id": e.id,
                    "text_daerah": e.text_daerah,
                    "text_indonesia": e.text_indonesia,
                    "instruction": f'Ucapkan: "{e.text_daerah}"',
                }
                for i, e in enumerate(validated[:3])
            ]
            db.add(
                Mission(
                    language_id=lang_jav.id,
                    title="Tamu ing Griya",
                    dialog_json={"npc_name": "Pak RT", "steps": steps},
                )
            )

        db.commit()
        print("Seed selesai. Login: admin@nusabahasa.id / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
