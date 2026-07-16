"""Happy-path auth + RBAC (Task 2)."""


def test_register_login_me(client):
    r = client.post(
        "/auth/register",
        json={"name": "Budi", "email": "budi@test.id", "password": "rahasia123"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["role"] == "user"

    r = client.post(
        "/auth/login",
        data={"username": "budi@test.id", "password": "rahasia123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "budi@test.id"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"name": "Budi", "email": "budi@test.id", "password": "rahasia123"},
    )
    r = client.post(
        "/auth/login",
        data={"username": "budi@test.id", "password": "salah"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_user_blocked_from_admin(client, user_headers):
    for path in ("/admin/entries", "/admin/stats", "/admin/leaderboard"):
        r = client.get(path, headers=user_headers)
        assert r.status_code == 403, path


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
