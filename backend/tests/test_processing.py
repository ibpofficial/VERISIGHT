import io
import os
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.engines.quality import assess_image_quality
from backend.app.engines.preprocessing import preprocess_document_image
from backend.app.engines.mrz.check_digits import calculate_mrz_check_digit, verify_check_digit
from backend.app.engines.mrz.parser import parse_mrz_td3, cross_check_mrz_with_viz
from backend.app.models import AuditLog
from backend.app.core.database import SessionLocal

client = TestClient(app)


def create_dummy_passport_image(path: str):
    """Creates a synthetic passport test image with text and MRZ lines."""
    img = np.ones((600, 850, 3), dtype=np.uint8) * 240
    # Header
    cv2.putText(img, "REPUBLIC OF UTOPIA - PASSPORT", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    # Photo placeholder
    cv2.rectangle(img, (50, 100), (220, 320), (180, 180, 180), -1)
    cv2.putText(img, "PORTRAIT", (80, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 2)
    # VIZ Text
    cv2.putText(img, "Surname: SHARMA", (260, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.putText(img, "Given Names: AMIT", (260, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.putText(img, "Nationality: UTO", (260, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.putText(img, "Date of Birth: 14/05/1988", (260, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.putText(img, "Doc No: A12345678", (260, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)
    cv2.putText(img, "Expiry: 21/08/2031", (260, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 10), 2)

    # Compute exact check digits
    doc_no = "A12345678"
    doc_chk = calculate_mrz_check_digit(doc_no)
    dob = "880514"
    dob_chk = calculate_mrz_check_digit(dob)
    exp = "310821"
    exp_chk = calculate_mrz_check_digit(exp)
    opt = "<<<<<<<<<<<<<<"
    opt_chk = "<"
    comp_data = f"{doc_no}{doc_chk}{dob}{dob_chk}{exp}{exp_chk}{opt}{opt_chk}"
    comp_chk = calculate_mrz_check_digit(comp_data)

    line1 = "P<UTOSHARMA<<AMIT<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    line2 = f"{doc_no}{doc_chk}UTO{dob}{dob_chk}M{exp}{exp_chk}{opt}{opt_chk}{comp_chk}"

    cv2.putText(img, line1, (30, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    cv2.putText(img, line2, (30, 540), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img)


def test_mrz_check_digits_math():
    # Standard ICAO 9303 test vector:
    # 'HA5391091' with weights [7, 3, 1]
    # H(17)*7 + A(10)*3 + 5*1 + 3*7 + 9*3 + 1*1 + 0*7 + 9*3 + 1*1
    # = 119 + 30 + 5 + 21 + 27 + 1 + 0 + 27 + 1 = 231 % 10 = 1
    computed = calculate_mrz_check_digit("HA5391091")
    assert computed == "1"
    assert verify_check_digit("HA5391091", "1") is True
    assert verify_check_digit("HA5391091", "2") is False


def test_mrz_td3_parser():
    doc_no = "A12345678"
    doc_chk = calculate_mrz_check_digit(doc_no)
    dob = "880514"
    dob_chk = calculate_mrz_check_digit(dob)
    exp = "310821"
    exp_chk = calculate_mrz_check_digit(exp)
    opt = "<<<<<<<<<<<<<<"
    opt_chk = "<"
    comp_data = f"{doc_no}{doc_chk}{dob}{dob_chk}{exp}{exp_chk}{opt}{opt_chk}"
    comp_chk = calculate_mrz_check_digit(comp_data)

    l1 = "P<UTOSHARMA<<AMIT<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    l2 = f"{doc_no}{doc_chk}UTO{dob}{dob_chk}M{exp}{exp_chk}{opt}{opt_chk}{comp_chk}"
    res = parse_mrz_td3(l1, l2)

    assert res["surname"] == "SHARMA"
    assert res["given_names"] == "AMIT"
    assert res["document_number"] == doc_no
    assert res["nationality"] == "UTO"
    assert res["dob"] == dob
    assert res["sex"] == "M"
    assert res["expiry_date"] == exp
    assert res["doc_number_check"] is True
    assert res["dob_check"] is True
    assert res["expiry_check"] is True


def test_quality_and_preprocessing(tmp_path):
    test_img = str(tmp_path / "test_doc.png")
    create_dummy_passport_image(test_img)

    # 1. Quality Assessment
    quality = assess_image_quality(test_img)
    assert quality["blur_score"] > 50.0
    assert quality["is_acceptable"] is True
    assert quality["readability_score"] > 0.5

    # 2. Preprocessing
    processed_dir = str(tmp_path / "processed")
    processed_path, meta = preprocess_document_image(test_img, processed_dir)
    assert os.path.exists(processed_path)
    assert meta["clahe_applied"] is True


def test_full_screening_upload_and_field_correction(tmp_path):
    # Login as screening officer
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy passport file
    test_img = str(tmp_path / "passport_sample.png")
    create_dummy_passport_image(test_img)

    # Upload and screen
    with open(test_img, "rb") as f:
        res = client.post(
            "/api/v1/screenings",
            headers=headers,
            files={"file": ("passport_sample.png", f, "image/png")},
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "UTO"}
        )
    assert res.status_code == 200
    screening = res.json()
    screening_id = screening["id"]
    assert screening["status"] == "COMPLETED"
    assert "reference_no" in screening

    # Verify Quality endpoint
    q_res = client.get(f"/api/v1/screenings/{screening_id}/quality", headers=headers)
    assert q_res.status_code == 200
    assert q_res.json()["readability_score"] > 0.0

    # Verify Extracted Fields
    f_res = client.get(f"/api/v1/screenings/{screening_id}/fields", headers=headers)
    assert f_res.status_code == 200
    fields = f_res.json()
    assert len(fields) > 0

    # Correct a field value
    target_field = fields[0]
    patch_res = client.patch(
        f"/api/v1/screenings/{screening_id}/fields/{target_field['id']}",
        headers=headers,
        json={"new_value": "CORRECTED_VAL", "notes": "Officer visual confirmation"}
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["current_value"] == "CORRECTED_VAL"
    assert updated["is_corrected"] is True

    # Verify Audit log entry created for field correction
    db = SessionLocal()
    try:
        audit = db.query(AuditLog).filter(
            AuditLog.screening_id == screening_id,
            AuditLog.event_type == "FIELD_MODIFIED"
        ).first()
        assert audit is not None
        assert "CORRECTED_VAL" in audit.action_description
    finally:
        db.close()


def test_reject_invalid_magic_bytes():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fake corrupted text file claiming to be png
    corrupted_bytes = b"NOT_A_REAL_IMAGE_FILE"
    res = client.post(
        "/api/v1/screenings",
        headers=headers,
        files={"file": ("fake.png", io.BytesIO(corrupted_bytes), "image/png")},
        data={"document_type": "PASSPORT_TD3"}
    )
    assert res.status_code == 400
    assert "Unsupported or corrupted file type" in res.json()["detail"]
