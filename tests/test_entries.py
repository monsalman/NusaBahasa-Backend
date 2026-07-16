"""Happy-path CRUD + search entries (Task 3), termasuk PATCH/DELETE & ?mine=true."""


def buat_entri(client, headers, lang, daerah="Tabea", indonesia="Halo", type_="kata"):
    r = client.post(
        "/entries",
        json={
            "language_id": lang.id,
            "text_daerah": daerah,
            "text_indonesia": indonesia,
            "type": type_,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_entry_pending(client, user_headers, lang):
    entry = buat_entri(client, user_headers, lang)
    assert entry["status"] == "pending"
    assert entry["text_daerah"] == "Tabea"


def test_public_list_only_validated(client, user_headers, admin_headers, lang):
    e1 = buat_entri(client, user_headers, lang, "Tabea", "Halo")
    buat_entri(client, user_headers, lang, "Sumolo", "Terima kasih")
    # Validasi salah satu
    r = client.patch(f"/admin/entries/{e1['id']}", json={"status": "validated"}, headers=admin_headers)
    assert r.status_code == 200

    r = client.get("/entries")
    assert r.status_code == 200
    ids = [row["id"] for row in r.json()]
    assert ids == [e1["id"]]


def test_search_by_text(client, user_headers, admin_headers, lang):
    e = buat_entri(client, user_headers, lang, "Wewene", "Perempuan")
    client.patch(f"/admin/entries/{e['id']}", json={"status": "validated"}, headers=admin_headers)

    assert len(client.get("/entries?q=wewene").json()) == 1
    assert len(client.get("/entries?q=perempuan").json()) == 1
    assert client.get("/entries?q=tidakada").json() == []


def test_get_detail(client, user_headers, lang):
    e = buat_entri(client, user_headers, lang)
    r = client.get(f"/entries/{e['id']}")
    assert r.status_code == 200
    assert r.json()["audio_files"] == []
    assert client.get("/entries/99999").status_code == 404


def test_mine_returns_own_all_statuses(client, user_headers, admin_headers, lang):
    e1 = buat_entri(client, user_headers, lang, "Tabea", "Halo")
    e2 = buat_entri(client, user_headers, lang, "Sumolo", "Terima kasih")
    client.patch(f"/admin/entries/{e1['id']}", json={"status": "validated"}, headers=admin_headers)
    # Entri milik orang lain tidak boleh ikut
    buat_entri(client, admin_headers, lang, "Punya admin", "x")

    r = client.get("/entries?mine=true", headers=user_headers)
    assert r.status_code == 200
    ids = {row["id"] for row in r.json()}
    assert ids == {e1["id"], e2["id"]}
    statuses = {row["status"] for row in r.json()}
    assert statuses == {"validated", "pending"}


def test_mine_requires_login(client):
    assert client.get("/entries?mine=true").status_code == 401


def test_owner_edits_while_pending(client, user_headers, lang):
    e = buat_entri(client, user_headers, lang, "Tabae", "Halo")  # typo disengaja
    r = client.patch(
        f"/entries/{e['id']}", json={"text_daerah": "Tabea"}, headers=user_headers
    )
    assert r.status_code == 200
    assert r.json()["text_daerah"] == "Tabea"


def test_owner_cannot_edit_after_validated(client, user_headers, admin_headers, lang):
    e = buat_entri(client, user_headers, lang)
    client.patch(f"/admin/entries/{e['id']}", json={"status": "validated"}, headers=admin_headers)
    r = client.patch(f"/entries/{e['id']}", json={"text_daerah": "X"}, headers=user_headers)
    assert r.status_code == 403


def test_admin_edits_anytime(client, user_headers, admin_headers, lang):
    e = buat_entri(client, user_headers, lang)
    client.patch(f"/admin/entries/{e['id']}", json={"status": "validated"}, headers=admin_headers)
    r = client.patch(f"/entries/{e['id']}", json={"text_indonesia": "Salam"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["text_indonesia"] == "Salam"


def test_other_user_cannot_edit(client, user_headers, lang):
    from tests.conftest import register

    e = buat_entri(client, user_headers, lang)
    other = register(client, name="Lain", email="lain@test.id")
    r = client.patch(f"/entries/{e['id']}", json={"text_daerah": "X"}, headers=other)
    assert r.status_code == 403


def test_delete_admin_only(client, user_headers, admin_headers, lang):
    e = buat_entri(client, user_headers, lang)
    assert client.delete(f"/entries/{e['id']}", headers=user_headers).status_code == 403
    assert client.delete(f"/entries/{e['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/entries/{e['id']}").status_code == 404
    assert client.delete("/entries/99999", headers=admin_headers).status_code == 404


def test_delete_entry_with_quiz_progress(client, user_headers, admin_headers, lang):
    e = buat_entri(client, user_headers, lang)
    r = client.post(
        "/quiz/progress",
        json={"entry_id": e["id"], "score": 0.9, "streak_data": {"streak": 2}},
        headers=user_headers,
    )
    assert r.status_code in (200, 201), r.text
    assert client.delete(f"/entries/{e['id']}", headers=admin_headers).status_code == 204


def test_languages_public(client, lang):
    r = client.get("/languages")
    assert r.status_code == 200
    assert r.json()[0]["code"] == "tnt"
