"""Happy-path quiz progress + missions (Task 4) — kontrak dipakai mobile & game Salman."""
from tests.conftest import TestingSession
from tests.test_entries import buat_entri

from app.models import Mission


def test_quiz_progress_save_and_read(client, user_headers, lang):
    e = buat_entri(client, user_headers, lang)

    r = client.post(
        "/quiz/progress",
        json={"entry_id": e["id"], "score": 0.8, "streak_data": {"streak": 1, "points": 10}},
        headers=user_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["score"] == 0.8

    # Simpan ulang entry sama → update, bukan duplikat
    client.post(
        "/quiz/progress",
        json={"entry_id": e["id"], "score": 1.0, "streak_data": {"streak": 2, "points": 25}},
        headers=user_headers,
    )
    rows = client.get("/quiz/progress", headers=user_headers).json()
    assert len(rows) == 1
    assert rows[0]["score"] == 1.0
    assert rows[0]["streak_data"] == {"streak": 2, "points": 25}


def test_quiz_progress_requires_login(client):
    assert client.get("/quiz/progress").status_code == 401


def test_mission_dialog(client, user_headers, lang):
    dialog = {
        "npc_name": "Opa Warung",
        "steps": [
            {
                "npc": "Selamat datang!",
                "entry_id": 1,
                "text_daerah": "Tabea",
                "text_indonesia": "Halo",
                "instruction": 'Ucapkan: "Tabea"',
            }
        ],
    }
    db = TestingSession()
    m = Mission(language_id=lang.id, title="Beli di Warung", dialog_json=dialog)
    db.add(m)
    db.commit()
    mission_id = m.id
    db.close()

    r = client.get(f"/missions/{mission_id}", headers=user_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Beli di Warung"
    assert body["dialog_json"]["npc_name"] == "Opa Warung"
    assert len(body["dialog_json"]["steps"]) == 1

    assert client.get("/missions/99999", headers=user_headers).status_code == 404
