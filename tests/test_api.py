from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import certificates


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(certificates, "OUTPUT_DIR", tmp_path / "certificates")
    monkeypatch.setenv("CERTIFICATE_OUTPUT_DIR", str(tmp_path / "certificates"))
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def sample_payload():
    return {
        "event_name": "Python Workshop",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Ananya Rao", "email": "ananya@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"},
        ],
    }


def test_create_job_and_generate_certificates(client):
    response = client.post("/api/jobs/", json=sample_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["total"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0


def test_input_validation(client):
    payload = sample_payload()
    payload["recipients"][0]["email"] = "not-an-email"
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 422


def test_job_status_and_recipient_list(client):
    created = client.post("/api/jobs/", json=sample_payload()).json()
    job_id = created["id"]

    status_response = client.get(f"/api/jobs/{job_id}/")
    assert status_response.status_code == 200
    assert status_response.json()["processed"] == 2

    recipients_response = client.get(f"/api/jobs/{job_id}/certificates/")
    assert recipients_response.status_code == 200
    assert recipients_response.json()["total"] == 2


def test_download_individual_pdf(client):
    created = client.post("/api/jobs/", json=sample_payload()).json()
    recipients = client.get(f"/api/jobs/{created['id']}/certificates/").json()["recipients"]
    response = client.get(recipients[0]["download_url"])
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_download_job_zip(client):
    created = client.post("/api/jobs/", json=sample_payload()).json()
    response = client.get(f"/api/jobs/{created['id']}/download/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


def test_one_generation_failure_does_not_stop_other_recipients(client, monkeypatch):
    original = certificates.generate_certificate_pdf

    def flaky_generator(recipient_name, event_name, issue_date, recipient_id):
        if recipient_name == "Ananya Rao":
            raise RuntimeError("Simulated PDF failure")
        return original(recipient_name, event_name, issue_date, recipient_id)

    monkeypatch.setattr(certificates, "generate_certificate_pdf", flaky_generator)
    response = client.post("/api/jobs/", json=sample_payload())
    data = response.json()

    assert response.status_code == 201
    assert data["status"] == "PARTIALLY_COMPLETED"
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert data["processed"] == 2
