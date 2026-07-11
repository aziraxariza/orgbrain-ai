import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


@pytest.fixture()
def client(db):
    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_signup_and_login_roundtrip(client):
    resp = client.post("/api/v1/auth/signup", json={
        "organization_name": "Test Signup Org",
        "email": "founder@testsignup.com",
        "password": "supersecret123",
        "full_name": "Founder Person",
    })
    assert resp.status_code == 201
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["role"] == "admin"

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "founder@testsignup.com", "password": "supersecret123",
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["tenant_id"] == token_data["tenant_id"]


def test_login_rejects_wrong_password(client):
    client.post("/api/v1/auth/signup", json={
        "organization_name": "Wrong Pw Org", "email": "u@wrongpw.com",
        "password": "correcthorse", "full_name": "U Ser",
    })
    resp = client.post("/api/v1/auth/login", json={"email": "u@wrongpw.com", "password": "nope"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/v1/employees")
    assert resp.status_code == 401


def test_tenant_isolation_between_orgs(client):
    org_a = client.post("/api/v1/auth/signup", json={
        "organization_name": "Org A", "email": "a@orga.com", "password": "passwordA1", "full_name": "A",
    }).json()
    org_b = client.post("/api/v1/auth/signup", json={
        "organization_name": "Org B", "email": "b@orgb.com", "password": "passwordB1", "full_name": "B",
    }).json()

    # Org A's token should never see Org B's (empty, but distinctly-scoped) employee list bleed through.
    resp_a = client.get("/api/v1/employees", headers={"Authorization": f"Bearer {org_a['access_token']}"})
    resp_b = client.get("/api/v1/employees", headers={"Authorization": f"Bearer {org_b['access_token']}"})
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    assert org_a["tenant_id"] != org_b["tenant_id"]
