# VERISIGHT — Design System Specification
## Liquid Glass Architecture & Enterprise Security Interface

---

## 1. Executive Aesthetic Strategy

VERISIGHT is built for high-stakes law enforcement, border control, and forensic document analysis. Its interface must communicate **precision, technical authority, and operational calm**. 

Instead of generic "AI saas" tropes (purple glow gradients, low-contrast floating text, emoji icons, oversized rounded bubbles), VERISIGHT utilizes a **Dark Liquid Glass Architectural System** designed specifically for:
- Maximum legibility of dense tabular OCR, MRZ, and cryptographic data.
- Clear structural hierarchy between permanent navigation controls and forensic workspaces.
- Seamless accessibility across different lighting conditions and hardware capabilities.

---

## 2. Liquid Glass Reference Analysis (`docs/references/vue-web-liquid-glass`)

### 2.1 Optical & Mathematical Mechanics
The reference implementation (`vue-web-liquid-glass`) achieves realistic physical refraction through an SVG displacement filter pipeline:
1. **Snell's Law Ray Tracing**:
   $$\eta = \frac{1}{\text{refractiveIndex}} = \frac{1}{1.5} \approx 0.667$$
   For each surface normal vector $\mathbf{N} = (N_x, N_y)$ along the curved bezel of the glass:
   $$k = 1 - \eta^2 (1 - (\mathbf{N} \cdot \mathbf{I})^2)$$
   When $k \ge 0$, the refracted ray direction is computed, projecting displacement along the remaining thickness of the glass.
2. **Displacement Buffer Generation**:
   A 2D `ImageData` map is generated where pixel red/green channels encode normalized $X$ and $Y$ optical displacements ($0x80 = \text{neutral}$, $>0x80 = \text{positive}$, $<0x80 = \text{negative}$).
3. **Specular Lighting & Rim Highlights**:
   A specular intensity buffer maps surface highlights along an incident light angle ($\theta = \pi/3$), anti-aliasing the outer perimeter and bezel edge.
4. **SVG Filter Composition**:
   ```xml
   <svg class="liquid-glass-filters">
     <filter id="glass-filter-{id}" x="-20%" y="-20%" width="140%" height="140%">
       <feImage href="{displacementMapDataUrl}" result="displacement" />
       <feDisplacementMap in="SourceGraphic" in2="displacement" scale="{maxDisplacement}" xChannelSelector="R" yChannelSelector="G" result="refracted" />
       <feImage href="{specularMapDataUrl}" result="specular" />
       <feBlend in="refracted" in2="specular" mode="screen" result="blended" />
       <feGaussianBlur in="blended" stdDeviation="{blur}" />
     </filter>
   </svg>
   ```

### 2.2 Transition from Vue to React + TypeScript
While the reference is built in Vue 3, VERISIGHT implements this in React 18 + TypeScript:
- **No Vue dependencies**.
- Reusable React hooks: `useLiquidGlass(options)` to dynamically generate optimized SVG filter definitions or fallback shader canvases.
- CSS backdrop layering: where high-frequency DOM repaints occur (e.g., live logs or rapid table filtering), the system gracefully uses hardware-accelerated CSS `backdrop-filter: blur(16px)` with multi-stop linear gradient specular borders (`border-image: linear-gradient(...)`) to maintain a steady 60 FPS.

---

## 3. Strict Enterprise Security Color Palette (Light Liquid Glass Edition)

| Token | Hex Code | Purpose & Semantic Role |
| :--- | :--- | :--- |
| **Background** | `#F8FAFC` | Crisp slate-50 base; clean, modern enterprise canvas. |
| **Sidebar Base** | `#FFFFFF` | Frosted white navigation container with 1px border. |
| **Surface** | `#FFFFFF` | Solid white workspace panels, inspection drawers. |
| **Card / Glass Panel** | `rgba(255, 255, 255, 0.85)` | Interactive cards with 16px backdrop blur, specular rim highlight. |
| **Primary Blue** | `#2563EB` | Primary action buttons, active navigation indicators (Blue 600). |
| **Sky / Accent** | `#0284C7` | Focus rings, active forensic bounding boxes, highlights (Sky 600). |
| **Success (CLEAR)** | `#16A34A` | Document verified, valid check digits, authenticated (Green 600). |
| **Warning (REVIEW)** | `#D97706` | Expired date, OCR low confidence, manual review required (Amber 600). |
| **Critical (HIGH RISK)** | `#DC2626` | Tampering detected, check digit failure, severe mismatch (Red 600). |
| **Primary Text** | `#0F172A` | Deep slate-900; ultra-high contrast for dense forensics. |
| **Secondary Text** | `#475569` | Slate-600; metadata labels, timestamps, field descriptions. |
| **Muted Text** | `#94A3B8` | Slate-400; helper labels, subtle technical indicators. |
| **Glass Border** | `rgba(15, 23, 42, 0.08)` | Crisp 1px boundary defining optical depth and separation. |
| **Glass Highlight** | `rgba(255, 255, 255, 0.95)` | Top-edge specular highlight simulating directional light. |

---

## 4. Reusable Glass Component Architecture (React + Tailwind)

### 4.1 `GlassPanel` & `GlassCard`
- **Visual Stacking**:
  1. Base: `#142238` at 65% opacity.
  2. Backdrop: `backdrop-filter: blur(12px) saturate(140%)`.
  3. Border: 1px solid `rgba(255, 255, 255, 0.08)` with subtle top highlight.
  4. Inset Box Shadow: `inset 0 1px 0 0 rgba(255, 255, 255, 0.12)`.
  5. Ambient Drop Shadow: `0 8px 32px 0 rgba(0, 0, 0, 0.37)`.
- **Performance Lock**: Applied strictly to containers, headers, and modals. **Never applied to repeated table rows in scrolling lists**.

### 4.2 `GlassButton`
- **States**: Default, Hover, Active, Disabled, Loading.
- **Refraction Feedback**: Hover state activates an internal radial gradient accentuating the curved corners. Focus-visible renders a crisp `2px solid #38BDF8` ring with 2px offset.

### 4.3 `GlassModal` & `GlassDialog`
- Full-screen backdrop using `#080F1D` at 80% opacity with `backdrop-filter: blur(8px)`.
- Center dialog card with elevated specular rim border, trapped focus, and ESC key listener.

### 4.4 `GlassSidebar` & `GlassTopbar`
- Permanent chrome elements anchored with subtle glass refraction, allowing forensic imagery to gently bleed under topbar margins during inspection panning.

### 4.5 `GlassInput` & `GlassSelect`
- Optimized for data entry: `#0D1728` background with 1px border.
- On focus: border shifts to `#38BDF8` with zero layout shift.

---

## 5. Legibility & Accessibility Guarantees (WCAG AA)

1. **Dense Data Surface Protection**:
   All critical data surfaces (OCR extraction tables, MRZ character matrix, audit log entries, JSON forensic payloads) are rendered on **solid or near-solid surfaces** (minimum 92% alpha or opaque `#0D1728` / `#111E32`). No transparent glass blurring behind raw character strings.
2. **Contrast Ratio**:
   - Primary text (`#F8FAFC`) on Surface (`#111E32`): **13.8:1** (Far exceeds WCAG AAA 7:1 requirement).
   - Secondary text (`#94A3B8`) on Surface (`#111E32`): **6.2:1** (Exceeds WCAG AA 4.5:1 requirement).
3. **Accessibility Fallback Modes**:
   - `@media (prefers-reduced-motion: reduce)`: All spring animations, transitions, and refraction shimmers are replaced with instantaneous state changes.
   - `@media (prefers-reduced-transparency: reduce)`: Glass panels immediately revert to 100% opaque `#142238` solid backgrounds, disabling backdrop filters.
   - `@supports not (backdrop-filter: blur(1px))`: Fallback to solid surfaces with high-contrast borders.

---

## 6. Anti-Slop Interface Rules

- **Zero Generic AI Visuals**: No rainbow gradients, no floating particle blobs, no glowing orbs.
- **Typography**: Inter / JetBrains Mono for cryptographic hashes, MRZ lines, and coordinates. Strict modular scale (12px, 14px, 16px, 18px, 24px, 32px).
- **Iconography**: Lucide React icons only. Every icon corresponds to an unambiguous security action (e.g., `ShieldCheck`, `AlertTriangle`, `FileSearch`, `KeyRound`, `Fingerprint`). No emojis as icons.
- **Micro-Copy**: Every empty state, tooltip, and button label uses standard law enforcement and forensic terminology (e.g., "Awaiting Document Ingestion", "ICAO Doc 9303 Check Digit Failure", "Laplacian Variance Below Threshold").

