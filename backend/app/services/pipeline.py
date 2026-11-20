import os
import time
import datetime
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    Screening, Document, QualityAssessment, ExtractedField, MRZRecord, 
    ForensicFinding, RiskAssessment, AuditLog, ScreeningStatus, RiskLevel, 
    ValidationStatus, ForensicMethod, FindingSeverity
)
from backend.app.engines.quality import assess_image_quality
from backend.app.engines.preprocessing import preprocess_document_image
from backend.app.engines.ocr.registry import ocr_registry
from backend.app.engines.mrz.parser import parse_mrz, parse_mrz_td3, cross_check_mrz_with_viz
from backend.app.engines.forensics.pipeline import run_full_forensic_suite
from backend.app.engines.risk.evaluator import evaluate_screening_risk

logger = logging.getLogger(__name__)

STAGE_ORDER = [
    "QUALITY_ASSESSMENT",
    "PREPROCESSING",
    "OCR_EXTRACTION",
    "MRZ_PARSING",
    "VALIDATION_CROSSCHECK",
    "FORENSICS_ANALYSIS",
    "RISK_SCORING",
]

STAGE_WEIGHTS = {
    "QUALITY_ASSESSMENT": 15,
    "PREPROCESSING": 15,
    "OCR_EXTRACTION": 25,
    "MRZ_PARSING": 15,
    "VALIDATION_CROSSCHECK": 10,
    "FORENSICS_ANALYSIS": 10,
    "RISK_SCORING": 10,
}


def initialize_stage_details() -> Dict[str, Any]:
    """Generates initial PENDING state map for all execution stages."""
    return {
        stage: {
            "status": "PENDING",
            "timing_ms": None,
            "error": None,
            "details": None
        }
        for stage in STAGE_ORDER
    }


def calculate_overall_progress(stage_details: Dict[str, Any]) -> int:
    """Calculates real percentage completion based on completed stages."""
    progress = 0
    for stage, weight in STAGE_WEIGHTS.items():
        st = stage_details.get(stage, {}).get("status")
        if st in ("COMPLETED", "SKIPPED"):
            progress += weight
        elif st == "RUNNING":
            progress += weight // 2
    return min(progress, 100)


def update_stage_state(screening: Screening, stages: Dict[str, Any], db: Session) -> None:
    screening.stage_details = dict(stages)
    flag_modified(screening, "stage_details")
    db.commit()


def execute_screening_pipeline(screening_id: str) -> None:
    """
    Executes the multi-stage asynchronous document screening pipeline.
    Runs each stage, persists real per-stage status, timing, and errors.
    If a stage fails, halts downstream dependent stages with DEPENDENCY_FAILED.
    """
    db: Session = SessionLocal()
    total_start = time.perf_counter()

    try:
        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            logger.error(f"Screening {screening_id} not found for pipeline execution.")
            return

        if screening.is_aborted:
            screening.status = ScreeningStatus.ABORTED
            db.commit()
            return

        stages = screening.stage_details or initialize_stage_details()
        screening.status = ScreeningStatus.PROCESSING
        db.commit()

        doc_record = db.query(Document).filter(Document.screening_id == screening.id).first()
        raw_storage_path = doc_record.storage_path if doc_record else None

        if not raw_storage_path or not os.path.exists(raw_storage_path):
            screening.status = ScreeningStatus.FAILED
            screening.stage_details["QUALITY_ASSESSMENT"] = {
                "status": "FAILED",
                "timing_ms": 0,
                "error": f"Raw document image not found at storage path: {raw_storage_path}",
                "details": None
            }
            db.commit()
            return

        # =========================================================================
        # STAGE 1: QUALITY ASSESSMENT
        # =========================================================================
        screening.current_stage = "QUALITY_ASSESSMENT"
        stages["QUALITY_ASSESSMENT"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        q_start = time.perf_counter()
        try:
            quality_result = assess_image_quality(raw_storage_path)
            q_time_ms = int((time.perf_counter() - q_start) * 1000)
            stages["QUALITY_ASSESSMENT"] = {
                "status": "COMPLETED",
                "timing_ms": q_time_ms,
                "error": None,
                "details": {
                    "overall_score": quality_result["overall_score"],
                    "blur_score": quality_result["blur_score"],
                    "glare_score": quality_result["glare_score"],
                    "estimated_dpi": quality_result["resolution_dpi"],
                    "is_acceptable": quality_result["is_acceptable"]
                }
            }

            # Upsert quality assessment record
            quality_record = db.query(QualityAssessment).filter(QualityAssessment.screening_id == screening.id).first()
            if not quality_record:
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
            db.commit()

            # Halt on severe optical rejection (spec requirement)
            if not quality_result["is_acceptable"]:
                stages["QUALITY_ASSESSMENT"]["status"] = "FAILED"
                stages["QUALITY_ASSESSMENT"]["error"] = "Severe optical degradation detected; document fails intake standards."
                for s in STAGE_ORDER[1:]:
                    stages[s] = {
                        "status": "DEPENDENCY_FAILED",
                        "timing_ms": 0,
                        "error": "Skipped due to upstream optical quality rejection.",
                        "details": None
                    }
                screening.status = ScreeningStatus.REJECTED_POOR_QUALITY
                screening.current_stage = "QUALITY_ASSESSMENT"
                instructions = ["Quality Rejection: Image does not meet minimum forensic standards for verification."]
                for issue in quality_result["issues_detected"]:
                    instructions.append(f"• {issue}")
                instructions.append("Action: Rescan with high-resolution camera (>300 DPI), flat alignment, and diffuse ambient light.")
                screening.rescan_instructions = "\n".join(instructions)
                update_stage_state(screening, stages, db)
                return

        except Exception as e:
            q_time_ms = int((time.perf_counter() - q_start) * 1000)
            stages["QUALITY_ASSESSMENT"] = {
                "status": "FAILED",
                "timing_ms": q_time_ms,
                "error": str(e),
                "details": None
            }
            screening.status = ScreeningStatus.FAILED
            update_stage_state(screening, stages, db)
            return

        if screening.is_aborted:
            screening.status = ScreeningStatus.ABORTED
            db.commit()
            return

        # =========================================================================
        # STAGE 2: PREPROCESSING (Deskew, Perspective Contour Warp, CLAHE, Denoise)
        # =========================================================================
        screening.current_stage = "PREPROCESSING"
        stages["PREPROCESSING"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        p_start = time.perf_counter()
        try:
            processed_path, prep_meta = preprocess_document_image(
                input_path=raw_storage_path,
                output_dir=settings.PROCESSED_DIR,
                orientation_hint=quality_result.get("orientation_detected", 0)
            )
            doc_record.processed_path = processed_path
            p_time_ms = int((time.perf_counter() - p_start) * 1000)
            stages["PREPROCESSING"] = {
                "status": "COMPLETED",
                "timing_ms": p_time_ms,
                "error": None,
                "details": prep_meta
            }
            update_stage_state(screening, stages, db)
        except Exception as e:
            p_time_ms = int((time.perf_counter() - p_start) * 1000)
            processed_path = raw_storage_path
            doc_record.processed_path = raw_storage_path
            stages["PREPROCESSING"] = {
                "status": "COMPLETED",
                "timing_ms": p_time_ms,
                "error": f"Notice: preprocessing fell back to original image ({str(e)})",
                "details": {"fallback": True}
            }
            update_stage_state(screening, stages, db)

        if screening.is_aborted:
            screening.status = ScreeningStatus.ABORTED
            db.commit()
            return

        # =========================================================================
        # STAGE 3: OCR EXTRACTION (PaddleOCR / Tesseract with Retry Backoff)
        # =========================================================================
        screening.current_stage = "OCR_EXTRACTION"
        stages["OCR_EXTRACTION"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        ocr_start = time.perf_counter()
        ocr_result = None
        ocr_retries = 2
        for attempt in range(ocr_retries + 1):
            try:
                ocr_result = ocr_registry.extract_with_fallback(processed_path)
                break
            except Exception as ocr_err:
                if attempt == ocr_retries:
                    ocr_time_ms = int((time.perf_counter() - ocr_start) * 1000)
                    stages["OCR_EXTRACTION"] = {
                        "status": "FAILED",
                        "timing_ms": ocr_time_ms,
                        "error": str(ocr_err),
                        "details": None
                    }
                    stages["MRZ_PARSING"] = {
                        "status": "DEPENDENCY_FAILED",
                        "timing_ms": 0,
                        "error": "Skipped due to OCR extraction failure.",
                        "details": None
                    }
                    stages["VALIDATION_CROSSCHECK"] = {
                        "status": "DEPENDENCY_FAILED",
                        "timing_ms": 0,
                        "error": "Skipped due to OCR extraction failure.",
                        "details": None
                    }
                    screening.status = ScreeningStatus.FAILED
                    update_stage_state(screening, stages, db)
                    return
                time.sleep(0.3 * (2 ** attempt))

        ocr_time_ms = int((time.perf_counter() - ocr_start) * 1000)
        stages["OCR_EXTRACTION"] = {
            "status": "COMPLETED",
            "timing_ms": ocr_time_ms,
            "error": ocr_result.error_message if ocr_result.status != "SUCCESS" else None,
            "details": {
                "engine_used": ocr_result.engine_name,
                "status": ocr_result.status,
                "fields_extracted": len(ocr_result.fields),
                "fallback_used": ocr_result.fallback_used
            }
        }

        # Clear existing extracted fields and persist fresh ones
        db.query(ExtractedField).filter(ExtractedField.screening_id == screening.id).delete()
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
        db.commit()

        if screening.is_aborted:
            screening.status = ScreeningStatus.ABORTED
            db.commit()
            return

        # =========================================================================
        # STAGE 4: MRZ PARSING
        # =========================================================================
        screening.current_stage = "MRZ_PARSING"
        stages["MRZ_PARSING"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        mrz_start = time.perf_counter()
        mrz_lines = ocr_result.raw_mrz_lines
        mrz_data = None
        if len(mrz_lines) >= 2:
            try:
                mrz_data = parse_mrz(mrz_lines)
            except Exception:
                mrz_data = parse_mrz_td3(mrz_lines[0], mrz_lines[1])

            mrz_time_ms = int((time.perf_counter() - mrz_start) * 1000)
            stages["MRZ_PARSING"] = {
                "status": "COMPLETED",
                "timing_ms": mrz_time_ms,
                "error": None,
                "details": {
                    "format": mrz_data.get("format"),
                    "composite_check": mrz_data.get("composite_check"),
                    "ocr_corrections": len(mrz_data.get("ocr_corrections", []))
                }
            }
        else:
            mrz_time_ms = int((time.perf_counter() - mrz_start) * 1000)
            stages["MRZ_PARSING"] = {
                "status": "COMPLETED",
                "timing_ms": mrz_time_ms,
                "error": None,
                "details": {"format": "NONE", "detected": False}
            }
        update_stage_state(screening, stages, db)

        # =========================================================================
        # STAGE 5: VALIDATION & CROSS-CHECK
        # =========================================================================
        screening.current_stage = "VALIDATION_CROSSCHECK"
        stages["VALIDATION_CROSSCHECK"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        v_start = time.perf_counter()
        cross_check = {"is_consistent": True, "matches": {}}
        if mrz_data and mrz_data.get("format") != "NONE":
            viz_conf_dict = {f.field_name: f.confidence for f in ocr_result.fields}
            cross_check = cross_check_mrz_with_viz(mrz_data, viz_fields_dict, viz_conf_dict)

            # Upsert MRZ record
            db.query(MRZRecord).filter(MRZRecord.screening_id == screening.id).delete()
            mrz_record = MRZRecord(
                screening_id=screening.id,
                raw_mrz_text="\n".join(mrz_lines),
                format=mrz_data["format"],
                doc_type_code=mrz_data.get("doc_type_code", "P"),
                issuing_country=mrz_data.get("issuing_country", ""),
                surname=mrz_data.get("surname", ""),
                given_names=mrz_data.get("given_names", ""),
                document_number=mrz_data.get("document_number", ""),
                nationality=mrz_data.get("nationality", ""),
                dob=mrz_data.get("dob", ""),
                sex=mrz_data.get("sex", ""),
                expiry_date=mrz_data.get("expiry_date", ""),
                optional_data=mrz_data.get("optional_data"),
                doc_number_check=mrz_data.get("doc_number_check", False),
                dob_check=mrz_data.get("dob_check", False),
                expiry_check=mrz_data.get("expiry_check", False),
                composite_check=mrz_data.get("composite_check", False),
                cross_check_matches=cross_check["matches"]
            )
            db.add(mrz_record)
        else:
            db.query(MRZRecord).filter(MRZRecord.screening_id == screening.id).delete()
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
                doc_number_check=True,
                dob_check=True,
                expiry_check=True,
                composite_check=True,
                cross_check_matches={}
            )
            db.add(mrz_record)

        v_time_ms = int((time.perf_counter() - v_start) * 1000)
        stages["VALIDATION_CROSSCHECK"] = {
            "status": "COMPLETED",
            "timing_ms": v_time_ms,
            "error": None,
            "details": {
                "cross_check_consistent": cross_check.get("is_consistent", True),
                "match_count": len(cross_check.get("matches", {}))
            }
        }
        update_stage_state(screening, stages, db)

        if screening.is_aborted:
            screening.status = ScreeningStatus.ABORTED
            db.commit()
            return

        # =========================================================================
        # STAGE 6: FORENSICS ANALYSIS
        # =========================================================================
        screening.current_stage = "FORENSICS_ANALYSIS"
        stages["FORENSICS_ANALYSIS"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        f_start = time.perf_counter()
        heatmap_dir = os.path.join(settings.PROCESSED_DIR, "heatmaps")
        os.makedirs(heatmap_dir, exist_ok=True)
        heatmap_path = os.path.join(heatmap_dir, f"{screening.reference_no}_ela.jpg")

        forensic_res = run_full_forensic_suite(
            raw_path=raw_storage_path,
            processed_path=processed_path,
            output_heatmap_path=heatmap_path
        )

        db.query(ForensicFinding).filter(ForensicFinding.screening_id == screening.id).delete()
        findings_models = []
        for finding in forensic_res.get("all_findings", []):
            try:
                method_enum = ForensicMethod[finding.get("analysis_method", "ELA")]
            except KeyError:
                method_enum = ForensicMethod.ELA
            try:
                severity_enum = FindingSeverity[finding.get("severity", "LOW")]
            except KeyError:
                severity_enum = FindingSeverity.LOW

            ff = ForensicFinding(
                screening_id=screening.id,
                analysis_method=method_enum,
                severity=severity_enum,
                region_bbox=finding.get("region_bbox"),
                title=finding.get("title", "Forensic Signal"),
                explanation=finding.get("explanation", ""),
                technical_details=finding.get("technical_details", {}),
                limitations=finding.get("limitations", "Automated heuristic evaluation"),
                recommended_action=finding.get("recommended_action", "Manual forensic review recommended")
            )
            db.add(ff)
            findings_models.append(ff)

        f_time_ms = int((time.perf_counter() - f_start) * 1000)
        stages["FORENSICS_ANALYSIS"] = {
            "status": "COMPLETED",
            "timing_ms": f_time_ms,
            "error": None,
            "details": {
                "total_findings": len(forensic_res.get("all_findings", [])),
                "ela_available": forensic_res.get("ela", {}).get("is_available", True),
                "metadata_flags": len(forensic_res.get("metadata", {}).get("findings", []))
            }
        }
        update_stage_state(screening, stages, db)

        if screening.is_aborted:
            screening.status = ScreeningStatus.ABORTED
            db.commit()
            return

        # =========================================================================
        # STAGE 7: RISK SCORING & FINALIZATION
        # =========================================================================
        screening.current_stage = "RISK_SCORING"
        stages["RISK_SCORING"]["status"] = "RUNNING"
        update_stage_state(screening, stages, db)

        r_start = time.perf_counter()
        fields_list = db.query(ExtractedField).filter(ExtractedField.screening_id == screening.id).all()
        risk_result = evaluate_screening_risk(
            quality_record=quality_record,
            mrz_record=mrz_record,
            fields=fields_list,
            forensic_findings=findings_models
        )

        db.query(RiskAssessment).filter(RiskAssessment.screening_id == screening.id).delete()
        risk_model = RiskAssessment(
            screening_id=screening.id,
            risk_level=risk_result["risk_level"],
            composite_score=risk_result["composite_score"],
            engine_version=risk_result.get("engine_version", "1.0.0"),
            rules_triggered=risk_result.get("rules_triggered", [])
        )
        db.add(risk_model)

        r_time_ms = int((time.perf_counter() - r_start) * 1000)
        stages["RISK_SCORING"] = {
            "status": "COMPLETED",
            "timing_ms": r_time_ms,
            "error": None,
            "details": {
                "composite_score": risk_result["composite_score"],
                "risk_level": risk_result["risk_level"].value,
                "rules_triggered_count": len(risk_result.get("rules_triggered", []))
            }
        }

        total_time_ms = int((time.perf_counter() - total_start) * 1000)
        screening.status = ScreeningStatus.COMPLETED
        screening.risk_level = risk_result["risk_level"]
        screening.risk_score = risk_result["composite_score"]
        screening.processing_time_ms = total_time_ms
        screening.current_stage = "COMPLETED"
        update_stage_state(screening, stages, db)

        # Cryptographic Audit Chain Record
        last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_audit.current_hash if last_audit else "0" * 64
        event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta_audit = {
            "processing_time_ms": total_time_ms,
            "risk_score": screening.risk_score,
            "ocr_engine": stages["OCR_EXTRACTION"].get("details", {}).get("engine_used")
        }
        current_hash = calculate_record_hash(
            prev_hash=prev_hash,
            record_id=screening.reference_no,
            event_type="SCREENING_ASYNC_PIPELINE_COMPLETED",
            actor_id=screening.officer_id,
            timestamp_iso=event_timestamp,
            metadata=meta_audit
        )
        audit_entry = AuditLog(
            event_type="SCREENING_ASYNC_PIPELINE_COMPLETED",
            actor_id=screening.officer_id,
            actor_role="SYSTEM_WORKER",
            screening_id=screening.id,
            action_description=f"Automated 7-stage verification completed for {screening.reference_no} with risk level {screening.risk_level.value}",
            metadata_json=meta_audit,
            prev_record_hash=prev_hash,
            current_hash=current_hash
        )
        db.add(audit_entry)
        db.commit()

        logger.info(f"Screening {screening.reference_no} pipeline completed in {total_time_ms}ms with risk {screening.risk_level.value}.")

    except Exception as exc:
        logger.exception(f"Unhandled error in screening pipeline for {screening_id}: {exc}")
        if 'screening' in locals() and screening:
            screening.status = ScreeningStatus.FAILED
            if screening.current_stage and screening.current_stage in stages:
                stages[screening.current_stage]["status"] = "FAILED"
                stages[screening.current_stage]["error"] = str(exc)
            screening.stage_details = stages
            db.commit()
    finally:
        db.close()
