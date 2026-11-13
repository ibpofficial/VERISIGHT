# VERISIGHT — MASTER SYSTEM SPECIFICATION
## SIH 2026 Problem Statement 26188: AI-Based Fake Identity & Document Screening System
### Ministry of Home Affairs (MHA) – SSB, Police II Division | Category: Software / Blockchain & Cybersecurity

---

## 1. Executive Summary & Objective

**VERISIGHT** is an enterprise-grade, explainable, and privacy-preserving document and identity screening platform designed to assist authorized security and immigration officers (Screening Officers, Senior Reviewers, Administrators, and Auditors). The platform ingests identity documents (primarily travel passports conforming to ICAO 9303, visas, and national identity cards), extracts structured data via Optical Character Recognition (OCR), performs rigorous cryptographic and structural validation (Machine Readable Zone — MRZ), executes multi-factor digital image forensics (Error Level Analysis, texture variance, text alignment, portrait tampering), and computes a deterministic, explainable risk assessment categorized as **CLEAR**, **REVIEW**, or **HIGH RISK**.

### Core Objective
Reduce manual fatigue and eliminate human oversight in preliminary identity screening by consolidating multi-layered forensic inspection into a unified, auditable, and transparent workflow while keeping a human officer strictly in the decision loop.

---

## 2. Non-Negotiable Operational Principles & Scope Boundaries

1. **Decision Support, Not Automated Authority**: The system provides intelligence and triage indicators. It never issues automated criminal accusations or unilateral final legal rejections. A human officer always makes the final call.
2. **No Government Database Claims**: The prototype does not claim direct, live integration with national sovereign databases (e.g., CCTNS, INTERPOL SLTD, national civil registries) without authorized secure gateway access. Authenticity is assessed based on internal document consistency, standards compliance, and image forensics.
3. **No Fabricated Accuracy Claims**: Accuracy metrics, ROC curves, and test scores must be tied to verified benchmarks and synthetic datasets. No invented "99.9% fraud detection" claims.
4. **Privacy & Ephemeral Biometrics**: No raw biometric templates or live face captures are stored permanently. All document evidence is encrypted at rest using AES-256 and hashed with SHA-256 upon ingestion.
5. **Anti-Slop Enterprise Standard**: All user interface surfaces, copywriting, empty states, error messages, and tooltips are engineered specifically for law enforcement and border security personnel. No placeholder metrics, no lorem ipsum, no emoji-as-icons, and no generic template styling.
6. **Synthetic Demo Compliance**: All demo identities and passport images are strictly synthetic and fabricated. No actual civilian PII is utilized.

---

## 3. System Architecture & Monorepo Topology

VERISIGHT is structured as an enterprise monorepo:

```
VERISIGHT/
├── docs/                               # Master specifications and architectural documentation
│   ├── MASTER_SPEC.md                  # This authoritative document
│   ├── ARCHITECTURE.md                 # System topology, data flow, security model
│   ├── API.md                          # Comprehensive OpenAPI/REST documentation
│   ├── RISK_RULES.md                   # Formal rule definitions and weights
│   ├── LIMITATIONS.md                  # Known constraints and forensic caveats
│   ├── DESIGN_SYSTEM.md                # Liquid glass design system and component spec
│   ├── DEMO_SCRIPT.md                  # Step-by-step jury walkthrough script
│   ├── JURY_QA.md                      # Anticipated jury inquiries and rigorous responses
│   └── CHECKLIST.md                    # Tracking matrix for all deliverable criteria
├── backend/                            # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                        # REST route controllers
│   │   │   ├── v1/
│   │   │   │   ├── auth.py             # Login, refresh, password reset
│   │   │   │   ├── dashboard.py        # Command center metrics and analytics
│   │   │   │   ├── screenings.py       # Screening initiation and pipeline dispatch
│   │   │   │   ├── documents.py        # File ingest, download, field overrides
│   │   │   │   ├── mrz.py              # MRZ validation details
│   │   │   │   ├── forensics.py        # Heatmap generator, ELA, texture, metadata
│   │   │   │   ├── face.py             # Consent-gated face verification
│   │   │   │   ├── risk.py             # Risk calculation and manual override
│   │   │   │   ├── cases.py            # Investigation center case lifecycle
│   │   │   │   ├── reports.py          # PDF generation and download
│   │   │   │   ├── audit.py            # Tamper-evident log and chain validation
│   │   │   │   └── admin.py            # User management, config, engine health
│   │   ├── core/                       # Security, config, hashing, database session
│   │   │   ├── config.py               # Pydantic BaseSettings (.env integration)
│   │   │   ├── security.py             # Password hashing (argon2/bcrypt), JWT encode/decode
│   │   │   ├── database.py             # SQLAlchemy AsyncEngine / Sessionmaker
│   │   │   └── audit_chain.py          # Cryptographic SHA-256 chain calculation
│   │   ├── engines/                    # Core decoupled processing modules
│   │   │   ├── quality.py              # Blur (Laplacian), glare, brightness, resolution
│   │   │   ├── preprocessing.py        # Deskew, denoise, contrast, perspective crop
│   │   │   ├── ocr/                    # OCR engine interface (PaddleOCR + Tesseract fallback)
│   │   │   │   ├── base.py             # OCREngine abstract base class
│   │   │   │   ├── tesseract_engine.py # PyTesseract implementation
│   │   │   │   └── paddle_engine.py    # PaddleOCR implementation with CPU fallback
│   │   │   ├── mrz/                    # ICAO Doc 9303 MRZ Parser
│   │   │   │   ├── parser.py           # TD1, TD2, TD3 format parser
│   │   │   │   └── check_digits.py     # 7-3-1 weight check digit algorithm
│   │   │   ├── forensics/              # Digital image tampering forensics
│   │   │   │   ├── ela.py              # Error Level Analysis with difference maps
│   │   │   │   ├── metadata.py         # EXIF, software tag, history inspection
│   │   │   │   ├── texture.py          # Local Binary Patterns (LBP) & noise analysis
│   │   │   │   ├── alignment.py        # Baseline text line and character pitch check
│   │   │   │   └── portrait.py         # Face bounding box edge discontinuity check
│   │   │   ├── risk/                   # Deterministic, explainable risk rules
│   │   │   │   ├── rules.py            # Configurable, versioned risk rules
│   │   │   │   └── evaluator.py        # Aggregator avoiding correlated double-counting
│   │   │   └── reports/                # ReportLab institutional PDF generator
│   │   │       ├── generator.py        # 5-page PDF compiler
│   │   │       └── layout.py           # Custom canvas, headers, footers, security marks
│   │   ├── models/                     # SQLAlchemy ORM Models (11 tables)
│   │   ├── schemas/                    # Pydantic Schemas for requests/responses
│   │   └── main.py                     # FastAPI application factory
│   ├── alembic/                        # DB Migration scripts
│   ├── tests/                          # Backend test suite (pytest)
│   └── Dockerfile                      # Production backend container
├── frontend/                           # React + TypeScript Vite Frontend
│   ├── src/
│   │   ├── components/                 # Reusable UI component library (15 components)
│   │   │   ├── glass/                  # Liquid glass primitive components
│   │   │   ├── layout/                 # Sidebar, Topbar, AppShell
│   │   │   ├── common/                 # MetricCard, RiskBadge, EmptyState, Skeletons
│   │   │   └── forensic/               # Dual viewer, heatmap canvas, MRZ indicator
│   │   ├── pages/                      # All 18 frontend pages
│   │   ├── hooks/                      # Custom hooks (auth, query, filters, glass)
│   │   ├── services/                   # Axios/Fetch API client bindings
│   │   ├── types/                      # TypeScript domain definitions
│   │   └── index.css                   # Tailwind CSS styling and liquid glass filters
│   ├── tests/                          # Vitest / React Testing Library frontend tests
│   └── Dockerfile                      # Nginx production frontend container
├── scripts/                            # Operational & demo generation scripts
│   ├── generate_synthetic_data.py      # Generates 5 distinct synthetic passport scenarios
│   └── seed_database.py                # Seeds 4 demo user roles & historical cases
├── docker-compose.yml                  # Full stack orchestration (backend, frontend, postgres, worker)
└── .env.example                        # Template environment variables
```

---

## 4. Database Schema (11 Core Tables)

The persistent layer is built on PostgreSQL with strict referential integrity, indexes on frequently queried foreign keys, and audit immutability:

1. **`users`**:
   - `id` (UUID, Primary Key)
   - `email` (VARCHAR(255), Unique, Indexed)
   - `password_hash` (VARCHAR(255), Not Null)
   - `full_name` (VARCHAR(255), Not Null)
   - `role` (ENUM: `ADMINISTRATOR`, `SCREENING_OFFICER`, `SENIOR_REVIEWER`, `AUDITOR`)
   - `badge_number` (VARCHAR(64), Nullable)
   - `is_active` (BOOLEAN, Default True)
   - `created_at` (TIMESTAMPTZ, Default NOW())
   - `updated_at` (TIMESTAMPTZ, Default NOW())

2. **`login_activities`**:
   - `id` (UUID, Primary Key)
   - `user_id` (UUID, Foreign Key -> `users.id`, Indexed)
   - `ip_address` (VARCHAR(45), Not Null)
   - `user_agent` (TEXT, Not Null)
   - `success` (BOOLEAN, Not Null)
   - `failure_reason` (VARCHAR(255), Nullable)
   - `created_at` (TIMESTAMPTZ, Default NOW())

3. **`screenings`**:
   - `id` (UUID, Primary Key)
   - `reference_no` (VARCHAR(32), Unique, Indexed) — Format: `VS-YYYYMMDD-XXXX`
   - `officer_id` (UUID, Foreign Key -> `users.id`, Indexed)
   - `document_type` (VARCHAR(64), Not Null) — e.g., `PASSPORT_TD3`, `VISA_MRV_A`, `NATIONAL_ID`
   - `issuing_country_code` (VARCHAR(3), Nullable)
   - `status` (ENUM: `PENDING`, `PREPROCESSING`, `ANALYZING`, `COMPLETED`, `FAILED`)
   - `risk_level` (ENUM: `CLEAR`, `REVIEW`, `HIGH_RISK`, Nullable)
   - `risk_score` (FLOAT, Nullable) — 0.0 to 100.0
   - `processing_time_ms` (INTEGER, Nullable)
   - `is_synthetic` (BOOLEAN, Default False, Indexed)
   - `scenario_tag` (VARCHAR(64), Nullable) — e.g., `CLEAN`, `EXPIRED`, `MRZ_MISMATCH`
   - `created_at` (TIMESTAMPTZ, Default NOW(), Indexed)
   - `updated_at` (TIMESTAMPTZ, Default NOW())

4. **`documents`**:
   - `id` (UUID, Primary Key)
   - `screening_id` (UUID, Foreign Key -> `screenings.id`, Unique, Indexed)
   - `original_filename` (VARCHAR(255), Not Null)
   - `storage_path` (VARCHAR(512), Not Null)
   - `processed_path` (VARCHAR(512), Nullable)
   - `file_size_bytes` (INTEGER, Not Null)
   - `mime_type` (VARCHAR(128), Not Null)
   - `sha256_hash` (VARCHAR(64), Not Null, Indexed) — Ingest verification hash
   - `is_encrypted` (BOOLEAN, Default True)
   - `created_at` (TIMESTAMPTZ, Default NOW())

5. **`quality_assessments`**:
   - `id` (UUID, Primary Key)
   - `screening_id` (UUID, Foreign Key -> `screenings.id`, Unique, Indexed)
   - `overall_score` (FLOAT, Not Null) — 0.0 to 1.0
   - `is_acceptable` (BOOLEAN, Not Null)
   - `blur_score` (FLOAT, Not Null) — Laplacian variance
   - `brightness_score` (FLOAT, Not Null) — Mean luminance
   - `glare_score` (FLOAT, Not Null) — Saturated pixel ratio
   - `resolution_dpi` (INTEGER, Not Null)
   - `orientation_detected` (INTEGER, Not Null) — 0, 90, 180, 270
   - `is_cropped` (BOOLEAN, Not Null)
   - `readability_score` (FLOAT, Not Null)
   - `issues_detected` (JSONB, Default '[]')
   - `rescan_recommended` (BOOLEAN, Default False)
   - `created_at` (TIMESTAMPTZ, Default NOW())

6. **`extracted_fields`**:
   - `id` (UUID, Primary Key)
   - `screening_id` (UUID, Foreign Key -> `screenings.id`, Indexed)
   - `field_name` (VARCHAR(64), Not Null) — e.g., `surname`, `given_names`, `document_number`, `dob`, `sex`, `expiry_date`
   - `original_value` (TEXT, Not Null)
   - `current_value` (TEXT, Not Null)
   - `confidence` (FLOAT, Not Null) — 0.0 to 1.0
   - `bounding_box` (JSONB, Not Null) — `{ "x": int, "y": int, "w": int, "h": int }`
   - `validation_status` (ENUM: `VALID`, `WARNING`, `INVALID`)
   - `is_corrected` (BOOLEAN, Default False)
   - `corrected_by` (UUID, Foreign Key -> `users.id`, Nullable)
   - `corrected_at` (TIMESTAMPTZ, Nullable)
   - `notes` (TEXT, Nullable)

7. **`mrz_records`**:
   - `id` (UUID, Primary Key)
   - `screening_id` (UUID, Foreign Key -> `screenings.id`, Unique, Indexed)
   - `raw_mrz_text` (TEXT, Not Null)
   - `format` (VARCHAR(16), Not Null) — `TD1`, `TD2`, `TD3`
   - `doc_type_code` (VARCHAR(4), Not Null)
   - `issuing_country` (VARCHAR(3), Not Null)
   - `surname` (VARCHAR(128), Not Null)
   - `given_names` (VARCHAR(128), Not Null)
   - `document_number` (VARCHAR(32), Not Null)
   - `nationality` (VARCHAR(3), Not Null)
   - `dob` (VARCHAR(10), Not Null) — YYMMDD
   - `sex` (VARCHAR(2), Not Null)
   - `expiry_date` (VARCHAR(10), Not Null) — YYMMDD
   - `optional_data` (VARCHAR(64), Nullable)
   - `doc_number_check` (BOOLEAN, Not Null)
   - `dob_check` (BOOLEAN, Not Null)
   - `expiry_check` (BOOLEAN, Not Null)
   - `composite_check` (BOOLEAN, Not Null)
   - `cross_check_matches` (JSONB, Not Null) — Visual vs MRZ field comparisons
   - `created_at` (TIMESTAMPTZ, Default NOW())

8. **`forensic_findings`**:
   - `id` (UUID, Primary Key)
   - `screening_id` (UUID, Foreign Key -> `screenings.id`, Indexed)
   - `analysis_method` (ENUM: `ELA`, `METADATA`, `TEXTURE`, `ALIGNMENT`, `PORTRAIT`)
   - `severity` (ENUM: `INFORMATIONAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
   - `region_bbox` (JSONB, Nullable) — `{ "x": int, "y": int, "w": int, "h": int }`
   - `title` (VARCHAR(255), Not Null)
   - `explanation` (TEXT, Not Null)
   - `technical_details` (JSONB, Not Null)
   - `limitations` (TEXT, Not Null) — E.g., "ELA is an indicator, not definitive proof"
   - `recommended_action` (TEXT, Not Null)
   - `created_at` (TIMESTAMPTZ, Default NOW())

9. **`risk_assessments`**:
   - `id` (UUID, Primary Key)
   - `screening_id` (UUID, Foreign Key -> `screenings.id`, Unique, Indexed)
   - `risk_level` (ENUM: `CLEAR`, `REVIEW`, `HIGH_RISK`)
   - `composite_score` (FLOAT, Not Null) — 0.0 to 100.0
   - `engine_version` (VARCHAR(32), Not Null)
   - `rules_triggered` (JSONB, Not Null) — Array of rule IDs, weights, and contributions
   - `reviewer_override_level` (ENUM: `CLEAR`, `REVIEW`, `HIGH_RISK`, Nullable)
   - `override_reason` (TEXT, Nullable)
   - `overridden_by` (UUID, Foreign Key -> `users.id`, Nullable)
   - `overridden_at` (TIMESTAMPTZ, Nullable)
   - `created_at` (TIMESTAMPTZ, Default NOW())

10. **`cases`**:
    - `id` (UUID, Primary Key)
    - `case_number` (VARCHAR(32), Unique, Indexed) — Format: `CASE-YYYY-XXXXX`
    - `screening_id` (UUID, Foreign Key -> `screenings.id`, Unique, Indexed)
    - `assigned_officer_id` (UUID, Foreign Key -> `users.id`, Nullable, Indexed)
    - `status` (ENUM: `OPEN`, `IN_REVIEW`, `ESCALATED`, `RESOLVED`, `RETURNED`)
    - `priority` (ENUM: `LOW`, `MEDIUM`, `HIGH`, `URGENT`)
    - `summary` (TEXT, Not Null)
    - `notes` (JSONB, Default '[]') — Array of `{ id, author, text, timestamp }`
    - `resolution_notes` (TEXT, Nullable)
    - `resolved_at` (TIMESTAMPTZ, Nullable)
    - `created_at` (TIMESTAMPTZ, Default NOW(), Indexed)
    - `updated_at` (TIMESTAMPTZ, Default NOW())

11. **`audit_log`** (Tamper-Evident SHA-256 Hash Chain):
    - `id` (BIGSERIAL, Primary Key)
    - `event_type` (VARCHAR(64), Not Null) — e.g., `DOCUMENT_INGESTED`, `FIELD_MODIFIED`, `RISK_OVERRIDDEN`, `CASE_ESCALATED`
    - `actor_id` (UUID, Foreign Key -> `users.id`, Nullable)
    - `actor_role` (VARCHAR(32), Not Null)
    - `screening_id` (UUID, Nullable, Indexed)
    - `case_id` (UUID, Nullable, Indexed)
    - `action_description` (TEXT, Not Null)
    - `metadata_json` (JSONB, Default '{}')
    - `prev_record_hash` (VARCHAR(64), Not Null)
    - `current_hash` (VARCHAR(64), Not Null, Indexed) — SHA-256(prev_hash + id + event_type + actor_id + timestamp + metadata)
    - `timestamp` (TIMESTAMPTZ, Default NOW(), Indexed)

---

## 5. Screening & Forensic Pipeline Specification

### Step 1: Upload & Ingestion Gate
- Accepts `image/jpeg`, `image/png`. Secure validation checks magic bytes (not just file extension).
- Maximum upload limit: 15 MB.
- Computes SHA-256 hash immediately upon byte reception; stores hash into `documents.sha256_hash` and initial audit log.
- Generates unique reference code `VS-YYYYMMDD-XXXX`.

### Step 2: Quality Assessment Engine
- **Blur Detection**: Modified Laplacian variance algorithm. Score < 100 flags severe blur.
- **Glare / Overexposure**: Analyzes histogram saturation; flags when > 4% of pixels are pinned at luminance 255.
- **Brightness**: Assesses mean pixel value (ideal: 90 - 200).
- **Resolution**: Verifies image dimensions correspond to >= 300 DPI for standard ID-1/ID-3 dimensions.
- **Rescan Recommendation**: If blur or glare exceeds critical threshold, flags `rescan_recommended=True`. Crucially: **poor quality is marked as UNRELIABLE/RESCAN, NOT as fraudulent intent**.

### Step 3: Preprocessing Engine
- Non-destructive processing: original file is immutably preserved in `documents.storage_path`.
- **Deskew**: Computes Hough Line Transform to detect document boundary angles; applies affine rotation matrix within [-45°, +45°].
- **Perspective Correction**: Extracts four corners of the ID card/passport page; applies homography transformation to generate standard rectilinear view.
- **Contrast Normalization**: CLAHE (Contrast Limited Adaptive Histogram Equalization) applied to luminance channel.

### Step 4: OCR Extraction & Interactive Field Mapping
- **Engine Interface**: Pluggable architecture (`OCREngine` ABC). Primary: PaddleOCR with CPU mode support; Fallback: Tesseract OCR (`pytesseract`).
- **Target Fields**: Document Type, Issuing State, Surname, Given Names, Document Number, Nationality, Date of Birth (DOB), Sex, Expiry Date, Optional Data, MRZ Line 1, MRZ Line 2.
- **Bounding Boxes**: Normalized coordinate format `{ x, y, w, h }` for every detected field.
- **Reviewer Field Correction**: Security officers can correct OCR misreads. Original value is never overwritten; changes are saved in `extracted_fields.current_value`, setting `is_corrected=True` and logging an immutable audit record.

### Step 5: MRZ Verification Engine
- Complies strictly with ICAO Document 9303 (Parts 4, 5, 6, 7).
- Supports TD3 (Passports, 2 lines of 44 characters), TD1 (ID cards, 3 lines of 30 characters), and TD2 (2 lines of 36 characters).
- **Check-Digit Verification**: Weight sequence `[7, 3, 1, 7, 3, 1, ...]`:
  - Document number check digit
  - Date of birth check digit
  - Expiry date check digit
  - Optional field check digit
  - Composite check digit (over doc number + dob + expiry + optional)
- **Cross-Field Consistency**: Compares visual printed field values against MRZ decoded payload. Discrepancies generate a high-priority warning flag.

### Step 6: Multi-Factor Digital Forensic Laboratory
- **Error Level Analysis (ELA)**: Resaves the image at a known JPEG compression quality (95%), computes the absolute pixel difference between original and recompressed image, and scales variance into an ELA heatmap. Highlights localized compression irregularities (e.g., pasted text or modified portrait box).
  - *Disclaimer mandatory*: "ELA indicates compression variance, which may arise from re-saving or multi-source compositing. It is a forensic indicator, not proof of forgery."
- **Metadata Inspection**: Reads EXIF tags, detects editing software traces (e.g., "Photoshop", "GIMP", "Canva"), creation/modification timestamp discrepancies, or stripped EXIF structures.
- **Texture Analysis**: Computes Local Binary Pattern (LBP) variance across text zones and background guilloche patterns. Inconsistent noise variance flags potential cut-and-paste.
- **Text Alignment Analysis**: Measures character baseline linearity and glyph pitch consistency across printed fields to detect font substitutions or digital text overlay.
- **Portrait Region Analysis**: Analyzes the boundary of the passport photo box for edge blending, anomalous gradients, or double borders.

### Step 7: Optional Face Verification Module
- Strictly consent-gated (explicit UI confirmation before camera activation or live photo comparison).
- Detects face in document portrait vs live camera feed using OpenCV Haar / Dlib / InsightFace lightweight embedding.
- Computes cosine similarity with calibrated threshold (e.g., 0.65).
- Displays confidence score alongside clear caveats: lighting, angle, and age variations.
- **Strict Privacy Rule**: Live capture is discarded immediately after comparison; only the mathematical similarity score is retained.

### Step 8: Explainable Risk Engine
- Deterministic, versioned rule engine (`VERISIGHT-RULES-v1.2`).
- Distinguishes **Critical Indicators** (e.g., MRZ check digit invalid, printed vs MRZ document number mismatch) from **Weak / Informational Indicators** (e.g., minor lighting imbalance, missing EXIF metadata).
- **No Correlated Double-Counting**: If poor image quality is detected, forensic texture noise flags are suppressed or down-weighted to prevent false accumulation.
- Outputs one of three states:
  - **CLEAR**: All check digits pass, visual-to-MRZ matches, no forensic anomalies, acceptable quality.
  - **REVIEW**: Single non-critical anomaly, expired document, or borderline quality requiring manual verification.
  - **HIGH RISK**: Multiple compounding flags, failed MRZ check digits, deliberate field contradiction, or severe ELA tamper signal.
- **Reviewer Override**: A Senior Reviewer or Administrator may override the algorithmic risk level by providing a mandatory written justification, securely recorded in `risk_assessments` and the audit log.

---

## 6. Cryptographic Audit Trail & Integrity Verification

To satisfy the SIH "Blockchain & Cybersecurity" mandate without deploying a bloated, slow blockchain node:
- VERISIGHT employs a **Cryptographically Verifiable Append-Only SHA-256 Hash Chain** (analogous to Git commit chains and Certificate Transparency logs).
- Every event computes:
  $$\text{Current Hash} = \text{SHA-256}(\text{Prev Hash} \parallel \text{ID} \parallel \text{Timestamp} \parallel \text{Event Type} \parallel \text{Actor ID} \parallel \text{Payload Hash})$$
- The API provides a public verification endpoint `GET /api/v1/audit/verify-integrity`:
  - Sequentially verifies every block in the database from block #1 to current.
  - Returns `{ "is_intact": true, "total_blocks": N, "last_verified_hash": "..." }` or pinpointed corruption metadata `{ "corrupted_at_id": X }`.
- Frontend provides an interactive **Audit Chain Verification Widget** with real-time status indication.

---

## 7. Institutional PDF Screening Report

The ReportLab engine compiles a professional 5-page forensic dossier:
- **Page 1: Executive Summary**: Reference number, screening date, officer details, risk badge (CLEAR / REVIEW / HIGH RISK), document thumbnail, primary extracted identity details.
- **Page 2: Extraction & MRZ Validation**: Complete side-by-side table of printed fields vs MRZ fields, ICAO check digit results, confidence scores.
- **Page 3: Forensic Laboratory Analysis**: High-resolution ELA difference heatmap, metadata findings, texture and alignment graphs, region-of-interest annotations.
- **Page 4: Audit Trail & Chain of Custody**: Cryptographic event sequence, SHA-256 evidence ingestion hash, timestamps, officer modifications.
- **Page 5: Statutory Disclaimers & Methodology**: Explicit legal disclaimer: "VERISIGHT is a triage decision-support tool. Findings must be corroborated by certified forensic examiners prior to legal action."

---

## 8. Role-Based Access Control (RBAC) Matrix

| Capability / Route | Screening Officer | Senior Reviewer | Administrator | Auditor |
| :--- | :---: | :---: | :---: | :---: |
| Dashboard & Live Metrics | Yes | Yes | Yes | Read-Only |
| Initiate Document Screening | Yes | Yes | Yes | No |
| View Extraction & Forensics | Yes | Yes | Yes | Read-Only |
| Correct OCR Field Value | Yes | Yes | Yes | No |
| Override Algorithmic Risk | No | Yes | Yes | No |
| Assign / Resolve Cases | Yes | Yes | Yes | No |
| Escalate Case | Yes | Yes | Yes | No |
| Export Forensic PDF Report | Yes | Yes | Yes | Yes |
| Inspect Audit Trail | No | No | Yes | Full Access |
| Verify Hash Chain Integrity | No | Yes | Yes | Yes |
| Manage Users & Roles | No | No | Yes | No |
| System Configuration & Rules | No | No | Yes | No |
| View Engine Status / Health | Yes | Yes | Yes | Yes |

---

## 9. Frontend Architecture: 18 Pages & 15 Components

### 18 Dedicated Pages:
1. `/login`: Secure officer authentication with liquid glass login card, demo credentials quick-picker, and legal warnings.
2. `/reset-password`: Self-service password recovery flow with email token simulation.
3. `/dashboard`: Command Center with real-time database KPIs, 5 Recharts visualizations, recent screening feed, and triage queue shortcuts.
4. `/screening/new`: Multi-step document upload with dropzone, camera capture, file validation, and supported template selection.
5. `/screening/:id/quality`: Image quality inspection screen (Laplacian blur, glare meters, resolution analysis, and rescan recommendation banner).
6. `/screening/:id/extraction`: Interactive OCR field inspection with clickable bounding boxes, confidence bars, and field correction modal.
7. `/screening/:id/mrz`: Dedicated MRZ analyzer displaying raw lines, parsed ICAO fields, 7-3-1 check digit indicators, and visual cross-checks.
8. `/screening/:id/forensics`: Forensic Laboratory featuring synchronized dual-viewport viewer, ELA difference slider, metadata table, and clickable findings.
9. `/screening/:id/face`: Consent-gated face verification studio comparing extracted portrait with live camera feed.
10. `/screening/:id/risk`: Explainable risk breakdown detailing rule contributions, critical vs weak signals, and reviewer override panel.
11. `/screening/:id/report`: In-browser PDF preview and instant download of the 5-page forensic report.
12. `/cases`: Investigation Center case queue with faceted filters (risk level, date range, document type, assigned officer, status).
13. `/cases/:id`: Detailed case investigation desk with evidence gallery, note taking, escalation controls, and resolution sign-off.
14. `/audit`: Cryptographic audit trail viewer with live SHA-256 chain verification button and integrity status badge.
15. `/admin/users`: User management portal for creating, editing, and deactivating accounts across all 4 RBAC roles.
16. `/admin/config`: System configuration console for calibrating risk rule weights, thresholds, and data retention rules.
17. `/admin/engine-status`: Processing engine diagnostic dashboard monitoring OpenCV, Tesseract, PaddleOCR, and database latencies.
18. `/404`: Security-themed Not Found page with quick navigation back to the Command Center.

### 15 Core Reusable Components:
1. `GlassPanel` / `GlassCard`: High-performance liquid glass container with SVG displacement refraction and specular rim lighting.
2. `GlassButton`: Tactile, refractive button with loading spinner, disabled states, and primary/secondary/destructive variants.
3. `GlassModal` / `GlassDialog`: Accessible dialog overlay with backdrop blur, focus trap, and keyboard dismissal.
4. `GlassSidebar`: Collapsible enterprise navigation bar with role-based route filtering and badge counters.
5. `GlassTopbar`: Header with breadcrumb trail, live system health pill, notifications dropdown, and user profile switcher.
6. `GlassInput` / `GlassSelect`: Themed form inputs with clear validation errors and technical helper text.
7. `ForensicImageViewer`: Synchronized dual-viewport canvas (original vs preprocessed/ELA) with zoom, pan, and bounding box overlays.
8. `RiskBadge`: High-contrast semantic badge for `CLEAR` (Green), `REVIEW` (Amber), and `HIGH RISK` (Red) with explanatory tooltips.
9. `MetricCard`: Command Center metric tile with trend indicator, sparkline chart, and synthetic data flag.
10. `FieldConfidenceBar`: Visual confidence meter for OCR fields with color-coded confidence tiers (>85% High, 60-85% Medium, <60% Low).
11. `CheckDigitIndicator`: Visual MRZ pill displaying valid checkmark or invalid alert with expected vs computed values.
12. `AuditChainValidator`: Interactive cryptographic widget displaying verification progress and proof of tamper-evidence.
13. `EvidenceViewerModal`: Modal dialog for inspecting raw vs preprocessed images and deep EXIF metadata.
14. `CaseActionBar`: Sticky triage action bar (Assign, Note, Request Rescan, Escalate, Resolve, Return).
15. `EmptyState` / `LoadingSkeleton`: Anti-slop technical empty states with clear recovery steps; animated dark glass skeletons.

---

## 10. Synthetic Demo Scenarios (5 Pre-Engineered Test Cases)

1. **`SCENARIO-1-CLEAN`**:
   - Identity: Amit Sharma, Indian Passport TD3.
   - All check digits valid, expiry in 2031, perfectly matching printed text, clean ELA, crisp resolution.
   - Expected Result: **CLEAR** (Score: 4/100).
2. **`SCENARIO-2-EXPIRED`**:
   - Identity: Elena Rostova, European Travel Doc TD3.
   - Valid check digits, matching printed text, but document expired in 2023.
   - Expected Result: **REVIEW** (Score: 42/100, Reason: "Document Expiry Date has elapsed").
3. **`SCENARIO-3-MRZ-MISMATCH`**:
   - Identity: David K. Chen.
   - Printed Date of Birth states "14 MAY 1988", but MRZ encodes "820514" (1982).
   - Expected Result: **HIGH RISK** (Score: 84/100, Reason: "Critical printed vs MRZ date of birth discrepancy").
4. **`SCENARIO-4-TAMPERED-ELA`**:
   - Identity: Marcus Vance, US Passport TD3.
   - Document number and photo box digitally altered via raster pasting; induces strong ELA compression variance and texture boundary discontinuity.
   - Expected Result: **HIGH RISK** (Score: 92/100, Reason: "Localized compression anomaly and texture discontinuity detected in portrait region").
5. **`SCENARIO-5-LOW-QUALITY`**:
   - Identity: Priya Patel.
   - Severe camera motion blur (Laplacian variance < 45) and bright flash glare over document number.
   - Expected Result: **REVIEW** (Score: 35/100, Quality: Unacceptable, Flag: "Rescan recommended due to optical glare and blur; inconclusive for forensic verification").

---

## 11. Acceptance Criteria & Section 23 Verification Matrix

| # | Verification Area | Target Standard / Test Metric |
| :--- | :--- | :--- |
| 1 | **Authentication & RBAC** | All 4 roles enforced; unauthorized requests return 401/403; JWT refresh functions cleanly. |
| 2 | **Command Center Live Data** | 100% metrics pulled from PostgreSQL; synthetic data badge displayed on seeded samples. |
| 3 | **Image Ingestion & Quality** | Magic byte validation; SHA-256 hash calculated at ingest; blur/glare scores accurately detected. |
| 4 | **Preprocessing** | Deskew and CLAHE normalize image without altering stored original file. |
| 5 | **OCR & Bounding Boxes** | Fields extracted with coordinates; clicking field highlights region; manual edit creates audit record. |
| 6 | **MRZ Parser** | 7-3-1 algorithm validates all check digits; printed vs MRZ mismatches explicitly marked. |
| 7 | **Forensic Lab & Heatmap** | ELA computes difference map; metadata highlights editing software; disclaimer clearly visible. |
| 8 | **Explainable Risk Engine** | Clear rule contributions; no double-counting of correlated signals; reviewer override requires note. |
| 9 | **Investigation Center** | Case queue filters operate dynamically; status transitions (Escalate, Resolve) persist to DB. |
| 10 | **Audit Trail Integrity** | Every change logged; SHA-256 chain verification passes; tampering detects corrupted block. |
| 11 | **PDF Generation** | 5-page institutional PDF generated with evidence hashes, ELA graphics, and legal disclaimers. |
| 12 | **Design System** | Liquid glass styling renders with fallbacks; WCAG AA contrast maintained; no AI slop. |
| 13 | **Automated Test Coverage** | Backend pytest suite passes (>85% coverage); frontend test suite verifies core user flows. |
| 14 | **Containerization** | `docker-compose up` launches all services with database migrations and seed scripts. |

