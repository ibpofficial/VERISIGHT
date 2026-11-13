import pytest
import os
import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import RiskLevel, CaseStatus

client = TestClient(app)


def create_sample_passport_image(tmp_path):
    img = np.full((600, 850, 3), 245, dtype=np.uint8)
    
    # Document title
    cv2.putText(img, "REPUBLIC OF INDIA / PASSPORT", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    
    # Visual inspection zone fields
    cv2.putText(img, "Surname: SHARMA", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Given Names: AARAV", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Nationality: IND", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Date of Birth: 15/08/1990", (50, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Sex: M", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Passport No: L1234567", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(img, "Date of Expiry: 14/08/2030", (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Face portrait area
    face_crop = np.full((240, 200, 3), (180, 160, 140), dtype=np.uint8)
    cv2.circle(face_crop, (70, 70), 12, (50, 40, 30), -1)
    cv2.circle(face_crop, (130, 70), 12, (50, 40, 30), -1)
    cv2.ellipse(face_crop, (100, 130), (35, 15), 0, 0, 180, (40, 30, 80), 4)
    img[120:360, 50:250] = face_crop
    
    # MRZ lines
    mrz1 = "P<INDSHARMA<<AARAV<<<<<<<<<<<<<<<<<<<<<<<<<<"
    mrz2 = "L1234567<1IND9008158M3008144<<<<<<<<<<<<<<02"
    cv2.putText(img, mrz1, (40, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 2)
    cv2.putText(img, mrz2, (40, 560), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 2)
    
    path = str(tmp_path / "e2e_passport.jpg")
    cv2.imwrite(path, img)
    return path


def test_complete_e2e_workflow(tmp_path):
    """
    Complete end-to-end lifecycle verification:
    1. Authenticate Officer
    2. Upload document & Ingest
    3. Quality Pre-flight
    4. OCR Extraction & Correction
    5. MRZ Verification
    6. Forensic Laboratory (ELA, Metadata, Texture, Alignment, Portrait)
    7. Biometric Face Match (Consent-gated)
    8. Risk Engine Evaluation
    9. Supervisory Risk Override (Senior Reviewer)
    10. Case Creation, Notes, & Resolution
    11. 5-Page PDF Dossier Generation
    12. Auditor Cryptographic Chain Verification
    """
    # -------------------------------------------------------------
    # Step 1: Login as Screening Officer
    # -------------------------------------------------------------
    login_officer = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    assert login_officer.status_code == 200
    officer_token = login_officer.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    # -------------------------------------------------------------
    # Step 2: Ingest Document
    # -------------------------------------------------------------
    img_path = create_sample_passport_image(tmp_path)
    with open(img_path, "rb") as f:
        res_ingest = client.post(
            "/api/v1/screenings",
            headers=officer_headers,
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "IND", "is_synthetic": True},
            files={"file": ("passport.jpg", f, "image/jpeg")}
        )
    assert res_ingest.status_code in [200, 201]
    screening = res_ingest.json()
    screening_id = screening["id"]
    assert screening["reference_no"].startswith("VS-")

    # -------------------------------------------------------------
    # Step 3: Optical Quality Assessment Check
    # -------------------------------------------------------------
    res_quality = client.get(f"/api/v1/screenings/{screening_id}/quality", headers=officer_headers)
    assert res_quality.status_code == 200
    quality = res_quality.json()
    assert "overall_score" in quality
    assert "blur_score" in quality
    assert "readability_score" in quality

    # -------------------------------------------------------------
    # Step 4: OCR Extraction & Field Correction
    # -------------------------------------------------------------
    res_fields = client.get(f"/api/v1/screenings/{screening_id}/fields", headers=officer_headers)
    assert res_fields.status_code == 200
    fields = res_fields.json()
    assert len(fields) > 0
    
    # Correct first field
    field_to_correct = fields[0]
    res_corr = client.patch(
        f"/api/v1/screenings/{screening_id}/fields/{field_to_correct['id']}",
        headers=officer_headers,
        json={"new_value": "VERIFIED_VAL", "notes": "E2E Officer optical check"}
    )
    assert res_corr.status_code == 200
    assert res_corr.json()["current_value"] == "VERIFIED_VAL"
    assert res_corr.json()["is_corrected"] is True

    # -------------------------------------------------------------
    # Step 5: MRZ Verification Check
    # -------------------------------------------------------------
    res_mrz = client.get(f"/api/v1/screenings/{screening_id}/mrz", headers=officer_headers)
    assert res_mrz.status_code == 200
    mrz = res_mrz.json()
    assert "format" in mrz
    assert "composite_check" in mrz

    # -------------------------------------------------------------
    # Step 6: Multi-Factor Forensics
    # -------------------------------------------------------------
    res_forensics = client.get(f"/api/v1/forensics/{screening_id}", headers=officer_headers)
    assert res_forensics.status_code == 200
    findings = res_forensics.json()
    assert isinstance(findings, list)

    res_heatmap = client.get(f"/api/v1/forensics/{screening_id}/heatmap", headers=officer_headers)
    assert res_heatmap.status_code == 200
    assert res_heatmap.headers["content-type"] == "image/jpeg"

    # -------------------------------------------------------------
    # Step 7: Ephemeral Biometric Face Verification
    # -------------------------------------------------------------
    live_face = np.full((200, 200, 3), (180, 160, 140), dtype=np.uint8)
    _, live_buf = cv2.imencode(".jpg", live_face)
    res_face = client.post(
        f"/api/v1/face/{screening_id}/verify",
        headers=officer_headers,
        data={"consent_granted": "true"},
        files={"live_image": ("live.jpg", live_buf.tobytes(), "image/jpeg")}
    )
    assert res_face.status_code == 200
    face_data = res_face.json()
    assert face_data["success"] is True
    assert "similarity_score" in face_data

    # -------------------------------------------------------------
    # Step 8: Risk Engine Evaluation
    # -------------------------------------------------------------
    res_risk = client.get(f"/api/v1/risk/{screening_id}", headers=officer_headers)
    assert res_risk.status_code == 200
    risk = res_risk.json()
    assert risk["risk_level"] in [RiskLevel.CLEAR.value, RiskLevel.REVIEW.value, RiskLevel.HIGH_RISK.value]
    assert "composite_score" in risk

    # -------------------------------------------------------------
    # Step 9: Supervisory Risk Override by Senior Reviewer
    # -------------------------------------------------------------
    login_reviewer = client.post("/api/v1/auth/login", json={
        "email": "reviewer@verisight.gov.in",
        "password": "Reviewer@12345"
    })
    assert login_reviewer.status_code == 200
    reviewer_token = login_reviewer.json()["access_token"]
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    res_override = client.post(
        f"/api/v1/risk/{screening_id}/override",
        headers=reviewer_headers,
        json={"override_level": RiskLevel.REVIEW.value, "reason": "Supervisory secondary review mandated"}
    )
    assert res_override.status_code == 200
    assert res_override.json()["reviewer_override_level"] == RiskLevel.REVIEW.value

    # -------------------------------------------------------------
    # Step 10: Investigation Center Case Creation & Notes
    # -------------------------------------------------------------
    res_case_create = client.post(
        "/api/v1/cases",
        headers=reviewer_headers,
        json={
            "screening_id": screening_id,
            "priority": "HIGH",
            "summary": "Flagged for manual secondary inspection",
            "assigned_officer_id": None
        }
    )
    assert res_case_create.status_code in [200, 201]
    case_obj = res_case_create.json()
    case_id = case_obj["id"]

    res_note = client.post(
        f"/api/v1/cases/{case_id}/notes",
        headers=reviewer_headers,
        json={"text": "Examined micro-print patterns and UV watermark indicators. Clear to proceed."}
    )
    assert res_note.status_code == 200

    res_status = client.patch(
        f"/api/v1/cases/{case_id}/status",
        headers=reviewer_headers,
        json={"status": CaseStatus.RESOLVED.value, "resolution_notes": "Cross-verified with consular visual standards."}
    )
    assert res_status.status_code == 200
    assert res_status.json()["status"] == CaseStatus.RESOLVED.value

    # -------------------------------------------------------------
    # Step 11: Institutional PDF Dossier Export
    # -------------------------------------------------------------
    res_pdf = client.get(f"/api/v1/reports/{screening_id}/download", headers=officer_headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000

    # -------------------------------------------------------------
    # Step 12: Compliance Auditor Cryptographic Chain Verification
    # -------------------------------------------------------------
    login_auditor = client.post("/api/v1/auth/login", json={
        "email": "auditor@verisight.gov.in",
        "password": "Auditor@12345"
    })
    assert login_auditor.status_code == 200
    auditor_token = login_auditor.json()["access_token"]
    auditor_headers = {"Authorization": f"Bearer {auditor_token}"}

    res_verify = client.get("/api/v1/audit/verify-integrity", headers=auditor_headers)
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["is_intact"] is True
    assert verify_data["total_blocks_verified"] > 0
