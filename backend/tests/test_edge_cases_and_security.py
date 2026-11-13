import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import UserRole

client = TestClient(app)


def test_unsupported_file_extensions():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt uploading executable file masquerading as image
    exe_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
    res1 = client.post(
        "/api/v1/screenings",
        headers=headers,
        files={"file": ("malicious.exe", io.BytesIO(exe_payload), "application/x-msdownload")},
        data={"document_type": "PASSPORT_TD3"}
    )
    assert res1.status_code == 400
    assert "unsupported" in res1.json()["detail"].lower()

    # 2. Attempt uploading zip archive
    zip_payload = b"PK\x03\x04\x14\x00\x00\x00"
    res2 = client.post(
        "/api/v1/screenings",
        headers=headers,
        files={"file": ("archive.zip", io.BytesIO(zip_payload), "application/zip")},
        data={"document_type": "PASSPORT_TD3"}
    )
    assert res2.status_code == 400


def test_corrupted_truncated_image_payload():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Valid JPEG magic bytes (\xFF\xD8\xFF) but corrupted payload of only 4 bytes
    corrupted_jpg = b"\xFF\xD8\xFF\xE0"
    res = client.post(
        "/api/v1/screenings",
        headers=headers,
        files={"file": ("corrupt.jpg", io.BytesIO(corrupted_jpg), "image/jpeg")},
        data={"document_type": "PASSPORT_TD3"}
    )
    # The system gracefully rejects unparseable byte streams
    assert res.status_code in [400, 422]


def test_unauthorized_rbac_access_denials():
    # 1. Login as Officer
    login_officer = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    officer_token = login_officer.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    # Officer attempts to access Administrator user management -> 403 Forbidden
    res_admin = client.get("/api/v1/admin/users", headers=officer_headers)
    assert res_admin.status_code == 403
    assert "permitted" in res_admin.json()["detail"].lower() or "required role" in res_admin.json()["detail"].lower()

    # Officer attempts to alter system risk thresholds -> 403 Forbidden
    res_config = client.patch(
        "/api/v1/admin/config",
        headers=officer_headers,
        json={"high_risk_threshold": 99.0}
    )
    assert res_config.status_code == 403

    # 2. Login as Auditor
    login_auditor = client.post("/api/v1/auth/login", json={
        "email": "auditor@verisight.gov.in",
        "password": "Auditor@12345"
    })
    auditor_token = login_auditor.json()["access_token"]
    auditor_headers = {"Authorization": f"Bearer {auditor_token}"}

    # Auditor attempts to ingest a screening -> 403 Forbidden (Auditor is read-only)
    dummy_jpg = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB"
    res_auditor_ingest = client.post(
        "/api/v1/screenings",
        headers=auditor_headers,
        files={"file": ("test.jpg", io.BytesIO(dummy_jpg), "image/jpeg")},
        data={"document_type": "PASSPORT_TD3"}
    )
    assert res_auditor_ingest.status_code == 403


def test_unauthenticated_and_tampered_token():
    # 1. Missing Authorization header
    res_no_auth = client.get("/api/v1/screenings")
    assert res_no_auth.status_code == 401

    # 2. Malformed token
    res_malformed = client.get(
        "/api/v1/screenings",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"}
    )
    assert res_malformed.status_code == 401

    # 3. Forged token signature
    forged_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB2ZXJpc2lnaHQuZ292LmluIn0.forged_signature_here"
    res_forged = client.get(
        "/api/v1/screenings",
        headers={"Authorization": f"Bearer {forged_token}"}
    )
    assert res_forged.status_code == 401


def test_nonexistent_resource_handling():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fake_uuid = "00000000-0000-0000-0000-000000000000"

    # Non-existent screening
    assert client.get(f"/api/v1/screenings/{fake_uuid}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/screenings/{fake_uuid}/quality", headers=headers).status_code == 404
    assert client.get(f"/api/v1/screenings/{fake_uuid}/fields", headers=headers).status_code == 404
    assert client.get(f"/api/v1/screenings/{fake_uuid}/mrz", headers=headers).status_code == 404
    assert client.get(f"/api/v1/forensics/{fake_uuid}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/risk/{fake_uuid}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/reports/{fake_uuid}/download", headers=headers).status_code == 404
    assert client.get(f"/api/v1/cases/{fake_uuid}", headers=headers).status_code == 404


def test_malicious_input_sanitization():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "reviewer@verisight.gov.in",
        "password": "Reviewer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. SQL Injection payload in case search
    sqli_search = "'; DROP TABLE screenings; --"
    res_search = client.get(f"/api/v1/cases?search={sqli_search}", headers=headers)
    assert res_search.status_code == 200  # Safely parameterized, returns empty list without error

    # 2. XSS script tag injection in case query
    xss_payload = "<script>alert('XSS_ATTACK')</script>"
    res_xss = client.get(f"/api/v1/cases?search={xss_payload}", headers=headers)
    assert res_xss.status_code == 200
