import pytest
import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.engines.face.verifier import (
    extract_document_portrait,
    evaluate_face_quality,
    compute_face_similarity,
    verify_document_vs_live
)
from backend.app.models import Screening, Document, AuditLog

client = TestClient(app)


def create_dummy_face_image(width=200, height=200, color=(180, 160, 140)):
    img = np.full((height, width, 3), color, dtype=np.uint8)
    cv2.circle(img, (70, 70), 12, (50, 40, 30), -1)
    cv2.circle(img, (130, 70), 12, (50, 40, 30), -1)
    cv2.ellipse(img, (100, 130), (35, 15), 0, 0, 180, (40, 30, 80), 4)
    return img


def test_face_quality_evaluation():
    face = create_dummy_face_image()
    quality = evaluate_face_quality(face)
    assert "blur_score" in quality
    assert "mean_luminance" in quality
    assert "resolution" in quality
    assert quality["resolution"] == (200, 200)


def test_face_similarity_computation():
    face1 = create_dummy_face_image()
    face2 = create_dummy_face_image()

    result = compute_face_similarity(face1, face2)
    assert "similarity_score" in result
    assert result["similarity_score"] > 0.85
    assert result["is_match"] is True
    assert result["confidence_band"] == "HIGH"
    assert "disclaimer" in result
    assert "privacy_notice" in result


def test_consent_enforcement_rejected():
    result = verify_document_vs_live(
        doc_image_path="nonexistent.jpg",
        live_image_bytes=b"fake",
        consent_granted=False
    )
    assert result["success"] is False
    assert result["error_code"] == "CONSENT_REQUIRED"


def test_api_face_verify_endpoint():
    # 1. Login as Screening Officer
    login = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get an existing screening from the seeded database
    db = SessionLocal()
    screening = db.query(Screening).first()
    assert screening is not None
    screening_id = screening.id
    db.close()

    # 3. Create dummy live image
    live_img = create_dummy_face_image(200, 250)
    _, buffer = cv2.imencode(".jpg", live_img)
    live_bytes = buffer.tobytes()

    # 4. Attempt verification WITHOUT consent -> Must fail with 400
    res_no_consent = client.post(
        f"/api/v1/face/{screening_id}/verify",
        headers=headers,
        data={"consent_granted": False},
        files={"live_image": ("live.jpg", live_bytes, "image/jpeg")}
    )
    assert res_no_consent.status_code == 400
    assert "consent" in res_no_consent.json()["detail"].lower()

    # 5. Perform verification WITH consent -> Must succeed
    res_verified = client.post(
        f"/api/v1/face/{screening_id}/verify",
        headers=headers,
        data={"consent_granted": True},
        files={"live_image": ("live.jpg", live_bytes, "image/jpeg")}
    )
    assert res_verified.status_code == 200
    data = res_verified.json()
    assert data["success"] is True
    assert "similarity_score" in data
    assert "threshold" in data
    assert "doc_portrait_b64" in data

    # 6. Verify audit log was recorded
    db2 = SessionLocal()
    audit = db2.query(AuditLog).filter(
        AuditLog.event_type == "FACE_VERIFICATION_PERFORMED",
        AuditLog.screening_id == screening_id
    ).first()
    assert audit is not None
    assert "similarity_score" in audit.metadata_json
    db2.close()
