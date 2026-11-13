import os
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    User, Screening, Document, ForensicFinding, AuditLog,
    ForensicMethod, FindingSeverity
)
from backend.app.schemas import ForensicFindingResponse
from backend.app.api.deps import get_current_user
from backend.app.engines.forensics.pipeline import run_full_forensic_suite

router = APIRouter(prefix="/forensics", tags=["Forensic Laboratory"])


@router.get("/{screening_id}", response_model=List[ForensicFindingResponse])
def get_or_run_forensics(
    screening_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves or dynamically computes multi-factor forensic findings:
    ELA, metadata provenance, surface texture, text alignment, and portrait boundary.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    doc = db.query(Document).filter(Document.screening_id == screening_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found")

    # Check if findings have already been computed
    existing_findings = db.query(ForensicFinding).filter(ForensicFinding.screening_id == screening_id).all()
    if existing_findings:
        return existing_findings

    # Otherwise run the full forensic suite
    heatmap_filename = f"{screening.reference_no}_ela.jpg"
    heatmap_path = os.path.join(settings.PROCESSED_DIR, heatmap_filename)
    raw_path = doc.storage_path
    processed_path = doc.processed_path or doc.storage_path

    suite_results = run_full_forensic_suite(
        raw_path=raw_path,
        processed_path=processed_path,
        output_heatmap_path=heatmap_path
    )

    created_findings: List[ForensicFinding] = []
    for f_item in suite_results.get("all_findings", []):
        finding = ForensicFinding(
            screening_id=screening_id,
            analysis_method=ForensicMethod(f_item["analysis_method"]),
            severity=FindingSeverity(f_item["severity"]),
            region_bbox=f_item.get("region_bbox"),
            title=f_item["title"],
            explanation=f_item["explanation"],
            technical_details=f_item.get("technical_details", {}),
            limitations=f_item["limitations"],
            recommended_action=f_item["recommended_action"]
        )
        db.add(finding)
        created_findings.append(finding)

    # Append to cryptographic audit chain
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "screening_id": screening_id,
        "reference_no": screening.reference_no,
        "findings_count": len(created_findings),
        "officer": current_user.email
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=screening_id,
        event_type="FORENSIC_ANALYSIS_EXECUTED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="FORENSIC_ANALYSIS_EXECUTED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening_id,
        action_description=f"Multi-factor forensic suite evaluated for {screening.reference_no}: {len(created_findings)} findings recorded",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)

    db.commit()
    for f in created_findings:
        db.refresh(f)

    return created_findings


@router.get("/{screening_id}/heatmap")
def get_ela_heatmap(
    screening_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the generated Error Level Analysis heatmap image file.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    heatmap_path = os.path.join(settings.PROCESSED_DIR, f"{screening.reference_no}_ela.jpg")
    
    if not os.path.exists(heatmap_path):
        # Generate on demand if missing
        doc = db.query(Document).filter(Document.screening_id == screening_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found")
        from backend.app.engines.forensics.ela import run_error_level_analysis
        run_error_level_analysis(doc.processed_path or doc.storage_path, heatmap_path)

    if not os.path.exists(heatmap_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Heatmap could not be generated")

    return FileResponse(heatmap_path, media_type="image/jpeg")
