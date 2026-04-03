import pytest
import json


def register(client, username, email, password, role="viewer"):
    return client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "role": role,
    })


def login(client, email, password):
    return client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })


class TestRegister:
    def test_register_success(self, client, clean_db):
        res = register(client, "alice", "alice@test.com", "password123")
        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["role"] == "viewer"

    def test_register_duplicate_email(self, client, clean_db):
        register(client, "alice", "alice@test.com", "password123")
        res = register(client, "alice2", "alice@test.com", "password123")
        assert res.status_code == 409

    def test_register_invalid_email(self, client, clean_db):
        res = register(client, "bob", "not-an-email", "password123")
        assert res.status_code == 422

    def test_register_short_password(self, client, clean_db):
        res = register(client, "bob", "bob@test.com", "abc")
        assert res.status_code == 422


class TestLogin:
    def test_login_success(self, client, clean_db):
        register(client, "charlie", "charlie@test.com", "pass1234")
        res = login(client, "charlie@test.com", "pass1234")
        assert res.status_code == 200
        assert "access_token" in res.get_json()["data"]

    def test_login_wrong_password(self, client, clean_db):
        register(client, "dave", "dave@test.com", "pass1234")
        res = login(client, "dave@test.com", "wrong")
        assert res.status_code == 401

    def test_login_unknown_email(self, client, clean_db):
        res = login(client, "ghost@test.com", "pass1234")
        assert res.status_code == 401


class TestMe:
    def test_me_requires_auth(self, client, clean_db):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_me_returns_profile(self, client, clean_db):
        register(client, "eve", "eve@test.com", "pass1234")
        token = login(client, "eve@test.com", "pass1234").get_json()["data"]["access_token"]
        res = client.get("/api/auth/me",
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.get_json()["data"]["email"] == "eve@test.com"
