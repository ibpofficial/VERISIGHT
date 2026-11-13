import os
import sys
import uuid
import hashlib
import datetime
import numpy as np
import cv2
from PIL import Image, ExifTags

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.audit_chain import calculate_record_hash
from backend.app.models import (
    User, UserRole, Screening, Document, QualityAssessment,
    ExtractedField, MRZRecord, ForensicFinding, RiskAssessment, Case, AuditLog,
    ScreeningStatus, RiskLevel, CaseStatus, CasePriority, ForensicMethod, FindingSeverity, ValidationStatus
)
from backend.app.engines.mrz.check_digits import calculate_mrz_check_digit
from backend.app.engines.forensics.ela import run_error_level_analysis
from backend.app.engines.risk.evaluator import evaluate_screening_risk

DEMO_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "demo_data")
os.makedirs(DEMO_DIR, exist_ok=True)


def create_base_passport_canvas(name: str, doc_no: str, dob: str, expiry: str, sex: str) -> np.ndarray:
    """Draws a synthetic high-resolution document image with guilloche patterns and text."""
    w, h = 900, 600
    canvas = np.full((h, w, 3), 245, dtype=np.uint8)

    # Security guilloche background simulation (fine wavy lines)
    for y in range(0, h, 8):
        pts = []
        for x in range(0, w, 15):
            wave_y = int(y + 4 * np.sin(x / 25.0))
            pts.append([x, wave_y])
        pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts_arr], False, (225, 235, 245), 1)

    # Passport Header
    cv2.rectangle(canvas, (30, 30), (w - 30, 90), (30, 58, 138), -1)
    cv2.putText(canvas, "REPUBLIC OF INDIA / PASSPORT", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # Simulated Portrait Box (left)
    cv2.rectangle(canvas, (60, 130), (300, 420), (200, 210, 220), -1)
    cv2.rectangle(canvas, (60, 130), (300, 420), (140, 150, 165), 2)
    # Silhouette face
    cv2.circle(canvas, (180, 230), 45, (100, 115, 130), -1)
    cv2.ellipse(canvas, (180, 340), (70, 55), 0, 0, 180, (100, 115, 130), -1)
    cv2.putText(canvas, "SYNTHETIC IDENTITY", (90, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 70, 80), 1)

    # VIZ Data Fields (right)
    fields = [
        ("SURNAME / NOM", name.split()[1] if len(name.split()) > 1 else name),
        ("GIVEN NAMES / PRENOMS", name.split()[0]),
        ("NATIONALITY / NATIONALITE", "INDIAN"),
        ("PASSPORT NO.", doc_no),
        ("DATE OF BIRTH", dob),
        ("SEX", sex),
        ("DATE OF EXPIRY", expiry),
    ]

    start_y = 150
    for label, val in fields:
        cv2.putText(canvas, label, (340, start_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 115, 130), 1)
        cv2.putText(canvas, val, (340, start_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (15, 23, 42), 2)
        start_y += 40

    return canvas


def add_mrz_zone(canvas: np.ndarray, line1: str, line2: str):
    """Prints 2-line ICAO TD3 MRZ at the bottom of the canvas."""
    h, w, _ = canvas.shape
    cv2.rectangle(canvas, (30, h - 130), (w - 30, h - 25), (255, 255, 255), -1)
    cv2.rectangle(canvas, (30, h - 130), (w - 30, h - 25), (203, 213, 225), 1)

    cv2.putText(canvas, line1, (45, h - 85), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (15, 23, 42), 2)
    cv2.putText(canvas, line2, (45, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (15, 23, 42), 2)


def generate_scenarios():
    print("=" * 60)
    print("VERISIGHT — Generating 5 Synthetic Demonstration Scenarios")
    print("=" * 60)

    db = SessionLocal()
    officer = db.query(User).filter(User.role == UserRole.SCREENING_OFFICER).first()
    officer_id = officer.id if officer else str(uuid.uuid4())

    scenarios = [
        # 1. CLEAN
        {
            "tag": "SCENARIO-1-CLEAN",
            "name": "ANIL KUMAR",
            "doc_no": "Z1234567",
            "dob_viz": "01/01/1990",
            "dob_mrz": "900101",
            "exp_viz": "01/01/2030",
            "exp_mrz": "300101",
            "sex": "M",
            "tamper": "none",
            "description": "Clean, genuine travel credential with perfect check digits and optimal optics."
        },
        # 2. EXPIRED
        {
            "tag": "SCENARIO-2-EXPIRED",
            "name": "PRIYA SHARMA",
            "doc_no": "A8765432",
            "dob_viz": "15/08/1985",
            "dob_mrz": "850815",
            "exp_viz": "15/05/2021",
            "exp_mrz": "210515",
            "sex": "F",
            "tamper": "none",
            "description": "Synthetic credential with validity period expired in May 2021."
        },
        # 3. MRZ MISMATCH
        {
            "tag": "SCENARIO-3-MRZ-MISMATCH",
            "name": "ROHIT VERMA",
            "doc_no": "P5544332",
            "dob_viz": "10/10/1992",
            "dob_mrz": "921010",
            "exp_viz": "10/10/2032",
            "exp_mrz": "321010",
            "sex": "M",
            "tamper": "mrz_mismatch",
            "description": "Altered document number in MRZ zone with failing 7-3-1 check digit."
        },
        # 4. TAMPERED ELA
        {
            "tag": "SCENARIO-4-TAMPERED-ELA",
            "name": "VIJAY SINGH",
            "doc_no": "K9988776",
            "dob_viz": "05/03/1988",
            "dob_mrz": "880305",
            "exp_viz": "05/03/2029",
            "exp_mrz": "290305",
            "sex": "M",
            "tamper": "ela_tamper",
            "description": "Digitally spliced portrait block producing severe ELA error variance and Photoshop EXIF metadata."
        },
        # 5. LOW QUALITY
        {
            "tag": "SCENARIO-5-LOW-QUALITY",
            "name": "SUNITA PATEL",
            "doc_no": "R1122334",
            "dob_viz": "22/11/1995",
            "dob_mrz": "951122",
            "exp_viz": "22/11/2035",
            "exp_mrz": "351122",
            "sex": "F",
            "tamper": "blur_glare",
            "description": "Severe motion blur and specular flash glare requiring rescan."
        },
    ]

    for sc in scenarios:
        print(f"\n[+] Generating {sc['tag']}...")
        canvas = create_base_passport_canvas(
            name=sc["name"],
            doc_no=sc["doc_no"],
            dob=sc["dob_viz"],
            expiry=sc["exp_viz"],
            sex=sc["sex"]
        )

        # Compute MRZ lines
        surname = sc["name"].split()[1] if len(sc["name"].split()) > 1 else sc["name"]
        given = sc["name"].split()[0]
        l1 = f"P<IND{surname}<<{given}".ljust(44, "<")

        mrz_doc_no = sc["doc_no"]
        if sc["tamper"] == "mrz_mismatch":
            # Deliberately modify last character to cause mismatch and check digit failure
            mrz_doc_no = sc["doc_no"][:-1] + ("1" if sc["doc_no"][-1] != "1" else "2")

        doc_chk = calculate_mrz_check_digit(mrz_doc_no)
        dob_chk = calculate_mrz_check_digit(sc["dob_mrz"])
        exp_chk = calculate_mrz_check_digit(sc["exp_mrz"])

        if sc["tamper"] == "mrz_mismatch":
            # Invalidate check digit
            doc_chk = str((int(doc_chk) + 5) % 10)

        composite_body = f"{mrz_doc_no}{doc_chk}{sc['dob_mrz']}{dob_chk}{sc['exp_mrz']}{exp_chk}"
        comp_chk = calculate_mrz_check_digit(composite_body)

        l2 = f"{mrz_doc_no}<{doc_chk}IND{sc['dob_mrz']}{dob_chk}{sc['sex']}{sc['exp_mrz']}{exp_chk}<<<<<<<<<<<<<<{comp_chk}0"
        add_mrz_zone(canvas, l1, l2)

        # Apply specific scenario distortions
        if sc["tamper"] == "ela_tamper":
            # Splice high-frequency noise block onto portrait
            noise = np.random.randint(40, 200, (140, 140, 3), dtype=np.uint8)
            canvas[150:290, 80:220] = noise
        elif sc["tamper"] == "blur_glare":
            # Apply Gaussian Blur
            canvas = cv2.GaussianBlur(canvas, (21, 21), 0)
            # Add specular glare blob
            cv2.circle(canvas, (700, 200), 80, (255, 255, 255), -1)
            cv2.circle(canvas, (700, 200), 120, (250, 250, 250), -1)

        file_name = f"{sc['tag']}.jpg"
        file_path = os.path.join(DEMO_DIR, file_name)

        if sc["tamper"] == "ela_tamper":
            # Save using PIL with Photoshop EXIF tag
            pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
            exif = pil_img.getexif()
            exif[305] = "Adobe Photoshop 2024 (Windows)"  # Tag 305: Software
            pil_img.save(file_path, "JPEG", quality=95, exif=exif)
        else:
            cv2.imwrite(file_path, canvas)

        # Compute SHA-256
        with open(file_path, "rb") as f:
            bytes_content = f.read()
        sha256_hash = hashlib.sha256(bytes_content).hexdigest()

        # Database Insertion
        ref_no = f"VS-DEMO-{sc['tag'][-4:]}"
        existing = db.query(Screening).filter(Screening.reference_no == ref_no).first()
        if existing:
            db.delete(existing)
            db.commit()

        screening = Screening(
            reference_no=ref_no,
            officer_id=officer_id,
            document_type="PASSPORT_TD3",
            issuing_country_code="IND",
            status=ScreeningStatus.COMPLETED,
            is_synthetic=True,
            scenario_tag=sc["tag"],
            processing_time_ms=1180
        )
        db.add(screening)
        db.flush()

        doc_rec = Document(
            screening_id=screening.id,
            original_filename=file_name,
            storage_path=file_path,
            processed_path=file_path,
            file_size_bytes=len(bytes_content),
            mime_type="image/jpeg",
            sha256_hash=sha256_hash,
            is_encrypted=False
        )
        db.add(doc_rec)

        # Quality Record
        is_poor = (sc["tamper"] == "blur_glare")
        q_rec = QualityAssessment(
            screening_id=screening.id,
            overall_score=42.0 if is_poor else 94.0,
            is_acceptable=not is_poor,
            blur_score=45.0 if is_poor else 165.0,
            brightness_score=210.0 if is_poor else 135.0,
            glare_score=0.12 if is_poor else 0.01,
            resolution_dpi=150 if is_poor else 300,
            orientation_detected=0,
            is_cropped=False,
            readability_score=0.55 if is_poor else 0.95,
            issues_detected=["Severe motion blur", "Specular flash glare"] if is_poor else [],
            rescan_recommended=is_poor
        )
        db.add(q_rec)

        # MRZ Record
        valid_checks = (sc["tamper"] != "mrz_mismatch")
        mrz_rec = MRZRecord(
            screening_id=screening.id,
            raw_mrz_text=f"{l1}\n{l2}",
            format="TD3",
            doc_type_code="P",
            issuing_country="IND",
            surname=surname,
            given_names=given,
            document_number=mrz_doc_no,
            nationality="IND",
            dob=sc["dob_mrz"],
            sex=sc["sex"],
            expiry_date=sc["exp_mrz"],
            doc_number_check=valid_checks,
            dob_check=True,
            expiry_check=True,
            composite_check=valid_checks,
            cross_check_matches={"document_number": valid_checks, "dob": True, "surname": True}
        )
        db.add(mrz_rec)

        # ELA Heatmap
        heatmap_path = os.path.join(settings.PROCESSED_DIR, f"{screening.reference_no}_ela.jpg")
        ela_res = run_error_level_analysis(file_path, heatmap_path)

        # Forensic findings
        forensic_list = []
        for f_item in ela_res.get("findings", []):
            ff = ForensicFinding(
                screening_id=screening.id,
                analysis_method=ForensicMethod(f_item["analysis_method"]),
                severity=FindingSeverity(f_item["severity"]),
                region_bbox=f_item.get("region_bbox"),
                title=f_item["title"],
                explanation=f_item["explanation"],
                technical_details=f_item.get("technical_details", {}),
                limitations=f_item["limitations"],
                recommended_action=f_item["recommended_action"]
            )
            db.add(ff)
            forensic_list.append(ff)

        if sc["tamper"] == "ela_tamper":
            ff_meta = ForensicFinding(
                screening_id=screening.id,
                analysis_method=ForensicMethod.METADATA,
                severity=FindingSeverity.CRITICAL,
                title="Consumer Photo Manipulation Software Signature",
                explanation="EXIF headers identify provenance from Adobe Photoshop 2024.",
                technical_details={"software": "Adobe Photoshop 2024"},
                limitations="Metadata can be stripped in web gateways.",
                recommended_action="Escalate to Senior Reviewer for physical credential demand."
            )
            db.add(ff_meta)
            forensic_list.append(ff_meta)

        # Risk Evaluation
        eval_risk = evaluate_screening_risk(q_rec, mrz_rec, [], forensic_list)
        risk_rec = RiskAssessment(
            screening_id=screening.id,
            risk_level=eval_risk["risk_level"],
            composite_score=eval_risk["composite_score"],
            engine_version=eval_risk["engine_version"],
            rules_triggered=eval_risk["rules_triggered"]
        )
        db.add(risk_rec)

        screening.risk_level = eval_risk["risk_level"]
        screening.risk_score = eval_risk["composite_score"]

        # If HIGH_RISK or REVIEW, create Case
        if eval_risk["risk_level"] in [RiskLevel.HIGH_RISK, RiskLevel.REVIEW]:
            case = Case(
                case_number=f"CASE-DEMO-{sc['tag'][-4:]}",
                screening_id=screening.id,
                assigned_officer_id=officer_id,
                status=CaseStatus.OPEN if eval_risk["risk_level"] == RiskLevel.HIGH_RISK else CaseStatus.IN_REVIEW,
                priority=CasePriority.HIGH if eval_risk["risk_level"] == RiskLevel.HIGH_RISK else CasePriority.MEDIUM,
                summary=f"Investigation opened for demo scenario {sc['tag']}: {sc['description']}",
                notes=[{
                    "id": str(uuid.uuid4()),
                    "author": "System Intake",
                    "text": f"Automated intake logged scenario {sc['tag']}.",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }]
            )
            db.add(case)

        # Audit Chain Entry
        last_audit = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_audit.current_hash if last_audit else "0" * 64
        event_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta_payload = {"scenario": sc["tag"], "ref": ref_no, "risk": eval_risk["risk_level"].value}
        block_hash = calculate_record_hash(prev_hash, screening.id, "SYNTHETIC_SCENARIO_SEEDED", officer_id, event_timestamp, meta_payload)
        audit_entry = AuditLog(
            event_type="SYNTHETIC_SCENARIO_SEEDED",
            actor_id=officer_id,
            actor_role="SYSTEM_EVALUATOR",
            screening_id=screening.id,
            action_description=f"Synthetic demonstration scenario {sc['tag']} seeded into database",
            metadata_json=meta_payload,
            prev_record_hash=prev_hash,
            current_hash=block_hash
        )
        db.add(audit_entry)

        db.commit()
        print(f" -> Successfully seeded {ref_no}: {eval_risk['risk_level'].value} (Score: {eval_risk['composite_score']})")

    db.close()
    print("\nAll 5 demonstration scenarios successfully generated and cataloged!")


if __name__ == "__main__":
    generate_scenarios()
