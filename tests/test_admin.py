"""Happy-path validasi + statistik + leaderboard (Task 3–4)."""
from tests.test_entries import buat_entri


def test_validation_queue_and_approve(client, user_headers, validator_headers, lang):
    e = buat_entri(client, user_headers, lang)

    r = client.get("/admin/entries?status=pending", headers=validator_headers)
    assert r.status_code == 200
    assert [row["id"] for row in r.json()] == [e["id"]]

    r = client.patch(
        f"/admin/entries/{e['id']}",
        json={"status": "validated", "validator_note": "OK"},
        headers=validator_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "validated"
    assert body["validator_note"] == "OK"
    assert body["validated_at"] is not None

    assert client.get("/admin/entries?status=pending", headers=validator_headers).json() == []


def test_reject_with_note(client, user_headers, validator_headers, lang):
    e = buat_entri(client, user_headers, lang)
    r = client.patch(
        f"/admin/entries/{e['id']}",
        json={"status": "rejected", "validator_note": "Ejaan salah"},
        headers=validator_headers,
    )
    assert r.json()["status"] == "rejected"


def test_stats(client, user_headers, admin_headers, lang):
    e1 = buat_entri(client, user_headers, lang, "Tabea", "Halo")
    buat_entri(client, user_headers, lang, "Sumolo", "Terima kasih")
    client.patch(f"/admin/entries/{e1['id']}", json={"status": "validated"}, headers=admin_headers)

    r = client.get("/admin/stats", headers=admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_entries"] == 2
    assert body["by_status"] == {"validated": 1, "pending": 1}
    assert body["active_contributors"] == 1


def test_leaderboard_sorted(client, admin_headers, lang):
    from tests.conftest import register

    a = register(client, name="Rajin", email="rajin@test.id")
    b = register(client, name="Santai", email="santai@test.id")
    for i in range(3):
        e = buat_entri(client, a, lang, f"kata-{i}", f"arti-{i}")
        client.patch(f"/admin/entries/{e['id']}", json={"status": "validated"}, headers=admin_headers)
    e = buat_entri(client, b, lang, "satu", "satu")
    client.patch(f"/admin/entries/{e['id']}", json={"status": "validated"}, headers=admin_headers)

    rows = client.get("/admin/leaderboard", headers=admin_headers).json()
    assert [r["name"] for r in rows] == ["Rajin", "Santai"]
    assert [r["validated_count"] for r in rows] == [3, 1]
