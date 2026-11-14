export type UserRole = 'ADMINISTRATOR' | 'SCREENING_OFFICER' | 'SENIOR_REVIEWER' | 'AUDITOR';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  badge_number?: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

export type ScreeningStatus = 'PENDING' | 'PREPROCESSING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
export type RiskLevel = 'CLEAR' | 'REVIEW' | 'HIGH_RISK';
export type CaseStatus = 'OPEN' | 'IN_REVIEW' | 'ESCALATED' | 'RESOLVED' | 'RETURNED';
export type CasePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface Screening {
  id: string;
  reference_no: string;
  officer_id: string;
  document_type: string;
  issuing_country_code?: string;
  status: ScreeningStatus;
  risk_level?: RiskLevel;
  risk_score?: number;
  processing_time_ms?: number;
  is_synthetic: boolean;
  scenario_tag?: string;
  created_at: string;
  updated_at: string;
}

export interface QualityAssessment {
  overall_score: number;
  is_acceptable: boolean;
  blur_score: number;
  brightness_score: number;
  glare_score: number;
  resolution_dpi: number;
  orientation_detected: number;
  is_cropped: boolean;
  readability_score: number;
  issues_detected: string[];
  rescan_recommended: boolean;
}

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ExtractedField {
  id: string;
  field_name: string;
  original_value: string | null;
  current_value: string | null;
  confidence: number | null;
  bounding_box: BoundingBox | null;
  validation_status: 'VALID' | 'WARNING' | 'INVALID' | 'INVALID_FORMAT' | 'LOW_CONFIDENCE' | 'MISSING' | 'UNREADABLE' | 'CORRECTED';
  is_corrected: boolean;
  notes?: string;
}

export interface MRZRecord {
  raw_mrz_text: string;
  format: string;
  doc_type_code: string;
  issuing_country: string;
  surname: string;
  given_names: string;
  document_number: string;
  nationality: string;
  dob: string;
  sex: string;
  expiry_date: string;
  optional_data?: string;
  doc_number_check: boolean;
  dob_check: boolean;
  expiry_check: boolean;
  composite_check: boolean;
  cross_check_matches: Record<string, boolean>;
}

export interface ForensicFinding {
  id: string;
  analysis_method: 'ELA' | 'METADATA' | 'TEXTURE' | 'ALIGNMENT' | 'PORTRAIT';
  severity: 'INFORMATIONAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  region_bbox?: BoundingBox;
  title: string;
  explanation: string;
  technical_details: Record<string, any>;
  limitations: string;
  recommended_action: string;
  created_at: string;
}

export interface RiskRule {
  rule_id: string;
  rule_name: string;
  category: string;
  weight: number;
  description: string;
  is_critical: boolean;
}

export interface RiskAssessment {
  risk_level: RiskLevel;
  composite_score: number;
  engine_version: string;
  rules_triggered: RiskRule[];
  reviewer_override_level?: RiskLevel;
  override_reason?: string;
  overridden_by?: string;
  overridden_at?: string;
}

export interface CaseNote {
  id: string;
  author: string;
  text: string;
  timestamp: string;
}

export interface Case {
  id: string;
  case_number: string;
  screening_id: string;
  assigned_officer_id?: string;
  status: CaseStatus;
  priority: CasePriority;
  summary: string;
  notes: CaseNote[];
  resolution_notes?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLogItem {
  id: number;
  event_type: string;
  actor_id?: string;
  actor_role: string;
  screening_id?: string;
  case_id?: string;
  action_description: string;
  metadata_json: Record<string, any>;
  prev_record_hash: string;
  current_hash: string;
  timestamp: string;
}

export interface AuditIntegrityResult {
  is_intact: boolean;
  total_blocks_verified: number;
  first_block_timestamp?: string;
  latest_block_timestamp?: string;
  latest_hash?: string;
  corrupted_at_id?: number;
  details: string;
}
