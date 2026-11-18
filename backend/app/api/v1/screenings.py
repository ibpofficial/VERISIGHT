import os
import hashlib
import uuid
import datetime
import cv2
import numpy as np
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    User, UserRole, Screening, Document, QualityAssessment, 
    ExtractedField, MRZRecord, AuditLog, ScreeningStatus, RiskLevel, ValidationStatus
)
from backend.app.schemas import (
    ScreeningResponse, QualityResponse, ExtractedFieldResponse, 
    FieldCorrectionRequest, MRZResponse, ScreeningStatusResponse
)
from backend.app.api.deps import get_current_user, require_roles
from backend.app.engines.quality import assess_image_quality
from backend.app.engines.preprocessing import preprocess_document_image
from backend.app.engines.ocr.registry import ocr_registry
from backend.app.engines.mrz.parser import parse_mrz, parse_mrz_td3, cross_check_mrz_with_viz
from backend.app.services.pipeline import execute_screening_pipeline, initialize_stage_details, calculate_overall_progress

router = APIRouter(prefix="/screenings", tags=["Document Screening"])

def validate_image_bytes(contents: bytes) -> str:
    """Validate file type by inspection of magic bytes (prevent MIME spoofing)."""
    if contents.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(contents) >= 12 and contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
        return "image/webp"
    if contents.startswith(b"BM"):
        return "image/bmp"
    if contents.startswith(b"II*\x00") or contents.startswith(b"MM\x00*"):
        return "image/tiff"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported or corrupted file type. Supported formats: JPEG, PNG, WEBP, BMP, TIFF."
    )


@router.post("", response_model=ScreeningResponse)
async def create_screening(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form("PASSPORT_TD3"),
    issuing_country_code: Optional[str] = Form("IND"),
    is_synthetic: bool = Form(False),
    scenario_tag: Optional[str] = Form(None),
    sync: bool = Form(True),
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    """
    Ingests document: validates magic bytes, computes SHA-256 evidence hash,
    stores raw document, creates audit record, and enqueues async pipeline.
    """
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )

    mime_type = validate_image_bytes(contents)

    # Decode probe to catch truncated / corrupted byte payloads
    arr = np.frombuffer(contents, dtype=np.uint8)
    probe_img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if probe_img is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or unreadable image payload. File headers exist but pixel data cannot be decoded."
        )

    # 1. Immediate SHA-256 evidence hashing at ingestion
    file_sha256 = hashlib.sha256(contents).hexdigest()

    # 2. Generate unique reference code: VS-YYYYMMDD-XXXX
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:4].upper()
    reference_no = f"VS-{date_str}-{short_uuid}"

    # 3. Store raw original image securely
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    extension_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }
    extension = extension_map.get(mime_type, ".jpg")
    original_filename = f"{reference_no}_orig{extension}"
    raw_storage_path = os.path.join(settings.UPLOAD_DIR, original_filename)

    with open(raw_storage_path, "wb") as f:
        f.write(contents)

    # 4. Create Screening & Document records in PENDING stage
    initial_stages = initialize_stage_details()
    screening = Screening(
        reference_no=reference_no,
        officer_id=current_user.id,
        document_type=document_type,
        issuing_country_code=issuing_country_code,
        status=ScreeningStatus.PENDING,
        stage_details=initial_stages,
        current_stage="PENDING",
        is_synthetic=is_synthetic,
        scenario_tag=scenario_tag
    )
    db.add(screening)
    db.flush()

    doc_record = Document(
        screening_id=screening.id,
        original_filename=file.filename or original_filename,
        storage_path=raw_storage_path,
        file_size_bytes=len(contents),
        mime_type=mime_type,
        sha256_hash=file_sha256,
        is_encrypted=False
    )
    db.add(doc_record)

    # 5. Cryptographic Audit Chain Record for Document Ingestion
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "reference_no": reference_no,
        "sha256": file_sha256,
        "file_size": len(contents),
        "officer": current_user.email
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=reference_no,
        event_type="DOCUMENT_INGESTED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="DOCUMENT_INGESTED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening.id,
        action_description=f"Document {reference_no} ingested with SHA-256 {file_sha256[:16]}...",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(screening)

    # 6. Trigger pipeline execution: synchronously or asynchronously via worker
    if sync:
        execute_screening_pipeline(screening.id)
        db.refresh(screening)
    else:
        background_tasks.add_task(execute_screening_pipeline, screening.id)

    return screening


@router.get("/{id}/status", response_model=ScreeningStatusResponse)
def get_screening_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns real-time execution progress, active stage, and stage details.
    """
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    stages_dict = screening.stage_details or initialize_stage_details()
    progress = calculate_overall_progress(stages_dict)

    err = None
    if screening.current_stage and screening.current_stage in stages_dict:
        err = stages_dict[screening.current_stage].get("error")

    return ScreeningStatusResponse(
        id=screening.id,
        reference_no=screening.reference_no,
        status=screening.status,
        current_stage=screening.current_stage,
        overall_progress=progress,
        stages=stages_dict,
        rescan_instructions=screening.rescan_instructions,
        error_message=err,
        is_aborted=screening.is_aborted
    )


@router.post("/{id}/retry", response_model=ScreeningStatusResponse)
def retry_screening(
    id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    """
    Resets failed or rejected stages and re-triggers pipeline execution.
    """
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    screening.status = ScreeningStatus.PENDING
    screening.is_aborted = False
    screening.rescan_instructions = None
    screening.stage_details = initialize_stage_details()
    screening.current_stage = "PENDING"
    db.commit()

    background_tasks.add_task(execute_screening_pipeline, screening.id)

    return ScreeningStatusResponse(
        id=screening.id,
        reference_no=screening.reference_no,
        status=screening.status,
        current_stage="PENDING",
        overall_progress=0,
        stages=screening.stage_details,
        rescan_instructions=None,
        error_message=None,
        is_aborted=False
    )


@router.post("/{id}/cancel", response_model=ScreeningStatusResponse)
def cancel_screening(
    id: str,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    """
    Signals pipeline worker to abort execution of the screening.
    """
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    screening.is_aborted = True
    screening.status = ScreeningStatus.ABORTED
    db.commit()

    stages_dict = screening.stage_details or initialize_stage_details()
    return ScreeningStatusResponse(
        id=screening.id,
        reference_no=screening.reference_no,
        status=screening.status,
        current_stage=screening.current_stage,
        overall_progress=calculate_overall_progress(stages_dict),
        stages=stages_dict,
        rescan_instructions=screening.rescan_instructions,
        error_message="Screening aborted by officer.",
        is_aborted=True
    )


@router.get("", response_model=List[ScreeningResponse])
def list_screenings(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[ScreeningStatus] = None,
    risk_filter: Optional[RiskLevel] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Screening)
    if status_filter:
        query = query.filter(Screening.status == status_filter)
    if risk_filter:
        query = query.filter(Screening.risk_level == risk_filter)
    screenings = query.order_by(Screening.created_at.desc()).offset(skip).limit(limit).all()
    return screenings


@router.get("/{id}", response_model=ScreeningResponse)
def get_screening(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")
    return screening


@router.get("/{id}/document")
def get_document_image(
    id: str,
    processed: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.screening_id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document image not found")

    path = doc.processed_path if processed and doc.processed_path else doc.storage_path
    if not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File on disk missing")

    return FileResponse(path, media_type=doc.mime_type)


@router.get("/{id}/quality", response_model=QualityResponse)
def get_quality_assessment(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    qa = db.query(QualityAssessment).filter(QualityAssessment.screening_id == id).first()
    if not qa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality assessment not found")
    return qa


@router.get("/{id}/fields", response_model=List[ExtractedFieldResponse])
def get_extracted_fields(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    screening = db.query(Screening).filter(Screening.id == id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")
    fields = db.query(ExtractedField).filter(ExtractedField.screening_id == id).all()
    return fields


@router.patch("/{id}/fields/{field_id}", response_model=ExtractedFieldResponse)
def correct_extracted_field(
    id: str,
    field_id: str,
    data: FieldCorrectionRequest,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    field = db.query(ExtractedField).filter(
        ExtractedField.id == field_id, 
        ExtractedField.screening_id == id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field record not found")

    old_val = field.current_value
    field.current_value = data.new_value
    field.is_corrected = True
    field.validation_status = ValidationStatus.CORRECTED
    field.corrected_by = current_user.id
    field.corrected_at = datetime.datetime.now(datetime.timezone.utc)
    if data.notes:
        field.notes = data.notes

    # Create immutable audit record
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "field_name": field.field_name,
        "original_value": field.original_value,
        "old_value": old_val,
        "new_value": data.new_value,
        "reviewer": current_user.email,
        "notes": data.notes
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=field.id,
        event_type="FIELD_MODIFIED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="FIELD_MODIFIED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=id,
        action_description=f"Field '{field.field_name}' corrected from '{old_val}' to '{data.new_value}'",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(field)
    return field


@router.get("/{id}/mrz", response_model=MRZResponse)
def get_mrz_record(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    mrz = db.query(MRZRecord).filter(MRZRecord.screening_id == id).first()
    if not mrz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MRZ record not found")
    return mrz
