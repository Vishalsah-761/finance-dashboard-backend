import pytest


def _token(client, username, email, role):
    client.post("/api/auth/register", json={
        "username": username, "email": email,
        "password": "pass1234", "role": role,
    })
    res = client.post("/api/auth/login",
                      json={"email": email, "password": "pass1234"})
    return res.get_json()["data"]["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestDashboardAccess:
    def test_viewer_cannot_access_summary(self, client, clean_db):
        token = _token(client, "vd", "vd@t.com", "viewer")
        res = client.get("/api/dashboard/summary", headers=auth(token))
        assert res.status_code == 403

    def test_analyst_can_access_summary(self, client, clean_db):
        token = _token(client, "an", "an@t.com", "analyst")
        res = client.get("/api/dashboard/summary", headers=auth(token))
        assert res.status_code == 200

    def test_admin_can_access_all_endpoints(self, client, clean_db):
        token = _token(client, "adm", "adm@t.com", "admin")
        for endpoint in ["/api/dashboard/summary",
                         "/api/dashboard/categories",
                         "/api/dashboard/monthly-trends",
                         "/api/dashboard/weekly-trends"]:
            res = client.get(endpoint, headers=auth(token))
            assert res.status_code == 200, f"Failed: {endpoint}"

    def test_viewer_can_access_recent_activity(self, client, clean_db):
        token = _token(client, "vr", "vr@t.com", "viewer")
        res = client.get("/api/dashboard/recent-activity", headers=auth(token))
        assert res.status_code == 200

    def test_summary_structure(self, client, clean_db):
        token = _token(client, "ad2", "ad2@t.com", "admin")
        res = client.get("/api/dashboard/summary", headers=auth(token))
        data = res.get_json()["data"]
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data
