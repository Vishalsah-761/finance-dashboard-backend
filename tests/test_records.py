import pytest


def _register_and_login(client, username, email, password, role="viewer"):
    client.post("/api/auth/register", json={
        "username": username, "email": email,
        "password": password, "role": role,
    })
    res = client.post("/api/auth/login",
                      json={"email": email, "password": password})
    return res.get_json()["data"]["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


SAMPLE_RECORD = {
    "amount": 1500.00,
    "type": "income",
    "category": "salary",
    "date": "2024-03-15",
    "notes": "March salary",
}


class TestRecordPermissions:
    def test_viewer_cannot_create(self, client, clean_db):
        token = _register_and_login(client, "v1", "v1@t.com", "pass1234", "viewer")
        res = client.post("/api/records/", json=SAMPLE_RECORD, headers=auth(token))
        assert res.status_code == 403

    def test_analyst_cannot_create(self, client, clean_db):
        token = _register_and_login(client, "a1", "a1@t.com", "pass1234", "analyst")
        res = client.post("/api/records/", json=SAMPLE_RECORD, headers=auth(token))
        assert res.status_code == 403

    def test_admin_can_create(self, client, clean_db):
        token = _register_and_login(client, "adm", "adm@t.com", "pass1234", "admin")
        res = client.post("/api/records/", json=SAMPLE_RECORD, headers=auth(token))
        assert res.status_code == 201

    def test_viewer_can_list(self, client, clean_db):
        token = _register_and_login(client, "v2", "v2@t.com", "pass1234", "viewer")
        res = client.get("/api/records/", headers=auth(token))
        assert res.status_code == 200

    def test_unauthenticated_cannot_list(self, client, clean_db):
        res = client.get("/api/records/")
        assert res.status_code == 401


class TestRecordCRUD:
    def setup_method(self):
        self._admin_token = None

    def _get_admin(self, client):
        if not self._admin_token:
            self._admin_token = _register_and_login(
                client, "admin2", "admin2@t.com", "pass1234", "admin"
            )
        return self._admin_token

    def test_create_and_get(self, client, clean_db):
        token = self._get_admin(client)
        create_res = client.post("/api/records/", json=SAMPLE_RECORD, headers=auth(token))
        assert create_res.status_code == 201
        record_id = create_res.get_json()["data"]["id"]

        get_res = client.get(f"/api/records/{record_id}", headers=auth(token))
        assert get_res.status_code == 200
        assert get_res.get_json()["data"]["amount"] == 1500.0

    def test_update_record(self, client, clean_db):
        token = self._get_admin(client)
        record_id = client.post(
            "/api/records/", json=SAMPLE_RECORD, headers=auth(token)
        ).get_json()["data"]["id"]

        res = client.patch(f"/api/records/{record_id}",
                           json={"amount": 2000.0}, headers=auth(token))
        assert res.status_code == 200
        assert res.get_json()["data"]["amount"] == 2000.0

    def test_soft_delete(self, client, clean_db):
        token = self._get_admin(client)
        record_id = client.post(
            "/api/records/", json=SAMPLE_RECORD, headers=auth(token)
        ).get_json()["data"]["id"]

        del_res = client.delete(f"/api/records/{record_id}", headers=auth(token))
        assert del_res.status_code == 200

        # Should now 404
        get_res = client.get(f"/api/records/{record_id}", headers=auth(token))
        assert get_res.status_code == 404

    def test_invalid_amount(self, client, clean_db):
        token = self._get_admin(client)
        bad = {**SAMPLE_RECORD, "amount": -100}
        res = client.post("/api/records/", json=bad, headers=auth(token))
        assert res.status_code == 422

    def test_invalid_category(self, client, clean_db):
        token = self._get_admin(client)
        bad = {**SAMPLE_RECORD, "category": "unicorn"}
        res = client.post("/api/records/", json=bad, headers=auth(token))
        assert res.status_code == 422
