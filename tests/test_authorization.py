from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    original_capabilities = deepcopy(app_module.capabilities)
    monkeypatch.setattr(app_module, "practice_leads", [{
        "username": "technology.lead",
        "display_name": "Technology Practice Lead",
        "password_hash": app_module.hash_password("correct-password"),
        "practice_areas": ["Technology"],
    }])
    app_module.active_sessions.clear()
    with TestClient(app_module.app) as test_client:
        yield test_client
    app_module.capabilities.clear()
    app_module.capabilities.update(original_capabilities)
    app_module.active_sessions.clear()


def test_unregister_requires_practice_lead_authentication(client):
    response = client.delete(
        "/capabilities/Cloud Architecture/unregister",
        params={"email": "alice.smith@slalom.com"},
    )

    assert response.status_code == 401
    assert "alice.smith@slalom.com" in app_module.capabilities["Cloud Architecture"]["consultants"]


def test_invalid_credentials_are_rejected(client):
    response = client.post("/auth/login", json={
        "username": "technology.lead",
        "password": "wrong-password",
    })

    assert response.status_code == 401


def test_practice_lead_can_unregister_consultant_in_own_practice(client):
    login_response = client.post("/auth/login", json={
        "username": "technology.lead",
        "password": "correct-password",
    })

    response = client.delete(
        "/capabilities/Cloud Architecture/unregister",
        params={"email": "alice.smith@slalom.com"},
    )

    assert login_response.status_code == 200
    assert response.status_code == 200
    assert "alice.smith@slalom.com" not in app_module.capabilities["Cloud Architecture"]["consultants"]


def test_practice_lead_cannot_manage_another_practice(client):
    client.post("/auth/login", json={
        "username": "technology.lead",
        "password": "correct-password",
    })

    response = client.delete(
        "/capabilities/Digital Strategy/unregister",
        params={"email": "liam.anderson@slalom.com"},
    )

    assert response.status_code == 403
    assert "liam.anderson@slalom.com" in app_module.capabilities["Digital Strategy"]["consultants"]


def test_logout_invalidates_session(client):
    client.post("/auth/login", json={
        "username": "technology.lead",
        "password": "correct-password",
    })

    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/session").json() == {"authenticated": False}