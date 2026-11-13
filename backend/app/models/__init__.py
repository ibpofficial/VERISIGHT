import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey, 
    Enum, JSON, BigInteger, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class UserRole(str, enum.Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    SCREENING_OFFICER = "SCREENING_OFFICER"
    SENIOR_REVIEWER = "SENIOR_REVIEWER"
    AUDITOR = "AUDITOR"


class ScreeningStatus(str, enum.Enum):
    PENDING = "PENDING"
    PREPROCESSING = "PREPROCESSING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(str, enum.Enum):
    CLEAR = "CLEAR"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"


class CaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    RETURNED = "RETURNED"


class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ForensicMethod(str, enum.Enum):
    ELA = "ELA"
    METADATA = "METADATA"
    TEXTURE = "TEXTURE"
    ALIGNMENT = "ALIGNMENT"
    PORTRAIT = "PORTRAIT"


class FindingSeverity(str, enum.Enum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValidationStatus(str, enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SCREENING_OFFICER)
    badge_number = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    login_activities = relationship("LoginActivity", back_populates="user", cascade="all, delete-orphan")
    screenings = relationship("Screening", back_populates="officer")
    assigned_cases = relationship("Case", back_populates="assigned_officer")


class LoginActivity(Base):
    __tablename__ = "login_activities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="login_activities")


class Screening(Base):
    __tablename__ = "screenings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    reference_no = Column(String(32), unique=True, nullable=False, index=True)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    document_type = Column(String(64), nullable=False)  # PASSPORT_TD3, VISA_MRV_A, NATIONAL_ID
    issuing_country_code = Column(String(3), nullable=True)
    status = Column(Enum(ScreeningStatus), default=ScreeningStatus.PENDING, nullable=False, index=True)
    risk_level = Column(Enum(RiskLevel), nullable=True, index=True)
    risk_score = Column(Float, nullable=True)  # 0.0 - 100.0
    processing_time_ms = Column(Integer, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False, index=True)
    scenario_tag = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    officer = relationship("User", back_populates="screenings")
    document = relationship("Document", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    quality_assessment = relationship("QualityAssessment", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="screening", cascade="all, delete-orphan")
    mrz_record = relationship("MRZRecord", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    forensic_findings = relationship("ForensicFinding", back_populates="screening", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    case = relationship("Case", back_populates="screening", uselist=False, cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    processed_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(128), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    is_encrypted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    screening = relationship("Screening", back_populates="document")


class QualityAssessment(Base):
    __tablename__ = "quality_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    overall_score = Column(Float, nullable=False)  # 0.0 to 1.0
    is_acceptable = Column(Boolean, nullable=False)
    blur_score = Column(Float, nullable=False)  # Laplacian variance
    brightness_score = Column(Float, nullable=False)  # Mean luminance
    glare_score = Column(Float, nullable=False)  # Saturated pixel ratio
    resolution_dpi = Column(Integer, nullable=False)
    orientation_detected = Column(Integer, default=0, nullable=False)  # 0, 90, 180, 270
    is_cropped = Column(Boolean, default=False, nullable=False)
    readability_score = Column(Float, nullable=False)
    issues_detected = Column(JSON, default=list, nullable=False)
    rescan_recommended = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    screening = relationship("Screening", back_populates="quality_assessment")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(64), nullable=False)  # surname, document_number, dob, etc.
    original_value = Column(Text, nullable=False)
    current_value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    bounding_box = Column(JSON, nullable=False)  # {"x": int, "y": int, "w": int, "h": int}
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.VALID, nullable=False)
    is_corrected = Column(Boolean, default=False, nullable=False)
    corrected_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    corrected_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    screening = relationship("Screening", back_populates="extracted_fields")


class MRZRecord(Base):
    __tablename__ = "mrz_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    raw_mrz_text = Column(Text, nullable=False)
    format = Column(String(16), nullable=False)  # TD1, TD2, TD3
    doc_type_code = Column(String(4), nullable=False)
    issuing_country = Column(String(3), nullable=False)
    surname = Column(String(128), nullable=False)
    given_names = Column(String(128), nullable=False)
    document_number = Column(String(32), nullable=False)
    nationality = Column(String(3), nullable=False)
    dob = Column(String(10), nullable=False)  # YYMMDD
    sex = Column(String(2), nullable=False)
    expiry_date = Column(String(10), nullable=False)  # YYMMDD
    optional_data = Column(String(64), nullable=True)
    doc_number_check = Column(Boolean, nullable=False)
    dob_check = Column(Boolean, nullable=False)
    expiry_check = Column(Boolean, nullable=False)
    composite_check = Column(Boolean, nullable=False)
    cross_check_matches = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    screening = relationship("Screening", back_populates="mrz_record")


class ForensicFinding(Base):
    __tablename__ = "forensic_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_method = Column(Enum(ForensicMethod), nullable=False)
    severity = Column(Enum(FindingSeverity), nullable=False)
    region_bbox = Column(JSON, nullable=True)  # {"x": int, "y": int, "w": int, "h": int}
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    technical_details = Column(JSON, default=dict, nullable=False)
    limitations = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    screening = relationship("Screening", back_populates="forensic_findings")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    composite_score = Column(Float, nullable=False)  # 0.0 - 100.0
    engine_version = Column(String(32), default="VERISIGHT-RULES-v1.2", nullable=False)
    rules_triggered = Column(JSON, default=list, nullable=False)
    reviewer_override_level = Column(Enum(RiskLevel), nullable=True)
    override_reason = Column(Text, nullable=True)
    overridden_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    overridden_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    screening = relationship("Screening", back_populates="risk_assessment")


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_number = Column(String(32), unique=True, nullable=False, index=True)
    screening_id = Column(String(36), ForeignKey("screenings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    assigned_officer_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False, index=True)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    notes = Column(JSON, default=list, nullable=False)  # [{"id": str, "author": str, "text": str, "timestamp": str}]
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    screening = relationship("Screening", back_populates="case")
    assigned_officer = relationship("User", back_populates="assigned_cases")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String(32), nullable=False)
    screening_id = Column(String(36), nullable=True, index=True)
    case_id = Column(String(36), nullable=True, index=True)
    action_description = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    prev_record_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

