import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import User, LoginActivity, UserRole
from backend.app.api.deps import require_roles
from fastapi import APIRouter, Depends

client = TestClient(app)

# Create a test-only role-restricted endpoint to test RBAC
test_router = APIRouter()

@test_router.get("/admin-only")
def admin_only_view(user: User = Depends(require_roles([UserRole.ADMINISTRATOR]))):
    return {"message": "Admin area accessed", "user": user.email}

@test_router.get("/officer-only")
def officer_only_view(user: User = Depends(require_roles([UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER]))):
    return {"message": "Officer area accessed", "user": user.email}

app.include_router(test_router, prefix="/api/v1/test")


def test_health_and_root():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "VERISIGHT" in res_root.json()["name"]


def test_login_success_and_activity():
    # Login as officer
    res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "SCREENING_OFFICER"
    assert data["email"] == "officer@verisight.gov.in"

    # Verify login activity recorded in DB
    db = SessionLocal()
    try:
        activity = db.query(LoginActivity).filter(
            LoginActivity.user_id == data["user_id"]
        ).order_by(LoginActivity.created_at.desc()).first()
        assert activity is not None
        assert activity.success is True
    finally:
        db.close()


def test_login_invalid_password():
    res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "WrongPassword!999"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_token_refresh():
    # Login to get refresh token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@verisight.gov.in",
        "password": "Admin@12345"
    })
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    ref_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()
    assert ref_res.json()["role"] == "ADMINISTRATOR"


def test_protected_me_endpoint():
    # Login as reviewer
    login_res = client.post("/api/v1/auth/login", json={
        "email": "reviewer@verisight.gov.in",
        "password": "Reviewer@12345"
    })
    token = login_res.json()["access_token"]

    # Access /me
    me_res = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "reviewer@verisight.gov.in"
    assert me_res.json()["role"] == "SENIOR_REVIEWER"

    # Unauthorized access without token
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401


def test_rbac_backend_enforcement():
    # Login as screening officer
    officer_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    officer_token = officer_res.json()["access_token"]

    # Login as admin
    admin_res = client.post("/api/v1/auth/login", json={
        "email": "admin@verisight.gov.in",
        "password": "Admin@12345"
    })
    admin_token = admin_res.json()["access_token"]

    # 1. Officer accessing officer-only view -> 200 OK
    res_officer_ok = client.get("/api/v1/test/officer-only", headers={
        "Authorization": f"Bearer {officer_token}"
    })
    assert res_officer_ok.status_code == 200

    # 2. Officer attempting to access admin-only view -> 403 Forbidden
    res_officer_denied = client.get("/api/v1/test/admin-only", headers={
        "Authorization": f"Bearer {officer_token}"
    })
    assert res_officer_denied.status_code == 403
    assert "Operation not permitted" in res_officer_denied.json()["detail"]

    # 3. Admin accessing admin-only view -> 200 OK
    res_admin_ok = client.get("/api/v1/test/admin-only", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert res_admin_ok.status_code == 200


def test_password_reset_flow():
    req_res = client.post("/api/v1/auth/reset-password", json={
        "email": "auditor@verisight.gov.in"
    })
    assert req_res.status_code == 200
    sim_token = req_res.json()["reset_token_simulation"]

    # Confirm password reset
    conf_res = client.post("/api/v1/auth/confirm-reset", json={
        "token": sim_token,
        "new_password": "NewAuditorPassword@123"
    })
    assert conf_res.status_code == 200

    # Login with new password
    login_new = client.post("/api/v1/auth/login", json={
        "email": "auditor@verisight.gov.in",
        "password": "NewAuditorPassword@123"
    })
    assert login_new.status_code == 200

    # Restore original password for downstream tests and demo consistency
    req_restore = client.post("/api/v1/auth/reset-password", json={
        "email": "auditor@verisight.gov.in"
    })
    sim_token_restore = req_restore.json()["reset_token_simulation"]
    client.post("/api/v1/auth/confirm-reset", json={
        "token": sim_token_restore,
        "new_password": "Auditor@12345"
    })

