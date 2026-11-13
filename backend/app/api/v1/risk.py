import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    User, UserRole, Screening, QualityAssessment, ExtractedField,
    MRZRecord, ForensicFinding, RiskAssessment, AuditLog, RiskLevel
)
from backend.app.schemas import RiskAssessmentResponse, RiskOverrideRequest
from backend.app.api.deps import get_current_user, require_roles
from backend.app.engines.risk.evaluator import evaluate_screening_risk

router = APIRouter(prefix="/risk", tags=["Explainable Risk Engine"])


@router.get("/{screening_id}", response_model=RiskAssessmentResponse)
def get_or_evaluate_risk(
    screening_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes or retrieves explainable, deterministic risk model evaluation
    for the specified travel credential screening.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    existing_assessment = db.query(RiskAssessment).filter(RiskAssessment.screening_id == screening_id).first()
    if existing_assessment:
        return existing_assessment

    # Gather all inputs across pipeline
    quality = db.query(QualityAssessment).filter(QualityAssessment.screening_id == screening_id).first()
    mrz = db.query(MRZRecord).filter(MRZRecord.screening_id == screening_id).first()
    fields = db.query(ExtractedField).filter(ExtractedField.screening_id == screening_id).all()
    findings = db.query(ForensicFinding).filter(ForensicFinding.screening_id == screening_id).all()

    eval_result = evaluate_screening_risk(quality, mrz, fields, findings)

    # Persist RiskAssessment
    assessment = RiskAssessment(
        screening_id=screening_id,
        risk_level=eval_result["risk_level"],
        composite_score=eval_result["composite_score"],
        engine_version=eval_result["engine_version"],
        rules_triggered=eval_result["rules_triggered"]
    )
    db.add(assessment)

    # Sync screening record risk
    screening.risk_level = eval_result["risk_level"]
    screening.risk_score = eval_result["composite_score"]

    # Append to cryptographic audit chain
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "screening_id": screening_id,
        "reference_no": screening.reference_no,
        "risk_level": eval_result["risk_level"].value,
        "composite_score": eval_result["composite_score"],
        "rules_count": len(eval_result["rules_triggered"]),
        "officer": current_user.email
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=screening_id,
        event_type="RISK_EVALUATION_COMPLETED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="RISK_EVALUATION_COMPLETED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening_id,
        action_description=f"Risk model classified {screening.reference_no} as {eval_result['risk_level'].value} (score: {eval_result['composite_score']})",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(assessment)
    return assessment


@router.post("/{screening_id}/override", response_model=RiskAssessmentResponse)
def override_risk_decision(
    screening_id: str,
    data: RiskOverrideRequest,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    """
    Permits an authorized Senior Reviewer or Administrator to execute a manual
    risk level override with mandatory evidentiary justification note.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    assessment = db.query(RiskAssessment).filter(RiskAssessment.screening_id == screening_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Risk evaluation must be computed before overriding")

    original_level = assessment.risk_level.value
    assessment.reviewer_override_level = data.override_level
    assessment.override_reason = data.reason
    assessment.overridden_by = current_user.id
    assessment.overridden_at = datetime.datetime.now(datetime.timezone.utc)

    # Sync screening record
    screening.risk_level = data.override_level

    # Append immutable signed audit block
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "screening_id": screening_id,
        "reference_no": screening.reference_no,
        "original_level": original_level,
        "override_level": data.override_level.value,
        "justification": data.reason,
        "reviewer": current_user.email
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=screening_id,
        event_type="RISK_DECISION_OVERRIDDEN",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="RISK_DECISION_OVERRIDDEN",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening_id,
        action_description=f"Decision overridden from {original_level} to {data.override_level.value} by {current_user.full_name}: {data.reason}",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(assessment)
    return assessment
