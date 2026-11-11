from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_school_registration_tenant_isolation_and_marks_workflow():
    suffix = uuid4().hex[:10].upper()
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

        token_a = register("TST" + suffix)
        token_b = register("TST" + uuid4().hex[:10].upper())
        headers_a = {"Authorization": "Bearer " + token_a}
        headers_b = {"Authorization": "Bearer " + token_b}

        class_row = client.post("/api/classes", headers=headers_a, json={"name":"Grade 5","curriculum":"CBC","stream":"East"})
        assert class_row.status_code == 201, class_row.text
        learner = client.post("/api/learners", headers=headers_a, json={
            "admission_number":"ADM-"+suffix,"first_name":"Amina","last_name":"Test",
            "gender":"Female","class_id":class_row.json()["id"]
        })
        assert learner.status_code == 201, learner.text
        subject = client.post("/api/subjects", headers=headers_a, json={"code":"MATH","name":"Mathematics","curriculum":"CBC"})
        exam = client.post("/api/exams", headers=headers_a, json={"name":"Term 1","academic_year":"2026","term":"Term 1","exam_type":"END_TERM"})
        assert subject.status_code == 201 and exam.status_code == 201

        paper = client.post("/api/exams/"+str(exam.json()["id"])+"/papers",headers=headers_a,json={
            "subject_id":subject.json()["id"],"class_id":class_row.json()["id"],"max_score":100
        })
        assert paper.status_code == 201, paper.text
        saved = client.put("/api/papers/"+str(paper.json()["id"])+"/marks",headers=headers_a,json={
            "marks":[{"learner_id":learner.json()["id"],"score":78}]
        })
        assert saved.status_code == 200, saved.text
        roster = client.get("/api/papers/"+str(paper.json()["id"])+"/marks",headers=headers_a)
        assert roster.status_code == 200
        assert roster.json()[0]["score"] == 78
        report = client.get("/api/reports/exam/"+str(exam.json()["id"]),headers=headers_a)
        assert report.status_code == 200
        assert report.json()[0]["percent"] == 78

        assert len(client.get("/api/learners",headers=headers_a).json()) == 1
        assert client.get("/api/learners",headers=headers_b).json() == []
        assert client.get("/api/exams/"+str(exam.json()["id"])+"/papers",headers=headers_b).status_code == 404
