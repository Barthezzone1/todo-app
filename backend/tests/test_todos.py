def test_register_returns_api_key(client):
    res = client.post("/register", json={"username": "testuser"})
    assert res.status_code == 200

    data = res.json()
    assert data["username"] == "testuser"
    assert "api_key" in data
    assert isinstance(data["api_key"], str)
    assert len(data["api_key"]) > 0


def test_todo_crud_flow(client):
    # Rejestracja i pobranie api_key
    res = client.post("/register", json={"username": "user1"})
    assert res.status_code == 200
    api_key = res.json()["api_key"]

    # UŻYWAMY X-API-Key
    headers = {"X-API-Key": api_key}

    # Początkowo lista zadań jest pusta
    res = client.get("/todos", headers=headers)
    assert res.status_code == 200
    assert res.json() == []

    # Tworzymy zadanie
    res = client.post("/todos", json={"title": "Kup mleko"}, headers=headers)
    assert res.status_code == 201
    todo = res.json()
    todo_id = todo["id"]
    assert todo["title"] == "Kup mleko"
    assert todo["done"] is False

    # Lista powinna mieć 1 zadanie
    res = client.get("/todos", headers=headers)
    assert res.status_code == 200
    todos = res.json()
    assert len(todos) == 1
    assert todos[0]["id"] == todo_id

    # Aktualizujemy zadanie (done=True)
    res = client.put(
        f"/todos/{todo_id}",
        json={"done": True},
        headers=headers,
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["done"] is True

    # Statystyki (total=1, done=1, not_done=0)
    res = client.get("/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total"] == 1
    assert stats["done"] == 1
    assert stats["not_done"] == 0

    # Usuwamy zadanie
    res = client.delete(f"/todos/{todo_id}", headers=headers)
    assert res.status_code == 204

    # Lista znów pusta
    res = client.get("/todos", headers=headers)
    assert res.status_code == 200
    assert res.json() == []


def test_unauthorized_access_is_blocked(client):
    # brak nagłówka -> 401
    res = client.get("/todos")
    assert res.status_code == 401

    # zły klucz w X-API-Key -> 401
    res = client.get("/todos", headers={"X-API-Key": "BAD_KEY"})
    assert res.status_code == 401