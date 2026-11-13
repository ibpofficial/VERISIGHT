import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    User, UserRole, Screening, Case, AuditLog,
    CaseStatus, CasePriority
)
from backend.app.schemas import (
    CaseResponse, CaseCreateRequest, CaseStatusUpdate, CaseNoteCreate
)
from backend.app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


@router.get("", response_model=List[CaseResponse])
def list_cases(
    status_filter: Optional[CaseStatus] = Query(None, alias="status"),
    priority_filter: Optional[CasePriority] = Query(None, alias="priority"),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    if priority_filter:
        query = query.filter(Case.priority == priority_filter)

    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    return cases


@router.post("", response_model=CaseResponse)
def create_case(
    data: CaseCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    screening = db.query(Screening).filter(Screening.id == data.screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced screening not found")

    existing_case = db.query(Case).filter(Case.screening_id == data.screening_id).first()
    if existing_case:
        return existing_case

    # Unique Case Number: CASE-YYYYMMDD-XXXX
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:4].upper()
    case_number = f"CASE-{date_str}-{short_uuid}"

    summary = data.summary or f"Investigation opened for credential {screening.reference_no} ({screening.document_type})"

    case = Case(
        case_number=case_number,
        screening_id=data.screening_id,
        assigned_officer_id=current_user.id,
        status=CaseStatus.OPEN,
        priority=data.priority or CasePriority.MEDIUM,
        summary=summary,
        notes=[{
            "id": str(uuid.uuid4()),
            "author": current_user.full_name or current_user.email,
            "text": f"Case automatically opened following screening {screening.reference_no}.",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }]
    )
    db.add(case)
    db.flush()

    # Append to SHA-256 audit chain
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "case_id": case.id,
        "case_number": case.case_number,
        "screening_id": screening.id,
        "reference_no": screening.reference_no,
        "officer": current_user.email
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=case.id,
        event_type="CASE_OPENED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="CASE_OPENED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening.id,
        case_id=case.id,
        action_description=f"Investigation case {case.case_number} initiated by {current_user.full_name}",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(case)
    return case


@router.get("/{id}", response_model=CaseResponse)
def get_case(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found")
    return case


@router.patch("/{id}/status", response_model=CaseResponse)
def update_case_status(
    id: str,
    data: CaseStatusUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found")

    old_status = case.status.value
    case.status = data.status
    if data.priority:
        case.priority = data.priority
    if data.assigned_officer_id:
        case.assigned_officer_id = data.assigned_officer_id

    if data.status in [CaseStatus.RESOLVED, CaseStatus.RETURNED]:
        case.resolved_at = datetime.datetime.now(datetime.timezone.utc)
        if data.resolution_notes:
            case.resolution_notes = data.resolution_notes

    # Add system transition note
    notes_list = list(case.notes or [])
    notes_list.append({
        "id": str(uuid.uuid4()),
        "author": current_user.full_name or current_user.email,
        "text": f"Status updated from {old_status} to {data.status.value}. Notes: {data.resolution_notes or 'None provided.'}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    case.notes = notes_list

    # Append to SHA-256 audit chain
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "case_id": case.id,
        "case_number": case.case_number,
        "old_status": old_status,
        "new_status": data.status.value,
        "officer": current_user.email,
        "notes": data.resolution_notes
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=case.id,
        event_type="CASE_STATUS_UPDATED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="CASE_STATUS_UPDATED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        case_id=case.id,
        action_description=f"Case {case.case_number} transitioned to {data.status.value} by {current_user.full_name}",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(case)
    return case


@router.post("/{id}/notes", response_model=CaseResponse)
def add_case_note(
    id: str,
    data: CaseNoteCreate,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found")

    new_note = {
        "id": str(uuid.uuid4()),
        "author": current_user.full_name or current_user.email,
        "text": data.text,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    notes_list = list(case.notes or [])
    notes_list.append(new_note)
    case.notes = notes_list

    # Append to SHA-256 audit chain
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "case_id": case.id,
        "case_number": case.case_number,
        "note_author": current_user.email,
        "note_length": len(data.text)
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=case.id,
        event_type="CASE_NOTE_ADDED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="CASE_NOTE_ADDED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        case_id=case.id,
        action_description=f"Investigation note affixed to {case.case_number} by {current_user.full_name}",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(case)
    return case
