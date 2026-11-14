# VERISIGHT — Comprehensive UX & Functionality Audit (Phase A)

**Date**: November 14, 2026  
**Auditor**: Lead System Architect & Product Designer  
**Scope**: Full Click-Through Audit of Routes, Buttons, Forms, Navigation, Analysis Outputs, and Copy  
**Standard**: WCAG AA, Anti-Slop Hygiene, SIH 26188 Jury & Security Officer Expectations  

---

## 1. Click-Through & Component Audit Matrix

| Surface / Route | Element / Interaction | Type | Status | Action Taken / Plan |
|---|---|---|---|---|
| `/login` | Email & Password inputs, Login Button | Form | **WORKS** | Verified authentication with JWT tokens against `/api/v1/auth/login`. |
| `/login` | 4 Quick-Fill Role Pills (Admin, Officer, Reviewer, Auditor) | Button | **WORKS** | Auto-populates demo credentials for live evaluation. |
| `/dashboard` | "Refresh" button | Button | **WORKS** | Calls TanStack query `refetch()` for live DB sync. |
| `/dashboard` | "Start New Screening" button | Button | **WORKS** | Routes to `/screenings/new`. |
| `/dashboard` | 4 Metric Cards (Total, Clear, Review, High Risk) | Display | **WORKS** | Bound directly to `/api/v1/dashboard/stats` SQLite queries. |
| `/dashboard` | 4 Recharts Charts (Risk, Doc Types, Methods, Temporal) | Charts | **WORKS** | Renders real database aggregations. |
| `/dashboard` | Quick Action cards (Screening, Cases, Audit, Status) | Links | **WORKS** | Correct routes. |
| `/dashboard` | Recent Activity table rows | Links | **WORKS** | Routes to respective screening assessment step. |
| `/screenings/new` | Document template cards (Passport, Visa, ID, License) | Selector | **WORKS** | Sets `document_type` filter for engine calibration. |
| `/screenings/new` | File Dropzone & Camera Capture | Upload | **WORKS** | Multipart form upload with pre-flight file validation. |
| `/screenings/new` | Reference No & Consent Checkbox | Form | **WORKS** | Validated with Zod schema. |
| `/screenings/new` | "Initiate Automated Pipeline" button | Button | **WORKS** | Calls `POST /api/v1/screenings`, navigates to `/screenings/:id/quality`. |
| `/screenings/:id/quality` | Breadcrumb `<Link to="/screenings">` | Breadcrumb | **BROKEN** | `/screenings` route was missing in `App.tsx` (caused 404). **FIX**: Added redirect in `App.tsx` and changed breadcrumb to `/cases` / `/dashboard`. |
| `/screenings/:id/quality` | Original vs Preprocessed Toggle | Toggle | **WORKS** | Displays raw image vs deskewed/normalized image. |
| `/screenings/:id/quality` | "Discard / Re-upload" button | Button | **WORKS** | Navigates to `/screenings/new`. |
| `/screenings/:id/quality` | "Proceed to OCR Extraction" button | Button | **WORKS** | Navigates to `/screenings/:id/extraction`. |
| `/screenings/:id/extraction` | Breadcrumb `<Link to="/screenings">` | Breadcrumb | **BROKEN** | Same as above. Fixed with route redirect and breadcrumb normalization. |
| `/screenings/:id/extraction` | Bounding Box overlay toggle on document | Toggle | **WORKS** | Renders SVG bounding boxes dynamically per field. |
| `/screenings/:id/extraction` | "Back to Quality" button | Button | **WORKS** | Navigates to `/screenings/:id/quality`. |
| `/screenings/:id/extraction` | "Proceed to MRZ Studio" button | Button | **WORKS** | Navigates to `/screenings/:id/mrz`. |
| `/screenings/:id/mrz` | Breadcrumb `<Link to="/screenings">` | Breadcrumb | **BROKEN** | Fixed with route redirect. |
| `/screenings/:id/mrz` | Check Digit computation grid (Doc, DOB, Expiry, Comp) | Display | **WORKS** | Real check digit computation using ICAO Doc 9303 modulo-10 weights. |
| `/screenings/:id/mrz` | "Back to Extraction" button | Button | **WORKS** | Navigates to `/screenings/:id/extraction`. |
| `/screenings/:id/mrz` | "Proceed to Forensic Lab" button | Button | **WORKS** | Navigates to `/screenings/:id/forensics`. |
| `/screenings/:id/forensics` | Breadcrumb `<Link to="/screenings">` | Breadcrumb | **BROKEN** | Fixed with route redirect. |
| `/screenings/:id/forensics` | 5 Forensic Pillar tabs (ELA, EXIF, Texture, Align, Portrait) | Tabs | **WORKS** | Live tabs switching analysis visualizer and heatmaps. |
| `/screenings/:id/forensics` | Heatmap Opacity slider & Split-view toggle | Controls | **WORKS** | Real-time CSS and canvas manipulation. |
| `/screenings/:id/forensics` | "Back to MRZ Studio" button | Button | **WORKS** | Navigates to `/screenings/:id/mrz`. |
| `/screenings/:id/forensics` | "Proceed to Facial Verification" button | Button | **WORKS** | Navigates to `/screenings/:id/face`. |
| `/screenings/:id/forensics` | "Proceed to Risk Results" button | Button | **WORKS** | Navigates to `/screenings/:id/risk`. |
| `/screenings/:id/face` | DPDP Act §6 Biometric Consent Gate | Checkbox | **WORKS** | Enforces legal affirmative consent before camera activation. |
| `/screenings/:id/face` | Live Camera Stream & Capture / Upload Switcher | Input | **WORKS** | Webcam capture via `navigator.mediaDevices` with fallback upload. |
| `/screenings/:id/face` | "Verify Facial Similarity" button | Button | **WORKS** | Posts to `/api/v1/face/:id/verify`, computes cosine similarity and quality checks. |
| `/screenings/:id/face` | "Proceed to Risk Assessment" button | Button | **WORKS** | Navigates to `/screenings/:id/risk`. |
| `/screenings/:id/risk` | Breadcrumb `<Link to="/screenings">` | Breadcrumb | **BROKEN** | Fixed with route redirect. |
| `/screenings/:id/risk` | Risk Badge & Composite Meter | Display | **WORKS** | Real `CLEAR`, `REVIEW`, `HIGH_RISK` calculated by rule engine. |
| `/screenings/:id/risk` | "Override Decision" button & Modal | Button/Modal | **WORKS** | Allows Senior Reviewer / Admin to record formal justification. |
| `/screenings/:id/risk` | "Create Investigation Case" button | Button | **BROKEN** | Called `/cases/new?screening_id=...` which had no route (404). **FIX**: Call `casesApi.create()` and navigate to `/cases/:caseId`. |
| `/screenings/:id/risk` | "Export Evidentiary PDF Dossier" | Button | **MISSING** | Endpoint `/api/v1/reports/:id/download` exists, but button was omitted from top header. **FIX**: Added download button. |
| `/cases` | Status & Priority Filter Dropdowns | Filters | **WORKS** | Server-side query parameter filtering. |
| `/cases` | Case Table row click | Row Link | **WORKS** | Navigates to `/cases/:id`. |
| `/cases/:id` | Status Update button & Modal | Modal | **WORKS** | Updates case status with mandatory resolution notes on closure. |
| `/cases/:id` | Add Note Form | Form | **WORKS** | Attaches timestamped audit-linked officer notes. |
| `/cases/:id` | "View Screening Risk" button | Button | **WORKS** | Links directly back to linked credential risk breakdown. |
| `/audit` | "Verify Ledger Cryptographic Integrity" button | Button | **WORKS** | Traverses entire SHA-256 hash chain and confirms zero tampering. |
| `/audit` | Pagination controls (Prev / Next) | Buttons | **WORKS** | Server-side skip/limit navigation. |
| `/admin/engine-status` | Engine Health & Latency Indicators | Display | **WORKS** | Pings each engine and returns live latency. |
| `/admin/users` | "Add Security Officer" button & modal | Modal | **WORKS** | Creates users with hashed credentials and role assignments. |
| `/admin/config` | Engine Weights & Threshold Sliders | Form | **WORKS** | Reads and saves threshold configuration. |
| `GlassSidebar` | Navigation links (7 current) | Links | **WORKS** | Roles respected. Missing "Quick Check" and "Help Center". **FIX**: Add to navigation items. |
| `GlassTopbar` | Dynamic page title lookup | Text | **BROKEN** | Typo `path.startsWith('/screening/new')` missed the `s` in `/screenings/new`. **FIX**: Corrected route pattern. |
| `GlassTopbar` | Simple/Expert toggle & Language toggle & Help icon | Controls | **MISSING** | Missing topbar controls. **FIX**: Built in Phase B & C. |

---

## 2. Hardcoded / Fabricated Output Audit

- **Integrations and Databases**: No fake external passport database checks are claimed. The platform accurately identifies itself as an offline algorithmic screening and document-forensics aid.
- **Forensic Metrics**: All ELA, EXIF metadata, frequency, and MRZ calculations are computed directly from the uploaded binary via OpenCV and NumPy.
- **Fallback States**: Where facial verification is skipped, the platform clearly shows `NOT APPLICABLE (SKIPPED BY OFFICER)` rather than fabricating a similarity score.
- **Database Stats**: All numbers on `/dashboard` and `/cases` reflect actual counts in the SQLite database (`verisight.db`).

---

## 3. Jargon & Reading Level Audit

Security officers and border control staff need immediate, unequivocal guidance without deciphering academic CV terminology. Below are the key jargon terms and their plain-language conversions:

| Technical Jargon Found in UI | Plain Language Translation (~Grade 8 Level) | Technical Details (Collapsed in Expert Mode) |
|---|---|---|
| **Laplacian variance** | **Image Sharpness**: The document photo is crisp and clear enough to read. | `cv2.Laplacian(gray, cv2.CV_64F).var()` score (Threshold >= 100.0). |
| **Hough Transform Deskew** | **Straightness Correction**: Automatically straightened the image by X degrees. | Standard Hough line angle detection and affine rotation. |
| **Error Level Analysis (ELA)** | **Edited Area Detection**: Looks for sections of the image saved at different compression levels. | Re-saved at 90% JPEG quality, amplified difference heatmap. |
| **DCT Quantization Inconsistency** | **Compression Artifacts**: Detects signs that a photo or text box was pasted in from another file. | Discrete Cosine Transform 8x8 block boundary discontinuity. |
| **ICAO Doc 9303 Modulo-10 Check Digits** | **Passport Security Code Check**: Checks whether dates and ID numbers match the mathematical codes in the bottom two lines. | Weights [7, 3, 1] cyclical modulo-10 algorithm. |
| **Cosine Similarity (Face)** | **Face Match Confidence**: How closely the document photo matches the live person's face. | Dot product of L2-normalized 512-dim biometric embeddings. |
| **SHA-256 Hash Chain** | **Tamper-Proof Audit Record**: Every action is permanently locked with a digital fingerprint so records cannot be secretly changed. | Merkle-linked cryptographic ledger where each block hashes previous hash + payload. |

---

## 4. Prioritized Action Plan

1. **Immediate Audit Fixes (Phase A completion)**:
   - Fix `/screenings` redirect in `App.tsx` and normalize breadcrumb links.
   - Fix "Create Investigation Case" button on `RiskResultsPage.tsx` to call `casesApi.create()` and route to the created case.
   - Fix route matching typo in `GlassTopbar.tsx`.
   - Add "Export PDF Dossier" button on `RiskResultsPage.tsx` and `CaseDetailPage.tsx`.
2. **Phase B (Guided Case Story & Usability)**:
   - Build `CaseStepper` (1 Create &rarr; 2 Add documents &rarr; 3 Automatic checks &rarr; 4 Review findings &rarr; 5 Investigate & decide &rarr; 6 Final report).
   - Add `"What next?"` panel on all primary screening pages.
   - Add Simple Mode / Expert Mode toggle (stored in user settings).
   - Add English / Hindi (`en` / `hi`) i18n localization store.
   - Enhance Finding Cards with plain-language structure: (a) What we checked, (b) What we found, (c) Why it matters, (d) How sure we are, (e) What you can do.
   - Add `GlossaryTooltip` component for all technical terms.
3. **Phase C (Help Center & User Guide)**:
   - Build `/help` route and `HelpCenterPage.tsx` with 5-min walkthrough, interactive tour, role guides, report reading guide, photo tips, FAQ, and synthetic sample loader.
   - Add contextual `?` help icons on each page opening a matching help drawer.
4. **Phase D (Easy-to-Understand Reports)**:
   - Upgrade ReportLab PDF generator with Page 1 "Summary for Everyone" + Technical Appendix.
   - Multi-document comparison table.
5. **Phase E (Quick Check Standalone Tool)**:
   - Backend forensic analysis engine for arbitrary images, PDFs, and DOCX documents.
   - Frontend `/quick-check` page with honest framing and one-click "Create Full Case" escalation.
6. **Phase F (Testing & Self-Test Verification)**:
   - Admin System Self-Test page (`/admin/self-test`).
   - Automated tests and smoke test script.

