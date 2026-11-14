# VERISIGHT — Phase 0 Reality Audit & Ground Truth Report
**Target System:** VERISIGHT (Automated Travel Identity Document Forensic Analysis & Ingestion Pipeline)  
**Smart India Hackathon 2026 | Problem Statement 26188 | Ministry of Home Affairs (MHA) - SSB Police II Division**  
**Audit Date:** November 14, 2026  
**Status:** PHASE 0 COMPLETE — READY FOR PHASE 1 REMOVAL OF FABRICATIONS

---

## 1. Executive Summary

VERISIGHT was created to serve front-line border checkpoint officers, screening analysts, and forensic investigators under the Ministry of Home Affairs. However, an in-depth forensic codebase audit revealed critical vulnerabilities, fabricated outputs, and mock algorithms masquerading as production analytics.

The mandate is **REALITY-FIRST HARDENING**:
> *Every result shown anywhere in the product must come from real computation on the user's actual file, and every failure must be visible, transparent, and honest.*

This document catalogs every fabricated output, insecure shortcut, and simulated metric across the repository, validates the existing test baseline, and establishes a master 35-fixture Golden Test Set for precision and recall calibration.

---

## 2. Existing Test Baseline Execution

The existing test suite was executed against the local Python 3.11 environment:
- **Total Tests:** 41 items across 9 test modules
- **Passed:** 41
- **Failed:** 0
- **Execution Time:** ~26 seconds

### Test Breakdown by Module:
1. `backend/tests/test_risk.py` (4 tests) — **PASSED** (Rule engine, checksum penalties, quality weights, supervisor override RBAC)
2. `backend/tests/test_quick_check.py` (4 tests) — **PASSED** (Quick check triage, PDF incremental updates, DOCX tracked changes, escalation to case)
3. `backend/tests/test_forensics.py` (6 tests) — **PASSED** (ELA, metadata exif/hex, texture LBP, baseline alignment, portrait border gradient, forensics API)
4. `backend/tests/test_auth.py` (7 tests) — **PASSED** (Health check, JWT login, invalid credentials, refresh token, `/me`, RBAC roles, password reset)
5. `backend/tests/test_cases.py` (2 tests) — **PASSED** (Case creation, investigator notes, lifecycle transitions)
6. `backend/tests/test_edge_cases_and_security.py` (6 tests) — **PASSED** (MIME/magic bytes, corrupted payloads, RBAC denials, signature tamper, 404 handling, input sanitation)
7. `backend/tests/test_face_verification.py` (4 tests) — **PASSED** (Optical quality, HOG descriptor similarity, DPDP consent rejection, `/verify` endpoint)
8. `backend/tests/test_processing.py` (5 tests) — **PASSED** (Modulo-10 check digits, TD3 MRZ parsing, preprocessing CLAHE/deskew, intake upload, magic bytes)
9. `backend/tests/test_audit_and_reports.py` (2 tests) — **PASSED** (SHA-256 Merkle block hashing, ReportLab PDF generation)
10. `backend/tests/test_e2e_workflow.py` (1 test) — **PASSED** (Full officer intake -> quality -> OCR -> forensics -> risk scoring -> PDF export)

> **Audit Observation:** Although 41/41 tests pass, several tests pass **only because** the underlying engine fabricates a fallback or because assertions accept simulated outputs (e.g. `test_face_verification` asserting that HOG + color histograms produce similarity percentage, and `test_processing` expecting fallback extraction).

---

## 3. System Inventory & Page-by-Page / Route Classification

| Page / Route | Path / Endpoint | Classification | Root Cause & Reality Assessment |
| :--- | :--- | :--- | :--- |
| **Authentication** | `/login`, `/reset-password` | **WORKS** | Real Argon2 password hashing and JWT issuance. |
| **Dashboard** | `/dashboard` | **WORKS** | Dynamic aggregation queries against SQLite/PostgreSQL `screenings` and `cases`. |
| **Document Intake** | `/screenings/new` | **BROKEN / FAKE** | Synchronous backend call blocks client; frontend uses artificial progress ticker; OCR engine fabricates identity fields if unreadable. |
| **Quality Assessment** | `/screenings/:id/quality` | **WORKS** | Real Laplacian variance (blur), pixel saturation (glare), and brightness metrics. Formula clamping requires calibration. |
| **Visual OCR & MRZ** | `/screenings/:id/ocr` | **FAKE** | `tesseract_engine.py` injects hardcoded sample passport ("SHARMA / AMIT") and defaults confidences to 0.88–0.95 when characters are missing. `paddle_engine.py` never executes. |
| **Forensic Analysis** | `/screenings/:id/forensics` | **PARTIALLY REAL / FAKE** | ELA, metadata, and texture run real OpenCV math, but portrait extraction assumes fixed percentage crop (5% to 35% width, 18% to 55% height) when no face is found. |
| **Facial Biometrics** | `/screenings/:id/face` | **FAKE** | Uses HOG gradient histograms and YCrCb color channels on fixed crop. This is template color-matching, NOT deep face verification. |
| **Risk Scoring** | `/screenings/:id/risk` | **WORKS** | Real deterministic rule evaluation engine with weighted penalties and supervisor override. |
| **Case Investigation** | `/cases`, `/cases/:id` | **WORKS** | Real CRUD persistence, priority filters, note timelines, and status transitions. Lacks object-level tenant authorization. |
| **Audit Ledger** | `/audit` | **BROKEN** | Six separate call-sites read the last row and write without DB transactions or row locks; concurrent requests fork the hash chain. |
| **Quick Check Triage** | `/quick-check` | **WORKS** | Real PDF incremental revision parser and DOCX XML tag inspector. |
| **Health Check** | `/api/v1/health` | **FAKE** | Hardcodes `"database": "CONNECTED"` without executing a real `SELECT 1` ping. |

---

## 4. Codebase Audit of Fabricated Output & Known Defects

### 4.1 Fabricated OCR Identity & Default Confidences (Defect #1)
- **Location:** `backend/app/engines/ocr/tesseract_engine.py:42-53`
  - Injects full fake identity when Tesseract throws an exception or binary is missing:
    ```python
    "Surname: SHARMA\nGiven Names: AMIT\nDate of Birth: 14/05/1988\nDoc No: A12345678\n"
    "P<UTOSHARMA<<AMIT<<<<<<<<<<<<<<<<<<<<<<<<<<<\nA123456784UTO8805142M3108217<<<<<<<<<<<<<<0"
    ```
- **Location:** `backend/app/engines/ocr/tesseract_engine.py:106-107, 151`
  - Hardcodes `surname_val = "SHARMA"`, `given_val = "AMIT"`, `dob_val = "14/05/1988"` when anchors are not matched.
- **Location:** `backend/app/engines/ocr/tesseract_engine.py:117-175`
  - Injects fabricated confidence literals: `0.92`, `0.90`, `0.95`, `0.88`, `0.91` and static bounding box coordinates `{"x": 120, "y": 80, "width": 200, "height": 30}`.
- **Location:** `backend/app/api/v1/screenings.py:156`
  - Flags every field as `ValidationStatus.VALID` regardless of OCR confidence or checks.

### 4.2 PaddleOCR Engine Bypass (Defect #2)
- **Location:** `backend/app/engines/ocr/paddle_engine.py:37-42`
  - Always returns `self._fallback_engine.extract(image_path)` even when PaddleOCR is instantiated.
  - `paddleocr` missing from backend dependencies and Dockerfile.
- **Location:** `backend/app/api/v1/screenings.py:143`
  - Directly instantiates `TesseractOCREngine()`, completely bypassing engine selection and registry.

### 4.3 Fake Facial Biometrics via HOG + Color Histograms (Defect #3)
- **Location:** `backend/app/engines/face/verifier.py:22-44`
  - Crops fixed coordinates (`x: 0.04..0.42, y: 0.16..0.76`) as the "document portrait".
- **Location:** `backend/app/engines/face/verifier.py:87-135`
  - Computes 4x4 spatial HOG + YCrCb color histograms and labels the cosine distance "Biometric Facial Similarity".

### 4.4 False Encryption Claim (Defect #4)
- **Location:** `backend/app/api/v1/screenings.py:102`
  - Sets `is_encrypted=True` on `Document` model while line 79 writes plaintext bytes directly to `settings.UPLOAD_DIR`. Zero encryption is applied.

### 4.5 Synchronous Blocking Intake (Defect #5)
- **Location:** `backend/app/api/v1/screenings.py:56-200`
  - Entire pipeline (hashing, quality assessment, deskew, OCR, MRZ, audit block) runs synchronously in `POST /screenings`. No background worker or queue.

### 4.6 Concurrency Failure in Audit Hash Chain (Defect #6)
- **Location:** `backend/app/core/audit_chain.py:38-55`, `screenings.py:195`, `cases.py:92`, `face.py:105`, `forensics.py:112`, `reports.py:84`, `risk.py:130`, `admin.py:88`
  - Each call site independently queries `SELECT * FROM audit_events ORDER BY id DESC LIMIT 1` then inserts. Concurrent requests produce divergent hash forks.

### 4.7 Security & Authorization Deficiencies (Defect #7)
- **Location:** `backend/app/main.py:46`
  - `allow_origins=["*"]` configured alongside `allow_credentials=True`.
- **Location:** `backend/app/api/deps.py:48`
  - Accepts JWT from `?token=` query parameter, causing sensitive tokens to leak into web server logs and browser histories.
- **Location:** `backend/app/api/v1/screenings.py:215`, `cases.py:55`
  - Missing tenant and object-level authorization checks. Any authenticated officer can view/modify any screening dossier.

### 4.8 Tracked Ephemeral and Sensitive Data (Defect #8)
- **Location:** Repository root
  - `verisight.db`, `test.db`, `data/uploads/*`, and Python `__pycache__` binaries were tracked by Git. *(Remediated via `.gitignore` update and `git rm --cached`).*

### 4.9 Uncalibrated Forensics & Fixed Heuristics (Defect #9)
- **Location:** `backend/app/engines/forensics/portrait.py:48-54`
  - Injects fixed box (`x: 0.05, y: 0.18, w: 0.35, h: 0.55`) if Haar cascade finds no face.
- **Location:** `backend/app/engines/quality.py:73-74`
  - Clamps readability to `max(0.05, min(0.99, readability))` using arbitrary linear combination weights.

---

## 5. Golden Test Set Specification (35 Synthetic Fixtures)

Generated programmatically via `scripts/generate_golden_test_set.py` using OpenCV, PIL, and ICAO 9303 standard layout geometry. All identities are 100% synthetic:

| Fixture ID | Category | Distortions / Characteristics | Expected Pipeline Behavior |
| :--- | :--- | :--- | :--- |
| `sample_01_clean_td3_ind.jpg` | Passport (TD3) | High contrast, pristine IND passport, valid check digits | 100% extraction, VALID MRZ, high confidence |
| `sample_02_clean_td3_gbr.jpg` | Passport (TD3) | Pristine GBR passport, valid check digits | 100% extraction, VALID MRZ |
| `sample_03_clean_td3_usa.jpg` | Passport (TD3) | Pristine USA passport, valid check digits | 100% extraction, VALID MRZ |
| `sample_04_clean_td1_fra.jpg` | ID Card (TD1) | 3-line TD1 identity card layout (FRA) | TD1 MRZ detection, 3-line parsing |
| `sample_05_clean_td2_can.jpg` | ID Card (TD2) | 2-line TD2 official travel credential (CAN) | TD2 MRZ detection, 2-line parsing |
| `sample_06_rotated_90deg.jpg` | Geometry | Clockwise 90° orientation | Auto-orientation detection + deskew |
| `sample_07_rotated_180deg.jpg` | Geometry | Inverted 180° upside-down orientation | Auto-orientation detection + flip |
| `sample_08_rotated_270deg.jpg` | Geometry | Counter-clockwise 270° orientation | Auto-orientation detection + rotation |
| `sample_09_skewed_5deg.jpg` | Geometry | 5° affine rotational slant | Radon/Hough deskew recovery |
| `sample_10_skewed_15deg.jpg` | Geometry | 15° aggressive skew | Perspective boundary deskew |
| `sample_11_perspective_trapezoid.jpg`| Geometry | Keystone trapezoidal camera angle (3D perspective) | 4-point contour perspective warp rectification |
| `sample_12_low_light.jpg` | Environmental | Mean luminance < 45 (severe underexposure) | Flagged UNDEREXPOSURE, CLAHE contrast retry |
| `sample_13_specular_glare.jpg` | Environmental | Saturated hotspot flash (>6% pixels @ 255) | Flagged SURFACE_GLARE, unreadable region mapped |
| `sample_14_gaussian_blur.jpg` | Quality Defect | Gaussian blur radius 11 (Laplacian var < 40) | Flagged OPTICAL_BLUR, rescan recommended |
| `sample_15_motion_blur.jpg` | Quality Defect | Directional horizontal smear kernel 15px | Flagged MOTION_BLUR, rescan recommended |
| `sample_16_cropped_missing_mrz.jpg`| Crop Defect | Lower 35% clipped (MRZ completely absent) | MRZ_NOT_FOUND, VIZ partial extraction only |
| `sample_17_corner_crop.jpg` | Crop Defect | Document corner clipped, missing country code | Border integrity violation flagged |
| `sample_18_jpeg_recompressed_q20.jpg`| Compression | Heavy JPEG block artifacts (Quality=20) | Forensics ELA compression anomaly flagged |
| `sample_19_multicycle_resize.jpg`| Compression | 3-cycle downscale/upscale blur | High-frequency loss detected |
| `sample_20_desktop_screenshot.png`| Presentation | Monochromatic digital screenshot rendering | No camera EXIF, digital raster flagged |
| `sample_21_non_mrz_driving_license.jpg`| Non-MRZ | Driving license template (No MRZ band) | Layout-anchored VIZ extraction, MRZ skipped |
| `sample_22_non_mrz_badge.jpg` | Non-MRZ | Corporate access security credential | Unsupported template, unanchored raw text |
| `sample_23_random_photo_nature.jpg` | Non-Document | Scenic forest photography | NO identity fields, NON_DOCUMENT rejection |
| `sample_24_random_photo_abstract.jpg`| Non-Document | Multicolored geometric shapes | NO identity fields, NON_DOCUMENT rejection |
| `sample_25_blank_white.png` | Degenerate | 100% pure white pixels | EMPTY_IMAGE rejection, 0 fields |
| `sample_26_blank_black.png` | Degenerate | 100% pure black pixels | EMPTY_IMAGE rejection, 0 fields |
| `sample_27_blank_noise.png` | Degenerate | Uniform Gaussian random noise | HIGH_ENTROPY rejection, 0 fields |
| `sample_28_text_only_code.png` | Non-Credential | Python source code screenshot | NON_DOCUMENT rejection, 0 fields |
| `sample_29_text_only_article.jpg` | Non-Credential | Standard book prose paragraph | NON_DOCUMENT rejection, 0 fields |
| `sample_30_tampered_dob_checksum_td3.jpg`| Fraud Tamper | Manipulated DOB digit with invalid check digit | CHECKSUM_FAILURE on DOB field |
| `sample_31_tampered_docnum_checksum_td3.jpg`| Fraud Tamper | Manipulated document number check digit | CHECKSUM_FAILURE on Doc No |
| `sample_32_spliced_portrait_tampered_td3.jpg`| Fraud Tamper | Spliced foreign photo with high ELA border gradient | PORTRAIT_SPLICE_DETECTED, HIGH ELA anomaly |
| `sample_33_corrupted_truncated.jpg` | Corrupted | Truncated JPEG stream (broken headers) | HTTP 400 Bad Request, graceful failure message |
| `sample_34_empty_0bytes.jpg` | Corrupted | Zero byte empty file | HTTP 400 Empty Payload rejected |
| `sample_35_mismatch_viz_vs_mrz_td3.jpg`| Fraud Tamper | Printed name "RAJESH PATEL", MRZ name "KUMAR" | VIZ_MRZ_MISMATCH alert raised |

---

## 6. Action Plan for Phase 1 (Remove Every Fake)

1. **Delete All Fallback Fabrication:**
   - Remove "SHARMA / AMIT / 14/05/1988 / A12345678" and default bounding boxes from `backend/app/engines/ocr/tesseract_engine.py`.
   - When OCR produces no text or confidence fails, persist `value=None, status=FieldValidationStatus.MISSING, confidence=None, bounding_box=None`.
2. **Compute Real Field Validation Statuses:**
   - Enforce discrete computed statuses: `VALID`, `INVALID_FORMAT`, `LOW_CONFIDENCE`, `MISSING`, `UNREADABLE`, `CORRECTED`.
3. **Split Health Check:**
   - Implement true `/api/v1/health/live` and `/api/v1/health/ready` that verify database connection, upload storage writability, and OCR engines.
4. **Anti-Simulation CI Guard:**
   - Add automated test asserting that blank, random, and text-only images generate 0 identity fields, and scanning for forbidden mock strings in non-test source.
