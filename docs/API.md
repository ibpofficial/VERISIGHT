# VERISIGHT REST API Reference Manual
## Version 1.0 // OpenAPI Specification 3.1.0 Compliant

---

## 1. Global Standards & Authentication

### 1.1 Base URL
All API v1 routes are mounted under:
```
http://127.0.0.1:8000/api/v1
```

### 1.2 Authentication Scheme
- **Mechanism**: Bearer JWT (Access Token in `Authorization` header).
- **Format**: `Authorization: Bearer <access_token>`
- **Token Query Support**: For binary stream endpoints (`/document`, `/heatmap`), authentication token may optionally be passed as `?token=<access_token>` to facilitate secure native browser `<img />` rendering.

### 1.3 Role-Based Access Control (RBAC) Matrix
| Endpoint / Resource | Admin | Senior Reviewer | Screening Officer | Auditor |
| :--- | :---: | :---: | :---: | :---: |
| `POST /screenings` (Intake) | Yes | Yes | Yes | No |
| `GET /screenings` (Browse) | Yes | Yes | Yes | Yes |
| `PATCH /screenings/.../fields` | Yes | Yes | Yes | No |
| `GET /forensics` & `/heatmap` | Yes | Yes | Yes | Yes |
| `POST /risk/.../override` | Yes | Yes | No | No |
| `PATCH /cases/.../status` | Yes | Yes | Yes | No |
| `GET /reports/.../download` | Yes | Yes | Yes | Yes |
| `GET /audit/verify-integrity` | Yes | Yes | No | Yes |
| `GET/PATCH /admin/...` | Yes | No | No | No |

---

## 2. Authentication & Session Endpoints (`/auth`)

### `POST /auth/login`
Authenticates officer credentials and returns access & refresh tokens.
- **Request Body**:
  ```json
  {
    "email": "officer@verisight.gov.in",
    "password": "Officer@12345"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "role": "SCREENING_OFFICER",
    "email": "officer@verisight.gov.in"
  }
  ```

### `POST /auth/refresh`
Exchanges a valid refresh token for a new access token.
- **Request Body**: `{"refresh_token": "..."}`
- **Response (200 OK)**: `{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}`

### `GET /auth/me`
Returns profile and badge information of the authenticated security officer.

---

## 3. Screening & Ingestion Endpoints (`/screenings`)

### `POST /screenings`
Ingests credential image, runs quality check, orientation deskew, OCR extraction, and MRZ verification.
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Image binary (JPEG or PNG, magic byte validated, up to 15MB).
  - `document_type`: `PASSPORT_TD3` | `ID_TD1` | `VISA_TD2`
  - `issuing_country_code`: 3-letter ISO code (e.g. `IND`)
  - `is_synthetic`: Boolean flag (true for evaluation demo scans)
  - `scenario_tag`: Optional demo label (`SCENARIO-1-CLEAN`, etc.)
- **Response (200 OK)**:
  ```json
  {
    "id": "e3b8a1c2-...",
    "reference_no": "VS-20261113-A8F2",
    "officer_id": "...",
    "document_type": "PASSPORT_TD3",
    "issuing_country_code": "IND",
    "status": "COMPLETED",
    "risk_level": "CLEAR",
    "risk_score": 12.0,
    "processing_time_ms": 1180,
    "is_synthetic": false,
    "created_at": "2026-11-13T06:30:00Z"
  }
  ```

### `GET /screenings/{id}/quality`
Returns the 7 optical quality metrics, detected orientation, and rescan directive.

### `GET /screenings/{id}/fields`
Returns all extracted VIZ fields with bounding box coordinates and validation states.

### `PATCH /screenings/{id}/fields/{field_id}`
Allows an officer to correct an OCR misread with mandatory justification note.
- **Request Body**:
  ```json
  {
    "new_value": "KUMAR",
    "notes": "Tesseract misread font character 0 as O in surname."
  }
  ```

### `GET /screenings/{id}/mrz`
Returns parsed ICAO 9303 line breakdown, 7-3-1 check digit booleans, and VIZ-vs-MRZ matches.

---

## 4. Digital Forensics Endpoints (`/forensics`)

### `GET /forensics/{screening_id}`
Executes or retrieves the 5-pillar forensic analysis findings:
1. Error Level Analysis (ELA)
2. Metadata & Software Provenance
3. Substrate Noise Texture Variance
4. Typographic Line Baseline Alignment
5. Portrait Boundary Discontinuity

### `GET /forensics/{screening_id}/heatmap`
Streams the JPEG Error Level Analysis heatmap rendered with the JET colormap.

---

## 5. Explainable Risk Engine Endpoints (`/risk`)

### `GET /risk/{screening_id}`
Returns deterministic risk score (0–100), risk tier (`CLEAR`, `REVIEW`, `HIGH_RISK`), engine version, and detailed list of triggered rules with weights.

### `POST /risk/{screening_id}/override`
Allows Senior Reviewer or Administrator to override risk level with mandatory justification note.
- **Request Body**:
  ```json
  {
    "override_level": "CLEAR",
    "reason": "Physical inspection verified genuine intaglio embossing and functional RFID chip; optical glare suppressed."
  }
  ```

---

## 6. Investigation Center Endpoints (`/cases`)

### `GET /cases`
Returns paginated cases filtered by `status` (`OPEN`, `IN_REVIEW`, `ESCALATED`, `RESOLVED`, `RETURNED`) or `priority`.

### `POST /cases`
Creates a formal investigation case linked to a screening record.

### `PATCH /cases/{id}/status`
Transitions case status and priority, appending resolution justification.

### `POST /cases/{id}/notes`
Affixes a dated officer note to the case dossier with immutable audit logging.

---

## 7. Institutional Reports & Audit Trail (`/reports`, `/audit`)

### `GET /reports/{screening_id}/download`
Compiles and streams the formal 5-page ReportLab PDF screening dossier (`Content-Disposition: attachment; filename="VERISIGHT_DOSSIER_...pdf"`).

### `GET /audit`
Returns paginated list of cryptographic audit chain blocks.

### `GET /audit/verify-integrity`
Traverses the sequential hash chain ($H_n = \text{SHA-256}(H_{n-1} \,\|\, ...)$) and certifies ledger integrity:
```json
{
  "is_intact": true,
  "total_blocks_verified": 42,
  "first_block_timestamp": "2026-11-13T06:00:00Z",
  "latest_block_timestamp": "2026-11-13T07:15:00Z",
  "latest_hash": "a4f8c92e...",
  "corrupted_at_id": null,
  "details": "All 42 cryptographic blocks verified intact. Zero chain breaks detected."
}
```

---

## 8. Command Center & Administration (`/dashboard`, `/admin`)

### `GET /dashboard/stats`
Returns aggregated live database KPIs, temporal volume, risk breakdown, and recent activity.

### `GET /admin/engine-status`
Returns real-time health telemetry for OpenCV, Tesseract OCR, MRZ parser, Forensics, ReportLab, and database connection.

### `GET /admin/config` & `PATCH /admin/config`
Reads and updates risk cutoffs (`high_risk_threshold`, `review_threshold`, `retention_days`).

---

## 8. Biometric Face Verification (Optional Step 7)

### `GET /face/{screening_id}/portrait`
Extracts and crops the normalized $128 \times 128$ photo from the ICAO TD3 passport photo window.
- **Roles**: All authenticated users.
- **Response**:
```json
{
  "screening_id": "uuid",
  "reference_no": "VS-20261113-XXXX",
  "portrait_b64": "data:image/jpeg;base64,...",
  "privacy_notice": "Ephemeral RAM retention notice...",
  "disclaimer": "Non-conclusive decision support notice..."
}
```

### `POST /face/{screening_id}/verify`
Executes ephemeral consent-gated facial cross-check comparing the document portrait with a live camera frame.
- **Roles**: `SCREENING_OFFICER`, `SENIOR_REVIEWER`, `ADMINISTRATOR`.
- **Form Data**:
  - `consent_granted`: `bool` (Mandatory; if `false`, returns `400 Bad Request`).
  - `live_image`: File (`image/jpeg` or `image/png`).
- **Response**:
```json
{
  "success": true,
  "similarity_score": 0.7863,
  "similarity_percentage": 78.6,
  "threshold": 0.65,
  "is_match": true,
  "confidence_band": "HIGH",
  "doc_quality": {
    "is_acceptable": true,
    "blur_score": 184.2,
    "mean_luminance": 132.5,
    "resolution": [128, 128],
    "flags": []
  },
  "live_quality": {
    "is_acceptable": true,
    "blur_score": 142.1,
    "mean_luminance": 128.0,
    "resolution": [200, 250],
    "flags": []
  },
  "caveats": [
    "Biometric algorithms are vulnerable to variations in pose, facial expression, and glasses/headwear.",
    "Document photo degradation, security printing watermarks, and laminate reflections reduce match fidelity.",
    "Age disparity between document issuance and present date may naturally reduce facial similarity."
  ],
  "disclaimer": "Non-conclusive probabilistic decision support metric.",
  "privacy_notice": "Biometric frames purged immediately from RAM in compliance with DPDP Act 2023."
}
```
- **Audit**: Writes cryptographic `FACE_VERIFICATION_PERFORMED` event (records only similarity score scalar; zero biometric vectors).

