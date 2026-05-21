import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from backend.main import app
from backend.database.db import get_session

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def override_get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

def test_delete_poem_flow():
    SQLModel.metadata.create_all(engine)
    client = TestClient(app)

    reg1 = client.post("/api/register", json={
        "username": "poet1",
        "email": "poet1@example.com",
        "password": "password123"
    })
    assert reg1.status_code == 200

    login1 = client.post("/api/login", json={
        "username": "poet1",
        "password": "password123"
    })
    assert login1.status_code == 200
    token1 = login1.json()["access_token"]

    reg2 = client.post("/api/register", json={
        "username": "poet2",
        "email": "poet2@example.com",
        "password": "password123"
    })
    assert reg2.status_code == 200

    login2 = client.post("/api/login", json={
        "username": "poet2",
        "password": "password123"
    })
    assert login2.status_code == 200
    token2 = login2.json()["access_token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    create_res = client.post("/api/poems", json={"content": "Hello World", "is_public": False}, headers=headers1)
    assert create_res.status_code == 200
    poem_id = create_res.json()["id"]

    del_no_auth = client.delete(f"/api/poems/{poem_id}")
    assert del_no_auth.status_code == 401

    del_forbidden = client.delete(f"/api/poems/{poem_id}", headers=headers2)
    assert del_forbidden.status_code == 403

    del_success = client.delete(f"/api/poems/{poem_id}", headers=headers1)
    assert del_success.status_code == 200
    assert del_success.json()["status"] == "success"

    del_not_found = client.delete(f"/api/poems/{poem_id}", headers=headers1)
    assert del_not_found.status_code == 404

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_delete_poem_flow()
