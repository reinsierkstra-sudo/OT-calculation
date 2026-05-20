# Style Gaps

All issues below were identified by auditing the CSS files and resolved in commit `0b7c211`.

---

| # | Issue | File(s) | Resolution |
|---|-------|---------|------------|
| 1 | 14 hardcoded values not using tokens | `gantt.css`, `components.css`, `layout.css` | Added `--color-border-subtle`, `--color-gantt-now`, `--color-danger-dark`, `--color-gold`, `--font-size-pill`, `--font-size-modal-header`, `--pill-gap/padding/dot-size`; replaced every raw hex and raw `px` with token references |
| 2 | `--space-4: 15px` breaks the spacing scale | `tokens.css` | Changed to `16px` — scale is now 4 8 12 16 20 24 30 40 60 |
| 3 | Two token pairs sharing the same value with no explanation | `tokens.css` | Added a block comment explaining that `--color-bg-page`/`--color-bg-header` and `--color-text-primary`/`--color-border-strong` are intentionally separate semantic roles |
| 4 | Dead tokens never referenced in any CSS rule | `tokens.css` | Removed `--color-vsm-warning-bg`, `--color-vsm-danger-bg`; gave `--font-size-h3` a real value (`1.17em`) and wired it to `h3` in `base.css`; removed OTIF chart colour tokens (JS-only, no CSS consumer) |
| 5 | `.isotope-section h2` duplicated base `h2` rule exactly | `layout.css` | Removed the block entirely — the base rule in `base.css` already applies |
| 6 | `--z-gantt-labels` and `--z-gantt-block` both `10`; `.gantt-grid-lines` used raw `z-index: 1` | `tokens.css`, `gantt.css` | Set `--z-gantt-labels: 20`, added `--z-gantt-grid: 1`, replaced raw value in `gantt.css` |
| 7 | `--font-size-h3: inherit` misleading; `h3` had no font-size or font-weight | `tokens.css`, `base.css` | Token set to `1.17em` (browser default); `h3` in `base.css` now declares `font-size: var(--font-size-h3)` and `font-weight: var(--font-weight-bold)` |
| 8 | `fadeIn` and `slideUp` keyframes declared but never used | `animations.css` | Removed both |
| 9 | `.btn--outline` hover had no easing; base `.btn` used `border: none` conflicting with outline border | `components.css` | Base `.btn` now uses `border: 2px solid transparent`; added `background` and `color` to the shared transition |
| 10 | `.modal-overlay` base rule set `overflow: auto` leaked into fullscreen variant; `.is-open` logic was non-obvious | `components.css` | `overflow: auto` moved onto `.modal-overlay.is-open` only; fullscreen `.is-open` sets `overflow: hidden` explicitly; removed the `:not()` selector |
| 11 | `.section-subtitle` used raw negative margin `-8px` | `components.css` | Changed to `calc(-1 * var(--space-2))` |
| 12 | Gantt row/block heights (`70px`/`60px`) hardcoded in CSS with no tokens | `tokens.css`, `gantt.css` | Added `--gantt-row-height`, `--gantt-block-height`, `--gantt-block-inset`, `--gantt-header-height`, `--gantt-label-width`; all four gantt files now reference these |
| 13 | `tokens.css` imported five times — once per partial | all partials, `dashboard.css` | Removed `@import url('tokens.css')` from all partials; `dashboard.css` imports tokens once at the top, then each partial in order |
| 14 | No `line-height` tokens | `tokens.css`, `base.css`, `components.css` | Added `--line-height-tight`, `--line-height-base`, `--line-height-loose`; applied to `body`, `h1`–`h3`, and key components |
| 15 | No `font-weight` tokens; `bold` and `600` used interchangeably | `tokens.css`, all files | Added `--font-weight-normal`, `--font-weight-semibold`, `--font-weight-bold`; replaced every raw `font-weight` value across all files |

---

## MISSING_STYLES items resolved

All 67 items from `MISSING_STYLES.md` resolved across multiple commits on branch `claude/resolve-style-gaps-uMfUV`.

| # | MISSING_STYLES item | File(s) changed | Resolution |
|---|---------------------|-----------------|------------|
| MS-1 | Person-button group layout (`.btn-group-grid`, `.group-label`) | `layout.css` | Added `.btn-group-grid`, `.btn-group-grid__col`, `.group-label` |
| MS-2 | Person button (`.btn--person`) | `components.css` | Added `.btn--person` flat blue variant with opacity hover |
| MS-3 | Positioned modal close button (`.modal-close--anchored`) | `components.css` | Added `.modal-close--anchored` (absolute, plum colour) |
| MS-4 | Image gallery modal (`.modal-panel--gallery`) | `components.css` | Added `.modal-panel--gallery` + `.modal-img-gap` |
| MS-5 | Branded `<hr>` divider (`.divider`) | `components.css` | Added `.divider` + `.divider--brand` using `var(--color-brand-pink)` |
| MS-6 | Auto-refresh with modal cancel (JS pattern) | — | Documented: JS-only pattern; no CSS required. Centralise in `patterns.js` / README when ready |
| MS-7 | Fixed sticky page header (`.header--fixed`) | `layout.css`, `tokens.css` | Added `.header--fixed`, `body.has-fixed-header`, `--z-header-fixed` token |
| MS-8 | Logo inside header (`.header-logo`) | `layout.css` | Added `.header-logo` left-side logo variant |
| MS-9 | Page title with text-shadow (`.page-heading--hero`) | `base.css` | Added `.page-heading--hero` (Arial, 40px, plum, text-shadow, flex gap) |
| MS-10 | Navigation button group (`.btn--nav`, `.btn--nav--secondary`) | `components.css` | Added `.btn--nav` + `.btn--nav--secondary` |
| MS-11 | Page-switching panels (`.page-panel`) | `components.css` | Added `.page-panel` + `.page-panel.is-visible` |
| MS-12 | Toggle chip (`.chip`) | `components.css` | Added `.chip` + `.chip.is-active` (maps to `var(--color-success)`) |
| MS-13 | Name chip / person tag (`.chip--selectable`) | `components.css` | Added `.chip--selectable` + `.chip--selectable.is-selected` |
| MS-14 | Calendar week table (`.table--calendar`) | `components.css` | Added `.table--calendar`, `.table__dienst-col`, `.table--week-gradient` nth-child sweep |
| MS-15 | Day-state row/cell classes | `components.css` | Added `.current-day`, `.past-day`, `.weekend`, `.current-week` |
| MS-16 | Highlighted cell with pulse (`.table__cell--highlight`) | `components.css`, `animations.css` | Added `.table__cell--highlight`; added `highlight-pulse` keyframe |
| MS-17 | Shift row colour-coding | `components.css`, `tokens.css` | Added `.row--shift-ochtend/middag/nacht`; added `--color-shift-*` tokens |
| MS-18 | Day section header (`.section-header--day`) | `components.css` | Added `.section-header--day` |
| MS-19 | Maintenance table (`.table--secondary`) | `components.css`, `tokens.css` | Added `.table--secondary`; added `--color-table-secondary` token |
| MS-20 | Minutes value cell (`.cell-value--plum`) | `components.css` | Added `.cell-value--plum` using `var(--color-brand-purple)` |
| MS-21 | Stock alert cells (`.cell--critical`, `.cell--warning`) | `components.css` | Added `.cell--critical` and `.cell--warning` |
| MS-22 | Plating tile grid | `components.css` | Added `.tile-container`, `.tile-grid`, `.tile`, `.tile--critical`, `.tile--warning` |
| MS-23 | Warning info banner (`.alert-banner`) | `components.css` | Added `.alert-banner`, `.alert-banner--warning`, `.alert-banner--danger` |
| MS-24 | Last-update bar (`.status-bar`) | `components.css` | Added `.status-bar` |
| MS-25 | Sticky table column header (`.col-sticky-top`) | `components.css`, `tokens.css` | Added `.col-sticky-top`; added `--z-table-header` token |
| MS-26 | Three-column info dashboard | `layout.css` | Added `.grid-row--3` (semantic rename of `.chart-row-three` intent) |
| MS-27 | Legend component | `components.css` | Added `.legend`, `.legend__item`, `.legend__swatch` |
| MS-28 | Large countdown display | `components.css`, `tokens.css` | Added `.countdown-display`, `.countdown-display__value/label`; added `--font-size-countdown` token |
| MS-29 | Controls toolbar (`.toolbar`) | `layout.css` | Added `.toolbar` flex toolbar |
| MS-30 | Coloured toggle button variants | `components.css` | Added `.btn--toggle` + `--btn-toggle-color` CSS variable; `--green/orange/blue` variants |
| MS-31 | Alarm flash button (`.btn.is-alarming`) | `components.css`, `animations.css` | Added `.btn.is-alarming`; added `button-glow` keyframe |
| MS-32 | Alarm bar overlay (`.alarm-overlay-bar`) | `components.css`, `animations.css`, `tokens.css` | Added `.alarm-overlay-bar` + `.is-active`; added `alarm-pulse` keyframe; added `--z-alarm-bar` token |
| MS-33 | Changelog modal entries | `components.css` | Added `.changelog-entry` + `--new/modified/deleted/running` modifiers |
| MS-34 | Print styles (`@media print`) | `print.css` (new) | New `print.css` partial; imported in `dashboard.css` note |
| MS-35 | Table container (`.table-container`) | `components.css` | Consolidated as canonical `.card` component |
| MS-36 | Coloured-border container variants | `components.css`, `tokens.css` | Added `.card--border-purple/blue/cherry`, `.card--bg-muted`; `--color-bg-muted` token |
| MS-37 | Isotope row border-left classes | `components.css` | Added `.row--isotope-thallium/gallium/indium/rubidium/iodine` using existing `--color-isotope-*` tokens |
| MS-38 | Row status classes | `components.css`, `tokens.css` | Added `.row--active/warning/urgent/done/pause/info`; added `--color-row-active/warning` tokens |
| MS-39 | Productieplanning local gantt | — | Migration note: adopt codebase `gantt.css` directly; remove green border override or token-ise as `--color-accent-gantt` |
| MS-40 | Sticky top navbar | `layout.css` | Added `.navbar`, `.navbar-logo`, `.navbar-links`, `.navbar-search` |
| MS-41 | Page header with subtitle | `layout.css` | Added `.page-header`, `.page-header__titles`, `.page-title`, `.page-subtitle` |
| MS-42 | Card component (`.card`) | `components.css` | Added canonical `.card`, `.card-header`, `.card-title` (same commit as MS-35) |
| MS-43 | Button size variants | `components.css` | Added `.btn--sm` and `.btn--lg` |
| MS-44 | Secondary and danger button variants | `components.css` | Added `.btn--secondary` (navy) and `.btn--danger` |
| MS-45 | Complete form system | `forms.css` (new) | New `forms.css` partial with `.form-group/label/control/hint/row/section` |
| MS-46 | Data table (`.table--data`) | `components.css` | Added `.table--data` with navy header, sort indicators, zebra stripe |
| MS-47 | Badge system | `components.css` | Added `.badge` base + 9 item-status variants + 6 alert-level variants |
| MS-48 | Alert block system | `components.css` | Added `.alert`, `.alert-icon`, severity modifiers; canonical for `.flash-*` too |
| MS-49 | Dashboard stat card system | `components.css` | Added `.stat-grid`, `.stat-card`, `.stat-value`, `.stat-label` |
| MS-50 | Timeline component | `components.css` | Added `.timeline`, `.timeline-item`, `.timeline-date/actie/detail` with `::before` dot |
| MS-51 | Filter bar | `layout.css` | Added `.filter-bar`, `.filter-group` |
| MS-52 | Pagination | `components.css` | Added `.pagination` with bordered links and `.is-active` navy highlight |
| MS-53 | Horizontal step indicator | `components.css` | Added `.steps`, `.step` (simpler variant; use wizard-steps for new work) |
| MS-54 | Wizard steps component | `components.css` | Added canonical `.wizard-steps`, `.wizard-step`, `.wizard-step-nr`, `.wizard-connector`, `.wizard-step-label` |
| MS-55 | Collapsible details/summary | `components.css` | Added `details.collapsible > summary` with CSS arrow |
| MS-56 | Utility class system | `utilities.css` (new) | New `utilities.css` with text, spacing, flex helpers |
| MS-57 | Flash message system | `components.css` | Merged into `.alert` system (`.flash-success` → `.alert.alert--ok`, etc.) |
| MS-58 | Archived row / label | `components.css` | Added `.row--archived` and `.tag--archived` |
| MS-59 | Responsive breakpoints | — | Note: add `responsive.css` partial when first Flask view requires it; dashboard is screen-fixed |
| MS-60 | QR label print layout | `print-label.css` (new) | New `print-label.css` for Brother 62mm×50mm thermal label |
| MS-61 | PDF/A4 report print layout | `print-report.css` (new) | New `print-report.css` with CSS Paged Media `@page` + named strings + page counter |
| MS-62 | Taupe/mink background colour token | `tokens.css` | Added `--color-bg-muted: #CFD9DE` and `--color-bg-taupe: #DBD9D6` |
| MS-63 | Item status colour tokens | `tokens.css` | Added 9 `--color-status-*` tokens |
| MS-64 | Navy colour token | `tokens.css` | Added `--color-navy: #283066` |
| MS-65 | Cherry colour token | `tokens.css` | Added `--color-brand-cherry: #A51C70` |
| MS-66 | `system-ui` font stack alternative | `tokens.css` | Added `--font-body-system` token |
| MS-67 | Alpine.js `[x-cloak]` utility | `utilities.css` | Added `[x-cloak] { display: none !important }` |
