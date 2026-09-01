---
name: Midnight Engineering
colors:
  surface: '#0e1320'
  surface-dim: '#0e1320'
  surface-bright: '#343948'
  surface-container-lowest: '#090e1b'
  surface-container-low: '#161b29'
  surface-container: '#1a1f2d'
  surface-container-high: '#252a38'
  surface-container-highest: '#303443'
  on-surface: '#dee2f5'
  on-surface-variant: '#c4c5d6'
  inverse-surface: '#dee2f5'
  inverse-on-surface: '#2b303e'
  outline: '#8e909f'
  outline-variant: '#434654'
  surface-tint: '#b5c4ff'
  primary: '#b5c4ff'
  on-primary: '#00287d'
  primary-container: '#1547be'
  on-primary-container: '#b4c3ff'
  inverse-primary: '#2955cb'
  secondary: '#eec04e'
  on-secondary: '#3f2e00'
  secondary-container: '#b38b19'
  on-secondary-container: '#362700'
  tertiary: '#7bd7c5'
  on-tertiary: '#003730'
  tertiary-container: '#005d51'
  on-tertiary-container: '#7ad6c4'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b5c4ff'
  on-primary-fixed: '#00164e'
  on-primary-fixed-variant: '#003baf'
  secondary-fixed: '#ffdf99'
  secondary-fixed-dim: '#eec04e'
  on-secondary-fixed: '#251a00'
  on-secondary-fixed-variant: '#5a4300'
  tertiary-fixed: '#97f3e1'
  tertiary-fixed-dim: '#7bd7c5'
  on-tertiary-fixed: '#00201b'
  on-tertiary-fixed-variant: '#005046'
  background: '#0e1320'
  on-background: '#dee2f5'
  surface-variant: '#303443'
  surface-card: '#0D1F3C'
  surface-inset: '#152B52'
  surface-floating: '#1F3666'
  text-primary: '#F0F4FF'
  text-secondary: '#8896B3'
  text-muted: '#6A7B9E'
  border-subtle: '#1E2D4A'
  whatsapp: '#25D366'
  accent-blue-hover: '#2563F4'
  accent-gold-hover: '#F0C040'
typography:
  display-hero:
    fontFamily: Fraunces
    fontSize: 56px
    fontWeight: '700'
    lineHeight: '1.05'
    letterSpacing: -0.03em
  display-hero-mobile:
    fontFamily: Fraunces
    fontSize: 34px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  section-title:
    fontFamily: Fraunces
    fontSize: 42px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  card-heading:
    fontFamily: dmSans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  body-large:
    fontFamily: dmSans
    fontSize: 18px
    fontWeight: '300'
    lineHeight: '1.7'
  body-base:
    fontFamily: dmSans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.65'
  body-compact:
    fontFamily: dmSans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: jetbrainsMono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.10em
  telemetry-stat:
    fontFamily: jetbrainsMono
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.0'
    letterSpacing: -0.01em
  tech-chip:
    fontFamily: jetbrainsMono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.2'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  grid-unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
  section-gap-lg: 96px
  section-gap-sm: 48px
  container-max: 1200px
---

## Brand & Style

The design system is rooted in a **Dark Editorial Precision** aesthetic. It is engineered to project the quiet authority of high-performance software architecture and AI systems. The style blends the gravitas of a modern terminal with the refined elegance of classical typography, moving away from generic SaaS aesthetics toward an immersive, technical atmosphere.

The design movement is a hybrid of **Minimalism** and **Modern Corporate**, utilizing:
- **Atmospheric Depth:** Layered navy surfaces that create a sense of infinite digital space.
- **Precision Detailing:** Subtle hairline gridlines, 0.5px borders, and monospaced telemetry chips.
- **Luminous Accents:** Strategic use of glow effects and high-saturation accents (Cobalt, Gold, Teal) to guide the eye toward critical metrics and actions.
- **Mobile-First Utility:** A native-PWA approach ensuring the interface feels like a high-end application rather than a squeezed website on smaller viewports.

## Colors

The palette is anchored by a deep **Midnight Canvas** background. Colors are used functionally to denote expertise areas: **Cobalt Blue** for Backend/Architecture, **Amber Gold** for Impact/Metrics, and **Cyan Teal** for Cloud/AI.

- **Primary (Cobalt):** Used for primary CTAs and brand anchors. It represents stability and core engineering.
- **Secondary (Gold):** Used for high-priority metrics and editorial overlines. It adds a premium, "awarded" feel.
- **Tertiary (Teal):** Reserved for technical status, cloud services, and live indicators.
- **Neutrals:** A range of navy shades (`#0D1F3C` to `#1F3666`) provide structural hierarchy without the harshness of pure black or the flatness of standard gray.
- **Typography:** Text is tiered from **Ice White** for maximum readability to **Muted Steel** for metadata and timestamps.

## Typography

The typography system relies on a high-contrast pairing of an editorial serif and technical sans/mono fonts.

- **Fraunces (Headlines):** Used for "Display" roles. It provides a sculptural, authoritative personality. Use tight tracking for a dense, high-end look.
- **DM Sans (Body):** The workhorse for narrative content. A light weight (300) is preferred for large body sections to maintain a sophisticated feel, while regular (400) is used for readability in cards.
- **JetBrains Mono (Technical/Data):** Reserved for metrics, tech stacks, and labels. It reinforces the engineering background of the platform.

**Responsive Note:** Large display types use `clamp()` logic to ensure they scale fluidly, but mobile-specific overrides are provided for the most aggressive headlines.

## Layout & Spacing

This design system uses a **Fluid Grid** model centered on a 4px modular unit. 

### Grid Philosophy
- **Desktop:** A 12-column grid. Featured items should span 2 or 3 columns to prevent the "cramped" feel of generic templates. 
- **Mobile:** A single-column flow with generous vertical breathing room.
- **Safe Areas:** For PWA environments, the layout must respect `env(safe-area-inset-*)` variables, particularly for the bottom action bar and sticky headers.

### Rhythms
- **Vertical Spacing:** Use `clamp(48px, 8vw, 96px)` for section gaps to ensure the "generous whitespace" required by the brand.
- **Card Padding:** Standardize on 24px (`p-6`) for internal content spacing to maintain a premium, airy feel.
- **Touch Targets:** Interactive elements must maintain a 44px minimum height on mobile.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layering** and **Ambient Glows** rather than traditional heavy shadows.

- **The Canvas:** `#080D1A` acts as the infinite base.
- **Layer 1 (Cards):** `#0D1F3C` with a `0.5px` border in `#1E2D4A`. 
- **Layer 2 (Interaction):** Hover states should lift elements slightly (`translateY(-4px)`) and introduce a subtle cobalt or gold outer glow (`box-shadow: 0 12px 40px rgba(0,0,0,0.5)`).
- **Glass Effects:** Navigation and mobile menus utilize a 90% opacity backdrop with a heavy `blur(16px)` to maintain context while ensuring legibility.
- **Outlines:** Use low-opacity "ghost borders" for secondary elements to keep the UI feeling lightweight and precise.

## Shapes

The shape language is **Rounded**, favoring a "modern container" look that softens the technical edge of the dark theme.

- **Standard Elements:** 0.5rem (8px) for buttons and small cards.
- **Featured Cards:** 1rem (16px) or 1.5rem (24px) for large showcase containers and terminal windows.
- **Action Elements:** Hero CTAs and contact pills use a **Pill-shape** (999px) to distinguish them as high-priority interactive triggers.
- **Terminal Windows:** Must include 3-dot window controls (Red, Amber, Green) to reinforce the "engineering" metaphor.

## Components

### Buttons
- **Primary:** Solid Cobalt Blue (`#1547BE`) with white text. Pill-shaped for Hero/Contact.
- **Secondary:** Solid WhatsApp Green (`#25D366`) for direct messaging triggers.
- **Ghost/Outline:** 1px border in `#1E2D4A` that illuminates to blue on hover.

### Cards (The "Showcase" Container)
- Background: Deep Slate Navy (`#0D1F3C`).
- Border: 0.5px Hairline.
- Interaction: On hover, the border illuminates to a soft blue glow and the card lifts.

### Tech Chips & Badges
- Small, monospaced tags using `#152B52` backgrounds.
- Categorized by border color: Blue (Backend), Teal (Cloud), Gold (Frontend), Purple (AI).

### Form Inputs
- Background: Surface Inset (`#152B52`).
- Focus State: Border color shifts to Cobalt with a soft 3px glow ring.

### Navigation (Mobile PWA)
- **Header:** Sticky, minimal, glassmorphic.
- **Menu:** Full-screen overlay with centered large-typography links.
- **Bottom Action Bar:** A persistent, safe-area-aware bar containing WhatsApp, Call, and Email icons for instant access.

### Status Indicators
- Use a small 8px circle with a CSS `@keyframes pulse` animation for "Live" systems.