import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def test_screening_id(tmp_path):
    # Login as screening officer
    login = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload test document
    img_path = str(tmp_path / "case_doc.jpg")
    img = np.full((300, 500, 3), 240, dtype=np.uint8)
    cv2.putText(img, "CASE TEST DOC", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(img_path, img)

    with open(img_path, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "IND", "is_synthetic": True},
            files={"file": ("case_doc.jpg", f, "image/jpeg")}
        )
    return res.json()["id"]


def test_case_creation_and_notes(test_screening_id):
    login = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Case
    create_res = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "screening_id": test_screening_id,
            "priority": "HIGH",
            "summary": "Suspected altered passport credential under investigation"
        }
    )
    assert create_res.status_code == 200
    case_data = create_res.json()
    assert case_data["case_number"].startswith("CASE-")
    assert case_data["status"] == "OPEN"
    assert case_data["priority"] == "HIGH"
    case_id = case_data["id"]

    # 2. Add Officer Note
    note_res = client.post(
        f"/api/v1/cases/{case_id}/notes",
        headers=headers,
        json={"text": "Contacted regional immigration liaison; awaiting physical database check."}
    )
    assert note_res.status_code == 200
    updated_case = note_res.json()
    assert len(updated_case["notes"]) >= 2
    assert "immigration liaison" in updated_case["notes"][-1]["text"]


def test_case_status_transitions(test_screening_id):
    login = client.post("/api/v1/auth/login", json={
        "email": "reviewer@verisight.gov.in",
        "password": "Reviewer@12345"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create case
    c_res = client.post(
        "/api/v1/cases",
        headers=headers,
        json={"screening_id": test_screening_id, "priority": "URGENT"}
    )
    case_id = c_res.json()["id"]

    # Transition to IN_REVIEW
    patch1 = client.patch(
        f"/api/v1/cases/{case_id}/status",
        headers=headers,
        json={"status": "IN_REVIEW"}
    )
    assert patch1.status_code == 200
    assert patch1.json()["status"] == "IN_REVIEW"

    # Resolve case with notes
    patch2 = client.patch(
        f"/api/v1/cases/{case_id}/status",
        headers=headers,
        json={
            "status": "RESOLVED",
            "resolution_notes": "Credential confirmed authentic; secondary physical checks verified security watermarks."
        }
    )
    assert patch2.status_code == 200
    res_data = patch2.json()
    assert res_data["status"] == "RESOLVED"
    assert res_data["resolution_notes"] is not None
    assert res_data["resolved_at"] is not None
