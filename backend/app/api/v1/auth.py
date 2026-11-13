from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from backend.app.models import User, LoginActivity
from backend.app.schemas import (
    LoginRequest, TokenResponse, RefreshRequest, 
    PasswordResetRequest, PasswordResetConfirm, UserResponse
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    user = db.query(User).filter(User.email == credentials.email.lower()).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(credentials.password, user.password_hash):
        activity = LoginActivity(
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            success=False,
            failure_reason="INVALID_PASSWORD"
        )
        db.add(activity)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        activity = LoginActivity(
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            success=False,
            failure_reason="ACCOUNT_DEACTIVATED"
        )
        db.add(activity)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    activity = LoginActivity(
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        success=True
    )
    db.add(activity)
    db.commit()

    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    data: RefreshRequest,
    db: Session = Depends(get_db)
):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User invalid or inactive"
        )

    new_access_token = create_access_token(subject=user.id, role=user.role.value)
    new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Session terminated successfully"}


@router.post("/reset-password")
def request_password_reset(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        reset_token = create_access_token(subject=user.id, role="PASSWORD_RESET")
        return {
            "message": "Password reset instructions dispatched.",
            "reset_token_simulation": reset_token
        }
    return {"message": "If the email is registered, instructions have been sent."}


@router.post("/confirm-reset")
def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    payload = decode_token(data.token)
    if not payload or payload.get("role") != "PASSWORD_RESET":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully. Please log in with your new credentials."}


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user
