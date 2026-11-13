import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import RiskLevel
from backend.app.engines.risk.evaluator import evaluate_screening_risk

client = TestClient(app)


class MockQuality:
    def __init__(self, rescan=False, read=0.9):
        self.rescan_recommended = rescan
        self.readability_score = read


class MockMRZ:
    def __init__(self, valid=True, cross=True):
        self.doc_number_check = valid
        self.dob_check = valid
        self.expiry_check = valid
        self.composite_check = valid
        self.cross_check_matches = {"doc": cross, "dob": cross}
        self.expiry_date = "300101"


def test_risk_evaluator_clean_scenario():
    q = MockQuality(rescan=False, read=0.95)
    m = MockMRZ(valid=True, cross=True)
    res = evaluate_screening_risk(q, m, [], [])
    assert res["risk_level"] == RiskLevel.CLEAR
    assert res["composite_score"] == 0.0
    assert len(res["rules_triggered"]) == 0


def test_risk_evaluator_mrz_checksum_failure():
    q = MockQuality(rescan=False, read=0.95)
    m = MockMRZ(valid=False, cross=True)
    res = evaluate_screening_risk(q, m, [], [])
    assert res["risk_level"] == RiskLevel.HIGH_RISK
    assert res["composite_score"] >= 50.0
    assert any(r["rule_id"] == "RULE_MRZ_CHECKSUM_FAILURE" for r in res["rules_triggered"])


def test_risk_evaluator_poor_quality_not_fraud():
    # Poor quality must trigger REVIEW and NOT false fraud
    q = MockQuality(rescan=True, read=0.55)
    m = MockMRZ(valid=True, cross=True)
    res = evaluate_screening_risk(q, m, [], [])
    assert res["risk_level"] == RiskLevel.REVIEW
    assert any(r["rule_id"] == "RULE_LOW_OPTICAL_QUALITY" for r in res["rules_triggered"])


def test_risk_override_rbac_enforcement(tmp_path):
    # 1. Login as officer
    officer_login = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    officer_token = officer_login.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    # 2. Upload doc to make screening
    img_path = str(tmp_path / "doc.jpg")
    img = np.full((300, 500, 3), 240, dtype=np.uint8)
    cv2.putText(img, "TEST PASSPORT", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.imwrite(img_path, img)

    with open(img_path, "rb") as f:
        upload_res = client.post(
            "/api/v1/screenings",
            headers=officer_headers,
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "IND", "is_synthetic": True},
            files={"file": ("passport.jpg", f, "image/jpeg")}
        )
    screening_id = upload_res.json()["id"]

    # 3. Get risk assessment
    risk_res = client.get(f"/api/v1/risk/{screening_id}", headers=officer_headers)
    assert risk_res.status_code == 200

    # 4. Attempt override as Screening Officer (MUST BE REJECTED 403)
    officer_override = client.post(
        f"/api/v1/risk/{screening_id}/override",
        headers=officer_headers,
        json={"override_level": "CLEAR", "reason": "Officer attempting unauthorized manual override"}
    )
    assert officer_override.status_code == 403

    # 5. Login as Senior Reviewer
    reviewer_login = client.post("/api/v1/auth/login", json={
        "email": "reviewer@verisight.gov.in",
        "password": "Reviewer@12345"
    })
    reviewer_token = reviewer_login.json()["access_token"]
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    # 6. Override as Senior Reviewer (MUST SUCCEED)
    reviewer_override = client.post(
        f"/api/v1/risk/{screening_id}/override",
        headers=reviewer_headers,
        json={
            "override_level": "CLEAR",
            "reason": "Physical inspection of security features confirmed authenticity; OCR glare suppressed."
        }
    )
    assert reviewer_override.status_code == 200
    updated = reviewer_override.json()
    assert updated["reviewer_override_level"] == "CLEAR"
    assert updated["override_reason"] is not None
