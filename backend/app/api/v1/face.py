import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import cv2

from backend.app.core.database import get_db
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models import User, UserRole, Screening, Document, AuditLog
from backend.app.engines.face.verifier import (
    verify_document_vs_live,
    extract_document_portrait,
    bgr_to_base64_jpeg,
    PRIVACY_STATEMENT,
    FACE_DISCLAIMER
)

router = APIRouter(prefix="/face", tags=["Face Verification"])


@router.get("/{screening_id}/portrait")
def get_extracted_portrait(
    screening_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extracts and returns the cropped portrait from the stored document image
    for pre-verification visual inspection.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening record not found")

    document = db.query(Document).filter(Document.screening_id == screening_id).first()
    if not document or not os.path.exists(document.storage_path):
        raise HTTPException(status_code=404, detail="Document storage artifact not found")

    doc_img = cv2.imread(document.storage_path)
    if doc_img is None:
        raise HTTPException(status_code=500, detail="Failed to load document image")

    portrait_crop = extract_document_portrait(doc_img)
    if portrait_crop is None:
        raise HTTPException(status_code=422, detail="Unable to isolate document portrait zone")

    b64_portrait = bgr_to_base64_jpeg(portrait_crop)

    return {
        "screening_id": screening_id,
        "reference_no": screening.reference_no,
        "portrait_b64": b64_portrait,
        "privacy_notice": PRIVACY_STATEMENT,
        "disclaimer": FACE_DISCLAIMER
    }


@router.post("/{screening_id}/verify")
def verify_face(
    screening_id: str,
    consent_granted: bool = Form(...),
    live_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.SCREENING_OFFICER,
        UserRole.SENIOR_REVIEWER,
        UserRole.ADMINISTRATOR
    ])),
):
    """
    Performs consent-gated biometric face verification comparing the document portrait
    with the provided live capture frame.
    Guarantees ephemeral in-memory processing with zero biometric persistence.
    """
    # Parse boolean consent safely from form payload
    is_consent_granted = False
    if isinstance(consent_granted, bool):
        is_consent_granted = consent_granted
    elif isinstance(consent_granted, str):
        is_consent_granted = consent_granted.lower() in ("true", "1", "yes")

    if not is_consent_granted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Biometric verification legally aborted: Explicit subject consent is required under DPDP Act 2023."
        )

    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening record not found")

    document = db.query(Document).filter(Document.screening_id == screening_id).first()
    if not document or not os.path.exists(document.storage_path):
        raise HTTPException(status_code=404, detail="Document storage artifact not found")

    # Read live image bytes
    live_bytes = live_image.file.read()
    if not live_bytes or len(live_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty live capture payload received")

    # Perform verification
    result = verify_document_vs_live(
        doc_image_path=document.storage_path,
        live_image_bytes=live_bytes,
        consent_granted=is_consent_granted
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Biometric verification failed")
        )

    # Cryptographic Audit Log (records metric, never biometric vector)
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "similarity_score": result["similarity_score"],
        "threshold": result["threshold"],
        "is_match": result["is_match"],
        "confidence_band": result["confidence_band"],
        "doc_quality_acceptable": result["doc_quality"]["is_acceptable"],
        "live_quality_acceptable": result["live_quality"]["is_acceptable"]
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=screening.reference_no,
        event_type="FACE_VERIFICATION_PERFORMED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="FACE_VERIFICATION_PERFORMED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening.id,
        action_description=f"Ephemeral biometric cross-check executed by {current_user.full_name} for ref {screening.reference_no}.",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)
    db.commit()

    return result
