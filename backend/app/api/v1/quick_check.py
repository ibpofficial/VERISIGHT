import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models import User, Screening, Document, Case, CaseStatus, CasePriority, RiskLevel, ScreeningStatus
from backend.app.api.deps import get_current_user
from backend.app.engines.quick_check.analyzer import QuickCheckAnalyzer

router = APIRouter(prefix="/quick-checks", tags=["Standalone Quick Check"])

# In-memory session cache for quick check evaluations
QUICK_CHECK_CACHE = {}

@router.post("")
async def run_quick_check(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes standalone digital forensic checks on arbitrary JPG, PNG, WEBP, TIFF, PDF, or DOCX files.
    """
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    check_id = str(uuid.uuid4())
    result = QuickCheckAnalyzer.analyze_file(file.filename, contents)
    result["check_id"] = check_id
    result["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result["officer_name"] = current_user.full_name
    result["officer_badge"] = current_user.badge_number

    # Save to session cache and persist temporary copy
    QUICK_CHECK_CACHE[check_id] = {
        "result": result,
        "filename": file.filename,
        "file_bytes": contents,
        "user_id": current_user.id
    }

    return result

@router.get("/{check_id}")
def get_quick_check_result(
    check_id: str,
    current_user: User = Depends(get_current_user)
):
    if check_id not in QUICK_CHECK_CACHE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quick check session expired or not found")
    return QUICK_CHECK_CACHE[check_id]["result"]

@router.post("/{check_id}/escalate")
def escalate_to_full_case(
    check_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Escalates a standalone Quick Check into a formal VERISIGHT Screening and Investigation Case.
    """
    if check_id not in QUICK_CHECK_CACHE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quick check session expired or not found")

    cache_item = QUICK_CHECK_CACHE[check_id]
    result = cache_item["result"]
    filename = cache_item["filename"]
    file_bytes = cache_item["file_bytes"]

    # 1. Create a Screening record
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:4].upper()
    ref_no = f"QC-{date_str}-{short_uuid}"

    # Determine risk level
    rl_map = {
        "CLEAR": RiskLevel.CLEAR,
        "REVIEW": RiskLevel.REVIEW,
        "HIGH_RISK": RiskLevel.HIGH_RISK
    }
    risk_level = rl_map.get(result.get("risk_level"), RiskLevel.REVIEW)

    screening = Screening(
        reference_no=ref_no,
        officer_id=current_user.id,
        document_type=f"QUICK_CHECK_{result.get('file_type', 'GENERAL')}",
        issuing_country_code="IND",
        status=ScreeningStatus.COMPLETED,
        risk_level=risk_level
    )
    db.add(screening)
    db.flush()

    # 2. Save document binary
    storage_filename = f"{screening.id}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    import hashlib
    sha256 = hashlib.sha256(file_bytes).hexdigest()

    doc = Document(
        screening_id=screening.id,
        filename=filename,
        file_path=file_path,
        file_size=len(file_bytes),
        mime_type="application/octet-stream",
        sha256_hash=sha256
    )
    db.add(doc)

    # 3. Create Investigation Case
    case_number = f"CASE-{date_str}-{short_uuid}"
    summary = f"Escalated from Quick Check ({filename}). Forensic Verdict: {result.get('verdict')}. Summary: {result.get('summary')}"

    new_case = Case(
        case_number=case_number,
        screening_id=screening.id,
        assigned_officer_id=current_user.id,
        status=CaseStatus.IN_REVIEW,
        priority=CasePriority.HIGH if risk_level == RiskLevel.HIGH_RISK else CasePriority.MEDIUM,
        summary=summary,
        notes=[{
            "id": str(uuid.uuid4()),
            "author": current_user.full_name,
            "badge": current_user.badge_number,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "text": f"Escalated from Quick Check tool. {len(result.get('findings', []))} forensic indicators identified."
        }]
    )
    db.add(new_case)
    db.commit()

    return {
        "case_id": new_case.id,
        "case_number": new_case.case_number,
        "screening_id": screening.id,
        "reference_no": screening.reference_no,
        "message": "Successfully escalated to active investigation case."
    }
