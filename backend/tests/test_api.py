from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_school_registration_and_tenant_isolation():
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        def register(code):
            response = client.post("/api/auth/register", json={
                "school_name": "Test School " + code,
                "school_code": code,
                "curriculum": "CBC",
                "admin_name": "Test Administrator",
                "email": "admin@example.com",
                "password": "StrongTestPassword!2026"
            })
            assert response.status_code == 201, response.text
            return response.json()["access_token"]

        token_a = register("TST" + suffix.upper())
        token_b = register("TST" + uuid4().hex[:10].upper())
        headers_a = {"Authorization": "Bearer " + token_a}
        headers_b = {"Authorization": "Bearer " + token_b}

        created = client.post("/api/learners", headers=headers_a, json={
            "admission_number": "ADM-" + suffix,
            "first_name": "Amina",
            "last_name": "Test",
            "gender": "Female"
        })
        assert created.status_code == 201, created.text
        assert len(client.get("/api/learners", headers=headers_a).json()) == 1
        assert client.get("/api/learners", headers=headers_b).json() == []
