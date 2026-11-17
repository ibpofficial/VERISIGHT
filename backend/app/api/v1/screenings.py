import os
import hashlib
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
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
    FieldCorrectionRequest, MRZResponse
)
from backend.app.api.deps import get_current_user, require_roles
from backend.app.engines.quality import assess_image_quality
from backend.app.engines.preprocessing import preprocess_document_image
from backend.app.engines.ocr.registry import ocr_registry
from backend.app.engines.mrz.parser import parse_mrz, parse_mrz_td3, cross_check_mrz_with_viz

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
    file: UploadFile = File(...),
    document_type: str = Form("PASSPORT_TD3"),
    issuing_country_code: Optional[str] = Form("IND"),
    is_synthetic: bool = Form(False),
    scenario_tag: Optional[str] = Form(None),
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SCREENING_OFFICER, UserRole.SENIOR_REVIEWER])),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )

    mime_type = validate_image_bytes(contents)

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

    # 4. Create Screening & Document ORM records
    screening = Screening(
        reference_no=reference_no,
        officer_id=current_user.id,
        document_type=document_type,
        issuing_country_code=issuing_country_code,
        status=ScreeningStatus.PREPROCESSING,
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

    # 5. Image Quality Assessment
    try:
        quality_result = assess_image_quality(raw_storage_path)
    except Exception as e:
        if os.path.exists(raw_storage_path):
            os.remove(raw_storage_path)
        raise HTTPException(status_code=400, detail=f"Corrupted or unreadable image file payload: {str(e)}")

    quality_record = QualityAssessment(
        screening_id=screening.id,
        overall_score=quality_result["overall_score"],
        is_acceptable=quality_result["is_acceptable"],
        blur_score=quality_result["blur_score"],
        brightness_score=quality_result["brightness_score"],
        glare_score=quality_result["glare_score"],
        resolution_dpi=quality_result["resolution_dpi"],
        orientation_detected=quality_result["orientation_detected"],
        is_cropped=quality_result["is_cropped"],
        readability_score=quality_result["readability_score"],
        issues_detected=quality_result["issues_detected"],
        rescan_recommended=quality_result["rescan_recommended"]
    )
    db.add(quality_record)

    # 6. Preprocessing (deskew, CLAHE, denoise)
    try:
        processed_path, prep_meta = preprocess_document_image(
            input_path=raw_storage_path,
            output_dir=settings.PROCESSED_DIR,
            orientation_hint=quality_result["orientation_detected"]
        )
    except Exception as e:
        processed_path = raw_storage_path
    doc_record.processed_path = processed_path
    screening.status = ScreeningStatus.ANALYZING

    # 7. OCR Extraction via Unified Registry (PaddleOCR primary / Tesseract fallback)
    ocr_result = ocr_registry.extract_with_fallback(processed_path)

    viz_fields_dict = {}
    for f_dto in ocr_result.fields:
        viz_fields_dict[f_dto.field_name] = f_dto.value
        val_status = ValidationStatus.MISSING
        if f_dto.validation_status in ValidationStatus.__members__:
            val_status = ValidationStatus[f_dto.validation_status]
        elif f_dto.value:
            val_status = ValidationStatus.VALID

        field_model = ExtractedField(
            screening_id=screening.id,
            field_name=f_dto.field_name,
            original_value=f_dto.value,
            current_value=f_dto.value,
            confidence=f_dto.confidence,
            bounding_box=f_dto.bounding_box,
            validation_status=val_status
        )
        db.add(field_model)

    # 8. Real MRZ Verification (Supports TD1, TD2, TD3 with Position-Aware OCR Normalization)
    mrz_lines = ocr_result.raw_mrz_lines
    if len(mrz_lines) >= 2:
        try:
            mrz_data = parse_mrz(mrz_lines)
        except Exception:
            mrz_data = parse_mrz_td3(mrz_lines[0], mrz_lines[1])

        viz_conf_dict = {f.field_name: f.confidence for f in ocr_result.fields}
        cross_check = cross_check_mrz_with_viz(mrz_data, viz_fields_dict, viz_conf_dict)

        mrz_record = MRZRecord(
            screening_id=screening.id,
            raw_mrz_text="\n".join(mrz_lines),
            format=mrz_data["format"],
            doc_type_code=mrz_data["doc_type_code"],
            issuing_country=mrz_data["issuing_country"],
            surname=mrz_data["surname"],
            given_names=mrz_data["given_names"],
            document_number=mrz_data["document_number"],
            nationality=mrz_data["nationality"],
            dob=mrz_data["dob"],
            sex=mrz_data["sex"],
            expiry_date=mrz_data["expiry_date"],
            optional_data=mrz_data["optional_data"],
            doc_number_check=mrz_data["doc_number_check"],
            dob_check=mrz_data["dob_check"],
            expiry_check=mrz_data["expiry_check"],
            composite_check=mrz_data["composite_check"],
            cross_check_matches=cross_check["matches"]
        )
        db.add(mrz_record)

        # Baseline preliminary risk level
        if not mrz_data["composite_check"] or not cross_check["is_consistent"]:
            screening.risk_level = RiskLevel.HIGH_RISK
            screening.risk_score = 85.0
        elif quality_result["rescan_recommended"]:
            screening.risk_level = RiskLevel.REVIEW
            screening.risk_score = 45.0
        else:
            screening.risk_level = RiskLevel.CLEAR
            screening.risk_score = 12.0
    else:
        # No MRZ detected or engine unavailable: store explicit unread MRZ record
        mrz_record = MRZRecord(
            screening_id=screening.id,
            raw_mrz_text="",
            format="NONE",
            doc_type_code="",
            issuing_country=screening.issuing_country_code or "",
            surname="",
            given_names="",
            document_number="",
            nationality="",
            dob="",
            sex="",
            expiry_date="",
            optional_data="",
            doc_number_check=False,
            dob_check=False,
            expiry_check=False,
            composite_check=False,
            cross_check_matches={}
        )
        db.add(mrz_record)
        screening.risk_level = RiskLevel.REVIEW
        screening.risk_score = 50.0

    screening.status = ScreeningStatus.COMPLETED
    screening.processing_time_ms = ocr_result.execution_time_ms

    # 9. Cryptographic Audit Chain Record
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
    return screening


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
