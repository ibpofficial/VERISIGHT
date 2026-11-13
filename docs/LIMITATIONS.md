# VERISIGHT System Limitations, Evidentiary Boundaries & Ethical Commitments
## Smart India Hackathon 2026 // Problem Statement 26188 (MHA - SSB)

---

## 1. Technical & Algorithmic Boundaries

### 1.1 Error Level Analysis (ELA) Limitations
- **Indicative Clue, Not Proof of Forgery**: Error Level Analysis identifies differences in compression error rates across 8x8 DCT macroblocks when re-saved at JPEG quality 95. High variance naturally occurs along high-contrast physical edges, printed security guilloche patterns, holographic overlays, and camera focus boundaries. ELA results must always be corroborated with physical tactile examination and cryptographic MRZ verification.
- **Multiple Save Cycles**: An authentic image that has been legitimately forwarded or resized across multiple messaging gateways may show complex multi-generation compression artifacts that can mimic or obscure localized digital splicing.

### 1.2 Metadata & EXIF Limitations
- **Stripped Metadata**: Legitimate web upload forms, privacy-focused mobile browsers, and chat applications (e.g. WhatsApp, Telegram) intentionally strip EXIF metadata to protect user privacy. Stripped metadata is an expected industry reality and is treated as `INFORMATIONAL`, not as evidence of fraud.
- **Header Forgery**: Basic command-line utilities (`exiftool`) can forge or remove metadata tags. Metadata findings serve as supplemental provenance clues.

### 1.3 Substrate & Typographic Limitations
- **Optical Lens Distortion**: Smartphone wide-angle lenses introduce radial (barrel) and tangential distortion that can cause slight baseline curvature in genuine documents. VERISIGHT’s preprocessing pipeline applies Hough line deskewing, but physical page curvature in creased travel booklets requires manual examiner confirmation.
- **Physical Wear & Tear**: Creased folds, physical ink smudges, and moisture damage can degrade character recognition confidence. Under VERISIGHT’s design philosophy, sub-optimal optical quality triggers a `REVIEW` / Rescan recommendation and is never conflated with deliberate counterfeit tampering.

---

## 2. Institutional & Sovereign Database Disclaimers

### 2.1 No Sovereign Database Integration Claims
- VERISIGHT is an independent, client-side/edge document screening and forensic analysis platform. It does NOT claim real-time direct integration into sovereign government databases (such as Ministry of External Affairs Passport Seva Kendra, UIDAI Aadhaar CIDR, or Interpol Stolen and Lost Travel Documents SLTD database) without official bilateral agency API authorization and secure government gateways.
- Validation of document numbers is conducted deterministically via mathematical ICAO Document 9303 checksums, VIZ-to-MRZ syntactic consistency cross-checks, and internal institutional watchlists.

### 2.2 Decision-Support Mandate
- In accordance with institutional border control jurisprudence, VERISIGHT provides **automated decision-support telemetry**. The software never autonomously denies border entry, revokes citizenship, or accuses travelers of felony forgery. The sovereign final clearance determination resides exclusively with the authorized security officer or magistrate.

---

## 3. Privacy, Data Protection & Biometric Guarantees

1. **Zero Permanent Biometric Storage**: The platform does not store biometric facial embeddings, vector indexes, or live webcam streams in permanent persistent databases.
2. **PII Sanitization in Audit Ledger**: Raw government identity numbers and biometric facial portraits are never printed into plain-text system logs or terminal streams. Audit chain entries record SHA-256 digests and structured cryptographic metadata only.
3. **Synthetic Demonstration Data**: All demonstration and jury evaluation credentials utilize fabricated, synthetic identities and dummy numbers adhering to privacy protection guidelines.
4. **Data Retention Controls**: Administrators can configure automated cache purge schedules (default 180 days) for evidentiary document images while permanently maintaining the immutable SHA-256 audit chain.

