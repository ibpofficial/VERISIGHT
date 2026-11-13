# VERISIGHT — Execution Checklist & Acceptance Tracking
## SIH 2026 Problem Statement 26188: AI-Based Fake Identity & Document Screening System

---

## Master Scope Checklist

- [x] **1. Authentication & RBAC**
  - [x] JWT Access + Refresh token architecture
  - [x] Secure password hashing (bcrypt / passlib)
  - [x] Password reset simulation flow
  - [x] Backend-enforced RBAC: Administrator, Screening Officer, Senior Reviewer, Auditor
  - [x] Login activity audit logging (IP, user agent, success/failure)
  - [x] Role-restricted frontend navigation and action gates

- [x] **2. Command Center (Dashboard)**
  - [x] Real-time database metrics (Total screenings, Today's screenings, CLEAR / REVIEW / HIGH RISK counts)
  - [x] Average processing time calculation
  - [x] 5 interactive Recharts visualizations (Risk distribution, Temporal volume, Document types, Detection methods, Processing latency)
  - [x] Recent screening activity feed with direct deep-links
  - [x] Quick action shortcuts (New Screening, Active Queue, Audit Log)
  - [x] Clear visual distinction for synthetic/seeded data

- [x] **3. Document Ingestion & Quality Preprocessing Pipeline**
  - [x] Document type selector with explicit supported templates (ICAO TD1, TD2, TD3 Passport, Visas)
  - [x] Multi-channel upload: Drag-and-drop dropzone, file browser, live webcam capture
  - [x] Magic byte file validation (JPEG, PNG, safe PDF) with 15MB size limit
  - [x] Immediate SHA-256 evidence hashing at ingest
  - [x] Image Quality Assessment engine:
    - [x] Modified Laplacian blur scoring
    - [x] Glare / saturation ratio calculation
    - [x] Brightness / luminance check
    - [x] Resolution DPI estimation
    - [x] Orientation detection (0°, 90°, 180°, 270°)
    - [x] Boundary crop detection
    - [x] Overall readability score & Rescan recommendation flag (poor quality ≠ fraud)
  - [x] Image Preprocessing:
    - [x] Affine rotation and deskew
    - [x] Homography perspective rectification
    - [x] CLAHE contrast normalization
    - [x] Denoising (bilateral filter)
    - [x] Preservation of original unedited image file

- [x] **4. OCR Extraction & Interactive Field Mapping**
  - [x] Pluggable OCR Engine interface (PaddleOCR with CPU mode + Tesseract fallback)
  - [x] Standard field extraction: Document Number, Issuing State, Surname, Given Names, Nationality, DOB, Sex, Expiry Date, MRZ lines
  - [x] Normalized bounding box coordinates for each extracted field
  - [x] Interactive UI: clicking field highlights bounding box on canvas; hovering box highlights field
  - [x] Reviewer field correction: edits saved to `current_value`, preserving `original_value` with immutable audit log

- [x] **5. MRZ Verification Engine**
  - [x] Complete ICAO Document 9303 parser for TD1, TD2, and TD3 formats
  - [x] Check digit verification using 7-3-1 weight algorithm:
    - [x] Document number check digit
    - [x] Date of birth check digit
    - [x] Expiry date check digit
    - [x] Optional data check digit
    - [x] Final composite check digit
  - [x] Visual printed text vs MRZ decoded cross-field comparison
  - [x] Discrepancy flagging and visual status indicators

- [x] **6. Multi-Factor Forensic Laboratory**
  - [x] Synchronized dual-viewport viewer (Original vs Preprocessed / ELA) with zoom, pan, and region select
  - [x] Error Level Analysis (ELA) with normalized difference heatmap
  - [x] Prominent non-conclusive ELA disclaimer
  - [x] Deep EXIF & software metadata inspector (Photoshop, Canva, GIMP tag detection)
  - [x] Local Binary Pattern (LBP) texture anomaly detection
  - [x] Text alignment, font pitch, and baseline linearity verification
  - [x] Portrait region edge discontinuity and tamper analysis
  - [x] Structured forensic findings list (Name, method, severity, region, explanation, technical result, limitations, recommendation)
  - [x] Clickable heatmap navigating to region of interest
  - [x] Explicit "NOT AVAILABLE" indicator when an analysis method cannot run

- [x] **7. Optional Biometric Face Verification**
  - [x] Strict consent gate requiring explicit subject permission under Section 6 of DPDP Act 2023
  - [x] Document portrait extraction vs live webcam capture or photo upload
  - [x] Face quality, lighting, blur, and resolution assessment
  - [x] Cosine similarity scoring with calibrated threshold (0.65)
  - [x] Zero permanent storage of biometric face embeddings or live photos in RAM/disk/DB

- [x] **8. Explainable Risk Engine**
  - [x] Deterministic, configurable, versioned rule engine (`VERISIGHT-RULES-v1.2`)
  - [x] Clear status classification: CLEAR / REVIEW / HIGH RISK
  - [x] Weighted separation of Critical vs Weak indicators
  - [x] Protection against double-counting correlated signals (e.g. poor quality suppressing false texture alarms)
  - [x] Detailed rule contribution breakdown for every screening
  - [x] Senior Reviewer / Administrator manual risk override with mandatory justification note

- [x] **9. Investigation Center (Cases)**
  - [x] Centralized case queue with faceted filtering (Risk, Date range, Document type, Officer, Status)
  - [x] Detailed case investigation desk with full evidence timeline
  - [x] Triage actions: Assign, Add Note, Request Rescreen, Escalate, Resolve, Return
  - [x] Resolution justification tracking and audit trail attachment

- [x] **10. Tamper-Evident Cryptographic Audit Trail**
  - [x] SHA-256 hash-chained immutable audit log
  - [x] Live verification endpoint (`/api/v1/audit/verify-integrity`)
  - [x] Interactive UI Audit Chain Validator with visual integrity seal and block inspector
  - [x] Comprehensive event tracking across all system actions

- [x] **11. Institutional PDF Screening Report**
  - [x] 5-page structured ReportLab dossier
  - [x] SHA-256 evidence hash and cryptographic audit references
  - [x] High-resolution ELA difference heatmap embed
  - [x] Complete MRZ and OCR extraction side-by-side table
  - [x] Statutory legal disclaimers and non-conclusive evidentiary notice

- [x] **12. Administration & Engine Health**
  - [x] User management (Create, edit, deactivate, assign RBAC roles)
  - [x] Risk rule threshold calibration and retention policy configuration
  - [x] Processing Engine Status dashboard (OpenCV, Tesseract, PaddleOCR, DB latency)

- [x] **13. Database Layer**
  - [x] All 11 PostgreSQL / SQLite tables created with foreign keys, constraints, and indexes
  - [x] Async & sync SQLAlchemy models and session handling with SQLite WAL pragma
  - [x] Database seeding script for 4 standard demo roles

- [x] **14. REST API**
  - [x] Full OpenAPI documentation at `/docs` and `/redoc`
  - [x] Standardized JSON response envelope and error schemas
  - [x] Background job dispatch with status polling

- [x] **15. Frontend Architecture & Light Liquid Glass System**
  - [x] All 18 pages implemented
  - [x] All 15 reusable components built
  - [x] Anti-slop enterprise design with Light Liquid Glass theme (`#F8FAFC`, `#FFFFFF`, Blue 600, Slate 900)
  - [x] Responsive layouts, glass loading skeletons, empty states, 404 page

- [x] **16. Synthetic Demo Dataset**
  - [x] Automated generation script for 5 synthetic passport scenarios (Clean, Expired, MRZ Mismatch, ELA Tampered, Low Quality)
  - [x] Database seeding script for demo user accounts and historical screening data

- [x] **17. Automated Testing Suite**
  - [x] Backend pytest suite (37 passed across 9 suites: Auth, RBAC, Upload, Quality, OCR, MRZ, Forensics, Face, Risk, Cases, Audit, PDF, E2E, Edge Cases & Security)
  - [x] Frontend test and production build (`tsc -b && vite build` built with 0 errors)
  - [x] End-to-end integration workflow test (Ingest to PDF & Audit verification)
  - [x] Edge cases: Corrupted file, invalid format, unauthorized access, SQLi/XSS sanitization

- [x] **18. Documentation & Deployment**
  - [x] `README.md` with complete setup instructions
  - [x] `docs/ARCHITECTURE.md`
  - [x] `docs/API.md`
  - [x] `docs/RISK_RULES.md`
  - [x] `docs/LIMITATIONS.md`
  - [x] `docs/DESIGN_SYSTEM.md`
  - [x] `docs/DEMO_SCRIPT.md` (Jury presentation guide)
  - [x] `docs/JURY_QA.md`
  - [x] `docker-compose.yml` orchestrating Frontend, Backend, PostgreSQL, and Worker
