# NusaBahasa — Backend (FastAPI)

Backend non-AI (Nadhif) + stub AI/audio (Salman). CPU-only, PostgreSQL + pgvector.

## Struktur
```
app/
├── main.py            # entrypoint FastAPI + CORS + include routers
├── db.py              # engine, SessionLocal, Base, get_db
├── models.py          # SQLAlchemy: languages, users, entries, audio_files, quiz_progress, missions, game_progress
├── schemas.py         # Pydantic request/response
├── seed.py            # data awal (tnt, admin/validator/user, contoh entri)
├── core/
│   ├── config.py      # settings dari .env
│   ├── security.py    # JWT + hash password
│   └── deps.py        # get_current_user, require_roles (RBAC)
├── routers/
│   ├── auth.py        # /auth/register, /auth/login, /auth/me
│   ├── entries.py     # /languages, /entries (list/get/create)
│   ├── admin.py       # /admin/entries (queue), PATCH validate, /admin/stats, /admin/leaderboard
│   ├── missions.py    # /missions/{id}
│   ├── quiz.py        # /quiz/progress (get/save)
│   ├── audio.py       # [Salman] /audio/presign, /audio/confirm (R2)
│   └── ai.py          # [Salman] /ai/transcribe, /ai/score, /ai/tts
└── services/          # [Salman] AI (CPU-only)
    ├── audio_utils.py # FFmpeg -> PCM 16k mono; WAV writer
    ├── storage.py     # Cloudflare R2 (boto3): presign/get/put
    ├── asr.py         # faster-whisper
    ├── scoring.py     # wav2vec2 embedding + cosine similarity
    └── tts.py         # MMS-TTS (VITS) + cache
migrations/            # Alembic
```

## Mengaktifkan AI (bagian Salman)
Deps AI berat dipisah. Model di-load lazy & diunduh saat pertama dipakai ke `MODELS_DIR`.
Tanpa langkah ini, endpoint `/ai/*` balas HTTP 503 dengan instruksi (frontend tetap jalan).
```bash
pip install -r requirements-ai.txt      # torch, transformers, faster-whisper, boto3
# butuh ffmpeg di PATH (macOS: brew install ffmpeg)
```
Set kredensial R2 di `.env` (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`)
agar `/audio/presign|confirm` aktif.

## Menjalankan — cara cepat (Docker)
```bash
cp .env.example .env
docker compose up --build      # API di http://localhost:8000, docs /docs
```

## Menjalankan — lokal (tanpa Docker)
Butuh **Python 3.11+** (3.9 TIDAK didukung — sintaks tipe `int | None`) dan PostgreSQL
dengan extension pgvector. Install pgvector di macOS: `brew install pgvector`.
```bash
createdb nusabahasa
psql -d nusabahasa -c "CREATE EXTENSION IF NOT EXISTS vector;"

python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # set DATABASE_URL, mis:
                                     # postgresql+psycopg2://<user>@localhost:5432/nusabahasa
alembic upgrade head                 # buat tabel + aktifkan pgvector
python -m app.seed                   # data awal
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

## Akun seed
| Role | Email | Password |
|---|---|---|
| admin | admin@nusabahasa.id | admin123 |
| validator | validator@nusabahasa.id | validator123 |
| user | user@nusabahasa.id | user123 |

## Pembagian kerja
- **Nadhif:** auth, entries, admin, missions, quiz, models/migrations.
- **Salman:** audio (R2) + ai (faster-whisper, wav2vec2, MMS-TTS) di `routers/` + `services/`. ✅ Terimplementasi.
