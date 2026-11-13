import os
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import AuditLog

client = TestClient(app)


@pytest.fixture
def test_screening_id(tmp_path):
    # Screening Officer creates the screening
    login = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    img_path = str(tmp_path / "report_doc.jpg")
    img = np.full((300, 500, 3), 240, dtype=np.uint8)
    cv2.putText(img, "REPORT TEST DOC", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(img_path, img)

    with open(img_path, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "IND", "is_synthetic": True},
            files={"file": ("report_doc.jpg", f, "image/jpeg")}
        )
    return res.json()["id"]


def test_audit_chain_verification():
    login = client.post("/api/v1/auth/login", json={
        "email": "auditor@verisight.gov.in",
        "password": "Auditor@12345"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/audit/verify-integrity", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_intact"] is True
    assert data["total_blocks_verified"] > 0
    assert data["latest_hash"] is not None


def test_pdf_report_generation(test_screening_id):
    login = client.post("/api/v1/auth/login", json={
        "email": "auditor@verisight.gov.in",
        "password": "Auditor@12345"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/reports/{test_screening_id}/download", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    # PDF magic byte verification
    assert res.content.startswith(b"%PDF-")
    assert len(res.content) > 1000
