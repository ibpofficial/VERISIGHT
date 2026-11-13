import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    User, Screening, Document, QualityAssessment, ExtractedField,
    MRZRecord, ForensicFinding, RiskAssessment, AuditLog
)
from backend.app.api.deps import get_current_user
from backend.app.engines.reports.generator import build_screening_pdf_report

router = APIRouter(prefix="/reports", tags=["Institutional Reports"])


@router.get("/{screening_id}/download")
def download_screening_report(
    screening_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compiles and downloads the formal 5-page PDF evidentiary screening dossier.
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening record not found")

    doc = db.query(Document).filter(Document.screening_id == screening_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found")

    quality = db.query(QualityAssessment).filter(QualityAssessment.screening_id == screening_id).first()
    fields = db.query(ExtractedField).filter(ExtractedField.screening_id == screening_id).all()
    mrz = db.query(MRZRecord).filter(MRZRecord.screening_id == screening_id).first()
    findings = db.query(ForensicFinding).filter(ForensicFinding.screening_id == screening_id).all()
    risk = db.query(RiskAssessment).filter(RiskAssessment.screening_id == screening_id).first()

    pdf_filename = f"VERISIGHT_DOSSIER_{screening.reference_no}.pdf"
    output_pdf_path = os.path.join(settings.REPORTS_DIR, pdf_filename)

    # Build PDF
    build_screening_pdf_report(
        screening_data={
            "reference_no": screening.reference_no,
            "document_type": screening.document_type,
            "issuing_country_code": screening.issuing_country_code,
            "is_synthetic": screening.is_synthetic,
            "created_at": screening.created_at,
        },
        document_data={
            "file_size_bytes": doc.file_size_bytes,
            "sha256_hash": doc.sha256_hash,
            "mime_type": doc.mime_type,
            "storage_path": doc.storage_path,
            "processed_path": doc.processed_path,
        },
        quality_data={
            "overall_score": quality.overall_score if quality else 0,
            "blur_score": quality.blur_score if quality else 0,
            "glare_score": quality.glare_score if quality else 0,
            "brightness_score": quality.brightness_score if quality else 0,
            "resolution_dpi": quality.resolution_dpi if quality else 300,
            "orientation_detected": quality.orientation_detected if quality else 0,
            "readability_score": quality.readability_score if quality else 0,
            "rescan_recommended": quality.rescan_recommended if quality else False,
        } if quality else None,
        fields_data=[
            {
                "field_name": f.field_name,
                "current_value": f.current_value,
                "confidence": f.confidence,
                "validation_status": f.validation_status.value if hasattr(f.validation_status, "value") else str(f.validation_status),
                "is_corrected": f.is_corrected,
            }
            for f in fields
        ],
        mrz_data={
            "raw_mrz_text": mrz.raw_mrz_text,
            "document_number": mrz.document_number,
            "dob": mrz.dob,
            "expiry_date": mrz.expiry_date,
            "doc_number_check": mrz.doc_number_check,
            "dob_check": mrz.dob_check,
            "expiry_check": mrz.expiry_check,
            "composite_check": mrz.composite_check,
        } if mrz else None,
        forensics_data=[
            {
                "analysis_method": f.analysis_method.value if hasattr(f.analysis_method, "value") else str(f.analysis_method),
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "title": f.title,
                "recommended_action": f.recommended_action,
            }
            for f in findings
        ],
        risk_data={
            "risk_level": risk.risk_level.value if risk else "REVIEW",
            "composite_score": risk.composite_score if risk else 0.0,
            "engine_version": risk.engine_version if risk else "VERISIGHT-v1.2",
            "reviewer_override_level": risk.reviewer_override_level.value if (risk and risk.reviewer_override_level) else None,
            "override_reason": risk.override_reason if risk else None,
        } if risk else None,
        output_path=output_pdf_path
    )

    # Log PDF generation in audit trail
    last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta_payload = {
        "screening_id": screening_id,
        "reference_no": screening.reference_no,
        "filename": pdf_filename,
        "officer": current_user.email
    }
    block_hash = calculate_record_hash(
        prev_hash=prev_hash,
        record_id=screening_id,
        event_type="PDF_REPORT_GENERATED",
        actor_id=current_user.id,
        timestamp_iso=event_timestamp,
        metadata=meta_payload
    )
    audit_entry = AuditLog(
        event_type="PDF_REPORT_GENERATED",
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        screening_id=screening_id,
        action_description=f"Evidentiary PDF dossier generated for {screening.reference_no} by {current_user.full_name}",
        metadata_json=meta_payload,
        prev_record_hash=prev_hash,
        current_hash=block_hash
    )
    db.add(audit_entry)
    db.commit()

    return FileResponse(
        output_pdf_path,
        media_type="application/pdf",
        filename=pdf_filename
    )
