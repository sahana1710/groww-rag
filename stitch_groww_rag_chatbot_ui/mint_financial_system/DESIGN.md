---
name: Mint Financial System
colors:
  surface: '#fbf8ff'
  surface-dim: '#d7d8f1'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f2ff'
  surface-container: '#ececff'
  surface-container-high: '#e5e6ff'
  surface-container-highest: '#dfe1fa'
  on-surface: '#171a2c'
  on-surface-variant: '#3c4a43'
  inverse-surface: '#2c2f42'
  inverse-on-surface: '#f0efff'
  outline: '#6b7b72'
  outline-variant: '#bacac1'
  surface-tint: '#006c4f'
  primary: '#006c4f'
  on-primary: '#ffffff'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#2fe0aa'
  secondary: '#3247e2'
  on-secondary: '#ffffff'
  secondary-container: '#4f63fb'
  on-secondary-container: '#fffbff'
  tertiary: '#934b07'
  on-tertiary: '#ffffff'
  tertiary-container: '#ffa15b'
  on-tertiary-container: '#733800'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dfe0ff'
  secondary-fixed-dim: '#bcc2ff'
  on-secondary-fixed: '#000b62'
  on-secondary-fixed-variant: '#102bcd'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb785'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#fbf8ff'
  on-background: '#171a2c'
  surface-variant: '#dfe1fa'
  mint-hover: '#00B386'
  mint-tint: '#E6FAF5'
  text-primary: '#44475B'
  text-secondary: '#7C7E8C'
  border-subtle: '#E9E9EB'
  surface-muted: '#F8F8F8'
  surface-card: '#FFFFFF'
  error-red: '#EB5B3C'
  dark-bg: '#121212'
  dark-surface: '#1E1E1E'
  dark-border: '#2A2E39'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  title-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 26px
  title-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  metric-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.02em
  metric-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system delivers a calm, transparent, and approachable financial interface tailored for retail investing, mutual funds, and equity trading. The aesthetic rejects the cluttered, anxiety-inducing density of legacy trading terminals in favor of clarity, composure, and confidence. 

The core philosophy blends modern minimalism with crisp financial utility:
- **Clean and Pure:** Pristine white surfaces and muted neutral backdrops maximize breathing room, reducing cognitive load when processing complex portfolio data.
- **Optimistic Accentuation:** Trademark mint green represents growth, stability, and positive yield without aggressive neon vibrancy.
- **Precision Typography:** Monospaced and proportional alignments guarantee absolute visual clarity for stock tickers, rupee denominations, percentages, and trade executions.
- **Trustworthy Ergonomics:** Soft geometric roundings, razor-thin borders, and purposeful contrast ratios cultivate security and ease-of-use for both first-time investors and active traders.

## Colors

The color palette centers on functional financial hierarchy and immediate visual legibility:

- **Primary (`#00D09C`):** Used strictly for high-intent actions (buy orders, primary CTAs), positive returns, confirmation states, and active navigational highlights. Accompanied by `#00B386` for hover interactions and `#E6FAF5` for subtle badges, active pill backgrounds, and soft callouts.
- **Secondary (`#5367FF`):** Digital indigo employed for technical indicators, educational tools, analytical charts, and non-actionable interactive cues.
- **Neutral Core (`#44475B`):** Deep charcoal slate engineered to replace harsh pure black, eliminating eye fatigue during prolonged portfolio review while preserving sharp contrast.
- **Secondary Slate (`#7C7E8C`):** Calibrated for secondary metadata, market timestamps, subheadings, and contextual hints.
- **Semantic Signals:** Negative market returns, stop-loss triggers, and validation errors are rendered in coral red (`#EB5B3C`).
- **Dark Mode Strategy:** Switches seamlessly to a deep foundation (`#121212`) with elevated card containers (`#1E1E1E`), softened borders (`#2A2E39`), and anti-glare luminous mint adjustments.

## Typography

Typography relies on Inter across all hierarchy tiers, delivering clinical, geometric legibility for financial figures, currency notations (₹), and tabular data feeds.

- **Financial Figures & Metrics:** Currency amounts and daily P&L figures utilize tabular figure settings (`tnum`) and tighter letter spacing to maintain visual alignment across updating tickers.
- **Weights:** Restricted to 400 (Body/Descriptive copy), 500 (Labels/Navigation/Table headers), 600 (Card titles/Stock symbols/Metrics), and 700 (High-impact promotional displays).
- **Hierarchy Handling:** Critical account values and real-time market valuations dominate using `metric-lg` and `headline-lg`, while secondary delta values (+₹1,240.50 / +2.14%) use `label-md` or `metric-md` directly adjacent.

## Layout & Spacing

The layout model utilizes a standard 12-column fluid grid system bounded by maximum reading containers to prevent content stretching on ultra-wide desktop monitors:

- **Desktop (1024px+):** Max-width 1280px, 12 columns with 24px (`1.5rem`) gutters and 32px (`2rem`) outer margin. Dashboard splits favor a 68/32 split between primary charting/holdings views and contextual order-placement panels.
- **Tablet (768px - 1023px):** 8 columns with 20px gutters and 24px outer margins. Two-column card rows reflow into balanced grids.
- **Mobile (< 768px):** 4 columns with 16px (`1rem`) gutters and 16px (`1rem`) outer margins. Dense tabular layouts collapse into stacked interactive cards with sticky bottom-anchored action bars.
- **Component Rhythm:** Interior component paddings follow strict 4px/8px increments. Dense list rows adhere to 56px height for tapability, while primary analytical cards leverage `space-lg` internal clearance.

## Elevation & Depth

Visual hierarchy prioritizes ultra-flat clarity, rejecting deep heavy shadows in favor of crisp borders, layered surfaces, and micro-elevation:

- **Level 0 (Base Canvas):** `#F8F8F8` in light mode (`#121212` in dark mode). Serves as the structural background behind all floating components.
- **Level 1 (Card & Content Blocks):** Pure `#FFFFFF` surface framed by a hairline 1px border (`#E9E9EB`). Flat elevation with zero default shadow for clean data density.
- **Level 2 (Hover & Active Cards):** Hairline border transitions to `#DCDCE0` accompanied by an ambient micro-shadow: `0 4px 12px rgba(68, 71, 91, 0.06)`.
- **Level 3 (Dropdowns & Popovers):** Elevated overlays receive `0 8px 24px rgba(68, 71, 91, 0.10)` bounded by a 1px border (`#E9E9EB`) for crisp contrast against underlying elements.
- **Level 4 (Sticky Order Sheets & Modals):** High-priority transaction dialogs receive `0 16px 40px rgba(0, 0, 0, 0.14)` with complete background backdrop blur (`backdrop-filter: blur(4px)`).

## Shapes

The design system applies a disciplined roundedness scale (Level 2) that reconciles approachable consumer software with institutional financial rigor:

- **Cards & Data Panels:** Formed with a standard 12px radius (`rounded-lg` adjustment), providing modern curvature while maximizing rectangular data real estate.
- **Filter Chips & Segmented Controls:** Formed with an 8px radius (`0.5rem`), matching the baseline `roundedness: 2` standard for tactile modular buttons.
- **Search Bars & Category Pills:** Complete full-pill geometry (`9999px`) reserved specifically for universal search inputs, ticker quick-filters, and verified account badges.
- **Form Controls & Modals:** Standard form fields adopt 8px radii, while major bottom sheets on mobile adopt 16px top corner rounding for natural thumb interaction.

## Components

### Buttons
- **Primary:** Background `#00D09C`, text `#FFFFFF`, 8px corner radius, font weight 600. Hover state shifts to `#00B386`. Active scale down to 0.98 for tactile feedback.
- **Secondary / Outline:** Background transparent, 1px solid border `#E9E9EB`, text `#44475B`. On hover: border `#00D09C`, text `#00D09C`, background `#E6FAF5`.
- **Destructive:** Background `#EB5B3C`, text `#FFFFFF` for sell/exit positions.

### Chips & Badges
- **Status Badges:** Small 4px vertical padding, 8px horizontal padding, full pill radius. Green badges (`#E6FAF5` bg, `#00B386` text), neutral badges (`#F8F8F8` bg, `#7C7E8C` text).
- **Filter Chips:** 8px radius, border 1px `#E9E9EB`, background `#FFFFFF`. Selected state adopts `#E6FAF5` surface, `#00D09C` border, `#00D09C` label.

### Input Fields & Universal Search
- **Universal Search Bar:** Full-pill shaped (`rounded-full`), height 44px, background `#F8F8F8`, 1px border `#E9E9EB`. Icon prefix in `#7C7E8C`. Focused state transitions to `#FFFFFF` surface with 1px `#00D09C` border and subtle mint glow.
- **Form Inputs:** 8px corner radius, 12px internal padding, 1px `#E9E9EB` border. Floating or top-aligned labels in `label-md` (`#7C7E8C`). Focus state border `#00D09C`.

### Cards & Investment Modules
- **Holding / Ticker Cards:** Background `#FFFFFF`, 12px corner radius, 1px solid `#E9E9EB`. Internal padding of 16px (`1rem`) to 20px. Features inline micro sparkline graphs and positive/negative returns formatted in mint green or coral red.

### Lists & Tables
- **Market Data Tables:** Clean alternating or single-tone rows with 1px horizontal dividers (`#E9E9EB`). Numeric columns right-aligned with `tnum` tabular metrics. Row hover triggers `#F8F8F8` background tint.

### Checkboxes & Radio Controls
- **Checkboxes:** 4px rounded box, border 1.5px `#7C7E8C`. Checked state fills `#00D09C` with white checkmark.
- **Radio Buttons:** Circular 16px diameter, checked state renders an inner 8px dot of `#00D09C`.