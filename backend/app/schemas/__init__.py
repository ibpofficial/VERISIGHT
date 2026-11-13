from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.app.models import (
    UserRole, ScreeningStatus, RiskLevel, CaseStatus, 
    CasePriority, ForensicMethod, FindingSeverity, ValidationStatus
)


# Auth & User Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: UserRole


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole
    badge_number: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    badge_number: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    badge_number: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Quality Assessment Schemas
class QualityResponse(BaseModel):
    overall_score: float
    is_acceptable: bool
    blur_score: float
    brightness_score: float
    glare_score: float
    resolution_dpi: int
    orientation_detected: int
    is_cropped: bool
    readability_score: float
    issues_detected: List[str]
    rescan_recommended: bool

    model_config = ConfigDict(from_attributes=True)


# Extracted Field Schemas
class BoundingBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class ExtractedFieldResponse(BaseModel):
    id: str
    field_name: str
    original_value: str
    current_value: str
    confidence: float
    bounding_box: Dict[str, Any]
    validation_status: ValidationStatus
    is_corrected: bool
    corrected_by: Optional[str] = None
    corrected_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FieldCorrectionRequest(BaseModel):
    new_value: str
    notes: Optional[str] = None


# MRZ Schemas
class MRZResponse(BaseModel):
    raw_mrz_text: str
    format: str
    doc_type_code: str
    issuing_country: str
    surname: str
    given_names: str
    document_number: str
    nationality: str
    dob: str
    sex: str
    expiry_date: str
    optional_data: Optional[str] = None
    doc_number_check: bool
    dob_check: bool
    expiry_check: bool
    composite_check: bool
    cross_check_matches: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# Forensic Findings Schemas
class ForensicFindingResponse(BaseModel):
    id: str
    analysis_method: ForensicMethod
    severity: FindingSeverity
    region_bbox: Optional[Dict[str, Any]] = None
    title: str
    explanation: str
    technical_details: Dict[str, Any]
    limitations: str
    recommended_action: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Risk Assessment Schemas
class RiskRuleContribution(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    weight: float
    description: str
    is_critical: bool


class RiskAssessmentResponse(BaseModel):
    risk_level: RiskLevel
    composite_score: float
    engine_version: str
    rules_triggered: List[Dict[str, Any]]
    reviewer_override_level: Optional[RiskLevel] = None
    override_reason: Optional[str] = None
    overridden_by: Optional[str] = None
    overridden_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RiskOverrideRequest(BaseModel):
    override_level: RiskLevel
    reason: str = Field(..., min_length=10)


# Screening Schemas
class ScreeningCreateRequest(BaseModel):
    document_type: str = "PASSPORT_TD3"
    issuing_country_code: Optional[str] = "IND"
    is_synthetic: bool = False
    scenario_tag: Optional[str] = None


class ScreeningResponse(BaseModel):
    id: str
    reference_no: str
    officer_id: str
    document_type: str
    issuing_country_code: Optional[str]
    status: ScreeningStatus
    risk_level: Optional[RiskLevel]
    risk_score: Optional[float]
    processing_time_ms: Optional[int]
    is_synthetic: bool
    scenario_tag: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Case Schemas
class CaseCreateRequest(BaseModel):
    screening_id: str
    priority: Optional[CasePriority] = CasePriority.MEDIUM
    summary: Optional[str] = None


class CaseNoteCreate(BaseModel):
    text: str = Field(..., min_length=3)


class CaseStatusUpdate(BaseModel):
    status: CaseStatus
    priority: Optional[CasePriority] = None
    assigned_officer_id: Optional[str] = None
    resolution_notes: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    case_number: str
    screening_id: str
    assigned_officer_id: Optional[str]
    status: CaseStatus
    priority: CasePriority
    summary: str
    notes: List[Dict[str, Any]]
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Audit Schemas
class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    actor_id: Optional[str]
    actor_role: str
    screening_id: Optional[str]
    case_id: Optional[str]
    action_description: str
    metadata_json: Dict[str, Any]
    prev_record_hash: str
    current_hash: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditIntegrityResponse(BaseModel):
    is_intact: bool
    total_blocks_verified: int
    first_block_timestamp: Optional[datetime]
    latest_block_timestamp: Optional[datetime]
    latest_hash: Optional[str]
    corrupted_at_id: Optional[int] = None
    details: str
