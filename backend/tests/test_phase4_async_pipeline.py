import os
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import ScreeningStatus
from backend.app.services.pipeline import execute_screening_pipeline

client = TestClient(app)


@pytest.fixture
def officer_token():
    res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


def create_mock_passport_image(path: str, blurred: bool = False):
    img = np.ones((600, 800, 3), dtype=np.uint8) * 240
    if blurred:
        # Extreme blur that drops Laplacian variance below threshold
        img = cv2.GaussianBlur(img, (51, 51), 0)
    else:
        cv2.putText(img, "PASSPORT REPUBLIC", (250, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "Surname: VERMA", (320, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(img, "Given Names: VIKRAM", (320, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        # High contrast edges to pass blur check
        for y in range(300, 450, 20):
            cv2.line(img, (100, y), (700, y), (10, 10, 10), 2)

        l1 = "P<INDVERMA<<VIKRAM<<<<<<<<<<<<<<<<<<<<<<<<<<"
        l2 = "Z9182374<9IND8806150M3006151<<<<<<<<<<<<<<0<"
        cv2.putText(img, l1, (40, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        cv2.putText(img, l2, (40, 560), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img)


def test_async_intake_and_status_tracking(tmp_path, officer_token):
    img_path = str(tmp_path / "valid_passport.png")
    create_mock_passport_image(img_path, blurred=False)

    headers = {"Authorization": f"Bearer {officer_token}"}
    with open(img_path, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            files={"file": ("valid_passport.png", f, "image/png")},
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "IND", "sync": "false"}
        )

    assert res.status_code == 200
    screening = res.json()
    screening_id = screening["id"]
    assert "reference_no" in screening
    assert screening["status"] in ("PENDING", "PROCESSING", "COMPLETED")

    # In Starlette TestClient, background tasks run upon response finish
    status_res = client.get(f"/api/v1/screenings/{screening_id}/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["id"] == screening_id
    assert status_data["status"] == "COMPLETED"
    assert status_data["overall_progress"] == 100

    stages = status_data["stages"]
    assert "QUALITY_ASSESSMENT" in stages
    assert "PREPROCESSING" in stages
    assert "OCR_EXTRACTION" in stages
    assert "MRZ_PARSING" in stages
    assert "VALIDATION_CROSSCHECK" in stages
    assert "FORENSICS_ANALYSIS" in stages
    assert "RISK_SCORING" in stages

    for stage_name, stage_info in stages.items():
        assert stage_info["status"] == "COMPLETED"
        assert stage_info["timing_ms"] is not None
    assert "MRZ_PARSING" in stages
    assert "VALIDATION_CROSSCHECK" in stages
    assert "FORENSICS_ANALYSIS" in stages
    assert "RISK_SCORING" in stages

    for stage_name, stage_info in stages.items():
        assert stage_info["status"] == "COMPLETED"
        assert stage_info["timing_ms"] is not None


def test_poor_quality_rejection_halts_downstream_stages(tmp_path, officer_token):
    """
    Submitting an extremely blurry image must fail QUALITY_ASSESSMENT,
    set REJECTED_POOR_QUALITY, mark downstream stages DEPENDENCY_FAILED,
    and generate explicit rescan instructions.
    """
    img_path = str(tmp_path / "severe_blur.png")
    create_mock_passport_image(img_path, blurred=True)

    headers = {"Authorization": f"Bearer {officer_token}"}
    with open(img_path, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            files={"file": ("severe_blur.png", f, "image/png")},
            data={"document_type": "PASSPORT_TD3", "sync": "true"}
        )

    assert res.status_code == 200
    screening_id = res.json()["id"]

    status_res = client.get(f"/api/v1/screenings/{screening_id}/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["status"] == "REJECTED_POOR_QUALITY"
    assert status_data["rescan_instructions"] is not None
    assert "Rescan" in status_data["rescan_instructions"]

    stages = status_data["stages"]
    assert stages["QUALITY_ASSESSMENT"]["status"] == "FAILED"
    # All downstream stages must be marked DEPENDENCY_FAILED (honest failure propagation)
    assert stages["PREPROCESSING"]["status"] == "DEPENDENCY_FAILED"
    assert stages["OCR_EXTRACTION"]["status"] == "DEPENDENCY_FAILED"
    assert stages["MRZ_PARSING"]["status"] == "DEPENDENCY_FAILED"
    assert stages["VALIDATION_CROSSCHECK"]["status"] == "DEPENDENCY_FAILED"
    assert stages["FORENSICS_ANALYSIS"]["status"] == "DEPENDENCY_FAILED"
    assert stages["RISK_SCORING"]["status"] == "DEPENDENCY_FAILED"


def test_cancel_screening_aborts_execution(tmp_path, officer_token):
    img_path = str(tmp_path / "cancel_test.png")
    create_mock_passport_image(img_path, blurred=False)

    headers = {"Authorization": f"Bearer {officer_token}"}
    with open(img_path, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            files={"file": ("cancel_test.png", f, "image/png")},
            data={"document_type": "PASSPORT_TD3", "sync": "false"}
        )
    screening_id = res.json()["id"]

    # Cancel screening
    cancel_res = client.post(f"/api/v1/screenings/{screening_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    cancel_data = cancel_res.json()
    assert cancel_data["status"] == "ABORTED"
    assert cancel_data["is_aborted"] is True


def test_retry_screening_restarts_pipeline(tmp_path, officer_token):
    img_path = str(tmp_path / "retry_test.png")
    create_mock_passport_image(img_path, blurred=False)

    headers = {"Authorization": f"Bearer {officer_token}"}
    with open(img_path, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            files={"file": ("retry_test.png", f, "image/png")},
            data={"document_type": "PASSPORT_TD3", "sync": "true"}
        )
    screening_id = res.json()["id"]

    # Trigger retry
    retry_res = client.post(f"/api/v1/screenings/{screening_id}/retry", headers=headers)
    assert retry_res.status_code == 200
    retry_data = retry_res.json()
    assert retry_data["status"] in ("PENDING", "PROCESSING", "COMPLETED")
