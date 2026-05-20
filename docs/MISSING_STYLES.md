# Missing Styles — Gap Analysis

Patterns found in other repos that are **not yet covered** by the codebase style library.
Each entry notes what the pattern is, where it lives, and how it should integrate.

> **All 67 items resolved.** See `STYLE_GAPS.md` for details.

---

## Dosiserv (`Dosiserv CYC.py`)

HTML is generated inline starting at line 1222.

### ~~1. Person-button group layout~~
~~**What:** `.groups-row` + `.group-col` + `.group-label` — a `display:flex; flex-wrap:wrap` row of columns, each column holding a group label and a stack of person buttons.~~
~~**Where:** `Dosiserv CYC.py` lines 1244–1263~~
~~**Integration:** Add a `.btn-group-grid` (or `.person-grid`) layout block to `layout.css`. The group label should become a small `.group-label` utility (bold, plum `var(--color-brand-purple)`, small font). The current `button-row` only handles a flat list — this is for hierarchical grouped buttons.~~

### ~~2. Person button (`.person-btn`)~~
~~**What:** Small button with flat blue `#3875BA` background, `border-radius: 12px`, `font-size: 13px`, no gradient. Hover uses `opacity: 0.85` instead of transform.~~
~~**Where:** `Dosiserv CYC.py` lines 1264–1276~~
~~**Integration:** Add as `.btn--flat` or `.btn--person` variant in `components.css`. Distinct from `.btn--primary` (gradient) and `.btn--outline` (border). Needs the JS "equalize all widths to the widest button" pattern documented alongside.~~

### ~~3. Positioned modal close button~~
~~**What:** `.modal-close` positioned `absolute; top: 8px; right: 12px` with plum colour `#662678` (not white). Used when modal close is inside a white-background box rather than a gradient header.~~
~~**Where:** `Dosiserv CYC.py` lines 1301–1311~~
~~**Integration:** Add `.modal-close--anchored` variant in `components.css`. Current `.modal-close` assumes a gradient header; this variant sits on white.~~

### ~~4. Image gallery modal (`.modal-box`)~~
~~**What:** A modal body variant that stacks multiple `<img>` elements with a small gap spacer (`.modal-img-gap: height: 12px`). Uses `max-height: 90vh; overflow: auto`.~~
~~**Where:** `Dosiserv CYC.py` lines 1295–1316~~
~~**Integration:** Add `.modal-panel--gallery` modifier and `.modal-img-gap` utility in `components.css`. The current `.modal-body` lacks a max-height and vertical scroll story.~~

### ~~5. Branded `<hr>` divider (`.divider`)~~
~~**What:** `border: none; border-top: 2px solid #E40D7E` centred at 90% width.~~
~~**Where:** `Dosiserv CYC.py` lines 1315–1319~~
~~**Integration:** Add `.divider` (and optionally `.divider--brand`) to `components.css` using `var(--color-brand-pink)`.~~

### ~~6. Auto-refresh with modal cancel~~
~~**What:** `setTimeout(location.reload, 60000)` stored in `refreshTimer`, cleared on modal open, restored on modal close. Common pattern across Dosiserv, Rooster, Productieplanning.~~
~~**Where:** `Dosiserv CYC.py` lines 1346–1376 (JS)~~
~~**Integration:** Document as a standard JS snippet in a future `patterns.js` or README. Not CSS, but a cross-repo interaction pattern worth centralising.~~

---

## Rooster (`cyclotron updater running.py`)

HTML is generated in `generate_html()` starting at line 407.

### ~~7. Fixed sticky page header (`.header--fixed`)~~
~~**What:** `.header` with `position: fixed; top: 0; left: 0; right: 0; min-height: 70px; z-index: 1000` with matching `padding-top: 120px` on `body`. The codebase `.header` is a non-fixed flex row.~~
~~**Where:** `cyclotron updater running.py` lines 422–435, body line 419~~
~~**Integration:** Add `.header--fixed` modifier to `layout.css` plus a `body.has-fixed-header` rule or a `--header-height` token. The current `.header` should remain non-fixed as the base.~~

### ~~8. Logo inside header (`.logo`)~~
~~**What:** `width: 250px; height: auto; margin-right: 30px` logo image.~~
~~**Where:** `cyclotron updater running.py` lines 436–439~~
~~**Integration:** The codebase `layout.css` already has `.header-right img` (max-height 160px). Add `.header-logo` as a left-side logo variant (fixed width, no max constraints).~~

### ~~9. Page title with text-shadow (`.title`)~~
~~**What:** Large `font-size: 40px; color: #662678; text-shadow: 1px 1px 2px rgba(0,0,0,0.3)` centred title inside the fixed header, with `gap: 15px` flex layout.~~
~~**Where:** `cyclotron updater running.py` lines 440–455~~
~~**Integration:** Could become a `h1.page-heading--hero` variant in `base.css`. Currently `h1` in codebase uses `--font-display` (ISOCPEUR monospace); this header title uses Arial.~~

### ~~10. Navigation button group in header (`.nav-buttons-container`, `.nav-button`)~~
~~**What:** Vertically stacked gradient buttons (`font-size: 12px`, `border-radius: 6px`, `box-shadow: 0 2px 4px`) for switching between sub-pages. Hover lifts with `translateY(-1px)`.~~
~~**Where:** `cyclotron updater running.py` lines 456–498~~
~~**Integration:** Add `.btn--nav` (small, stacked gradient button) to `components.css`. The return button grey variant (`.return-button`) needs `.btn--nav--secondary`.~~

### ~~11. Page-switching content panels (`.page-content`, `.page-content.active`)~~
~~**What:** `display: none` / `display: block` pattern for client-side tab-like page switching via JS `classList.add('active')`.~~
~~**Where:** `cyclotron updater running.py` lines 493–499~~
~~**Integration:** Add `.page-panel` + `.page-panel.is-visible` to `components.css`. Naming aligned with the codebase `.is-open` convention.~~

### ~~12. Toggle chip (`.toggle-chip`, `.toggle-chip.active`)~~
~~**What:** Small `border-radius: 12px; font-size: 10px` pill toggles for showing/hiding rows. Default `#e0e0e0` background, active turns `#4CAF50` (green).~~
~~**Where:** `cyclotron updater running.py` lines 522–549~~
~~**Integration:** Add `.chip` + `.chip.is-active` to `components.css`. The active colour should map to `var(--color-success)` to use the existing success token. Note: this differs from `.pill` (status display, not interactive).~~

### ~~13. Name chip / person tag (`.name-chip`, `.name-chip.selected`)~~
~~**What:** Small clickable `border-radius: 12px; font-size: 10px` tag for person name selection. Default `#f0f0f0`, selected turns `var(--color-brand-purple)` with pink border.~~
~~**Where:** `cyclotron updater running.py` lines 574–615~~
~~**Integration:** Extend `.chip` with a `.chip--selectable` variant and a `.chip.is-selected` state using brand tokens.~~

### ~~14. Calendar week table (`.week-table`)~~
~~**What:** `border-collapse: collapse; border-radius: 8px; overflow: hidden; table-layout: fixed` table with a fixed `200px` service-column (`.dienst-col`) and 7 equal day columns. Per-day gradient headers (`nth-child` to simulate a continuous purple→pink sweep across columns).~~
~~**Where:** `cyclotron updater running.py` lines 634–712~~
~~**Integration:** Add `.table--calendar` modifier and `.table__dienst-col` to `components.css`. The per-column nth-child gradient header is a Rooster-specific pattern and should be documented as a `table--week-gradient` sub-modifier.~~

### ~~15. Day-state row/cell classes (`.current-day`, `.past-day`, `.weekend`, `.current-week`)~~
~~**What:** `.current-day` — blue gradient `#3875BA → #4CC9F0` with inner shadow. `.past-day` — grey background `#f0f0f0; color: #666`. `.weekend` — slightly off-white `#fafafa`. `.current-week` — `box-shadow: 0 0 0 8px #3875BA` on the table.~~
~~**Where:** `cyclotron updater running.py` lines 713–731~~
~~**Integration:** Add to `components.css` as table state modifiers. `--color-text-heading-h2` (`#3875BA`) already exists in tokens. `--color-disabled` covers the past-day text colour.~~

### ~~16. Highlighted cell with pulse animation (`.highlighted-cell`)~~
~~**What:** Gold `linear-gradient(135deg, #FFD700, #FFA500)` cell with inset pulse shadow animation on selected-name cells.~~
~~**Where:** `cyclotron updater running.py` lines 733–744 (CSS) and `@keyframes pulse` line 741~~
~~**Integration:** Add `.table__cell--highlight` to `components.css` and a `highlight-pulse` keyframe to `animations.css`. Currently `animations.css` only has `pulse` (opacity) — this needs a shadow-pulse variant.~~

### ~~17. Shift row colour-coding (`.shift-o`, `.shift-m`, `.shift-n`)~~
~~**What:** `fffacd` (yellow) for ochtend, `f0f8ff` (light blue) for middag, `f0fff0` (light green) for nacht.~~
~~**Where:** `cyclotron updater running.py` lines 809–812~~
~~**Integration:** Add `.row--shift-ochtend`, `.row--shift-middag`, `.row--shift-nacht` to `components.css`. Colours should become tokens: `--color-shift-ochtend`, etc.~~

### ~~18. Day section header (`.day-header`)~~
~~**What:** `background: var(--color-brand-gradient)` full-width div acting as a section separator with white bold text, `font-size: 18px`, `border-radius: 6px`.~~
~~**Where:** `cyclotron updater running.py` lines 797–808~~
~~**Integration:** Add `.section-header--day` (or `.callout-header`) to `components.css`. Different from `h2` (no underline) and `.modal-header` (no rounded corners all-around).~~

### ~~19. Maintenance table (`.maintenance-day-table`) with secondary blue header~~
~~**What:** Table with `th { background: #5891d1 }` — a lighter blue than brand. Used specifically for maintenance/work items where brand gradient would be too heavy.~~
~~**Where:** `cyclotron updater running.py` lines 770–795~~
~~**Integration:** Add `--color-table-secondary: #5891d1` token and a `.table--secondary` modifier. Or unify to `--color-text-heading-h2` (`#3875BA`) which is close.~~

### ~~20. Minutes value cell (`.minutes-cell`)~~
~~**What:** `font-weight: bold; color: #662678` — bold plum number in a table cell.~~
~~**Where:** `cyclotron updater running.py` lines 819–822~~
~~**Integration:** Merge into existing `.cell-kpi-lg` concept or add `.cell-value--plum` using `var(--color-brand-purple)`.~~

### ~~21. Stock alert section (`.below-minimum`, `.at-minimum`)~~
~~**What:** `background: #ffebee; color: #c62828` (below) and `background: #fff3e0; color: #ef6c00` (at minimum) — table cell colouring for inventory thresholds.~~
~~**Where:** `cyclotron updater running.py` lines 857–866~~
~~**Integration:** Add `.cell--critical` and `.cell--warning` to `components.css` using the existing `--color-danger` and `--color-warning` tokens.~~

### ~~22. Plating tile grid (inline styles, no class)~~
~~**What:** Three colored container cards (`background: #0077BE`, `#90EE90`, `#FFB347`) each holding a `display: grid; grid-template-columns: repeat(3,1fr)` of stock tiles. Tiles have dynamic background colour (white/red/orange) based on stock level.~~
~~**Where:** `cyclotron updater running.py` lines 1618–1735 (all inline styles in JS template literal)~~
~~**Integration:** This is the most unextracted pattern. Needs a `.tile-container`, `.tile-grid`, and `.tile` component in `components.css`, with `.tile--critical` and `.tile--warning` state modifiers. Container background should become context-specific tokens or be passed via CSS custom property overrides.~~

### ~~23. Warning info banner (inline, no class)~~
~~**What:** `background: #fff3cd; border-radius: 12px; border-left: 6px solid #ffc107` — amber left-border box, different from the red `.tampering-banner`.~~
~~**Where:** `cyclotron updater running.py` line 1738 (inline style)~~
~~**Integration:** Add `.alert-banner` + `.alert-banner--warning` (amber) and `.alert-banner--danger` (red) to `components.css`. The `.tampering-banner` is too specialised and too loud for general warnings.~~

### ~~24. Last-update bar (`#last-update`)~~
~~**What:** `text-align: center; font-size: 14px; color: #666; background: white; padding: 10px; border-radius: 5px; box-shadow` — a small centred status bar showing timestamp.~~
~~**Where:** `cyclotron updater running.py` lines 759–769~~
~~**Integration:** Add `.status-bar` to `components.css`. Uses existing shadow and border-radius tokens.~~

### ~~25. Sticky table column header (`th` with `position: sticky; top: 0; z-index: 10`)~~
~~**What:** Horizontal sticky for table `<th>` (vertical scroll), different from `.col-sticky` which sticks a column left (horizontal scroll).~~
~~**Where:** `cyclotron updater running.py` lines 1051–1054 (also Productieplanning line ~1047)~~
~~**Integration:** Add `.col-sticky-top` to `components.css`. Also needs a `--z-table-header` token in `tokens.css`.~~

---

## Productieplanning (`Productieplanning running.py`)

HTML is generated in `generate_html()` starting at line 496.

### ~~26. Three-column info dashboard (`.top-container`, `.top-box`)~~
~~**What:** `display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px` layout with white `border-radius: 8px` boxes above the main table. Different from `.chart-row-three` which is for chart canvases.~~
~~**Where:** `Productieplanning running.py` lines 533–548~~
~~**Integration:** `.chart-row-three` in `layout.css` is close but semantically wrong (no charts here). Add `.info-row-three` or repurpose `.chart-row-three` as `.grid-row--3` in `layout.css`.~~

### ~~27. Legend component (`.legend`, `.legend-column`, `.legend-item`)~~
~~**What:** Two-column flex layout of colour-coded `display: inline-block; padding: 4px 8px; border-radius: 4px` chips showing what each row colour means.~~
~~**Where:** `Productieplanning running.py` lines 549–600~~
~~**Integration:** Add `.legend` + `.legend__item` to `components.css`. Background colour is set per-item inline; the component just needs the layout and border-radius.~~

### ~~28. Large countdown display (`.end-week-info`, `.end-week-time`)~~
~~**What:** Centred info block with a `font-size: 30px; font-weight: bold` time value and a smaller label. Used for "next Thursday EOW" countdown.~~
~~**Where:** `Productieplanning running.py` lines 602–616~~
~~**Integration:** Add `.countdown-display` to `components.css`. The `font-size: 30px` should map to a new `--font-size-countdown: 30px` token or reuse `--font-size-h2`.~~

### ~~29. Controls toolbar (`.controls`, `.cyclotron-filter`)~~
~~**What:** `display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap` toolbar with filter buttons.~~
~~**Where:** `Productieplanning running.py` lines 618–631~~
~~**Integration:** Add `.toolbar` to `layout.css`. The current `.button-row` is centred text-align — this is a proper flex toolbar with gap control.~~

### ~~30. Coloured toggle button variants (`.cyclotron-filter button`, `.hide-completed-toggle`, `.changelog-toggle`)~~
~~**What:** Three different outlined toggle buttons: green `#4CAF50` (filter), orange `#ff9800` (hide completed), blue `#2196F3` (changelog). Each has `.active` state filling the background.~~
~~**Where:** `Productieplanning running.py` lines 632–691~~
~~**Integration:** Add `.btn--toggle` base with `border: 2px solid` + `.btn--toggle--green/orange/blue` variants, or map to a generic `.btn--toggle` that inherits a `--btn-toggle-color` CSS variable. The `.active` class pattern should align to codebase `.is-open` / `.is-active` convention.~~

### ~~31. Alarm flash button (`.changelog-toggle.alarm-flash`)~~
~~**What:** When an alarm fires, a button turns red with `@keyframes button-flash` (red glow oscillation) and `box-shadow` animation.~~
~~**Where:** `Productieplanning running.py` lines 687–701~~
~~**Integration:** Add `@keyframes button-glow` to `animations.css` and `.btn.is-alarming` modifier to `components.css`. Different from existing `pulse` which is opacity-only.~~

### ~~32. Alarm bar overlay (`.alarm-bar`, `.alarm-bar.active`)~~
~~**What:** `position: fixed; top: 0; left: 0; right: 0` full-width red alert bar with `@keyframes alarm-pulse`, a message div and a stop button. Pushes content down when active (body needs padding-top).~~
~~**Where:** `Productieplanning running.py` lines 1170–1202~~
~~**Integration:** Add `.alarm-overlay-bar` to `components.css`. Distinct from `.tampering-banner` (static, always visible). This appears/disappears based on JS state. Add `--z-alarm-bar` token above `--z-modal`.~~

### ~~33. Changelog modal (`.changelog-modal`, `.changelog-content`, `.changelog-entry`)~~
~~**What:** Modal variant with an internal filter text input, print button, and changelog entries left-bordered by type (new=green, modified=orange, deleted=red, running=red/amber).~~
~~**Where:** `Productieplanning running.py` lines 757–974~~
~~**Integration:** The base modal structure should reuse `.modal-overlay` / `.modal-panel`. Add `.changelog-entry` + type modifiers (`.changelog-entry--new`, `--modified`, `--deleted`, `--running`) to `components.css`. Left-border colour pattern is the same as Cycrevparts `.alert` blocks.~~

### ~~34. Print styles (`@media print`)~~
~~**What:** Hides all UI, shows only `.changelog-print-container` using `'Courier New'` monospace font, `12pt`, `page-break-inside: avoid`.~~
~~**Where:** `Productieplanning running.py` lines 876–925~~
~~**Integration:** Add a `print.css` partial to the codebase. Currently `dashboard.css` has no print rules. The gantt chart, tables and reports across all repos need consistent print behaviour.~~

### ~~35. Table container (`.table-container`)~~
~~**What:** White `background; padding: 10px 15px 15px; border-radius: 8px; box-shadow` wrapping div for a table. Has an embedded `h3` with no extra padding.~~
~~**Where:** `Productieplanning running.py` lines 1005–1018~~
~~**Integration:** Very similar to the Cycrevparts `.card`. Consolidate as `.card` in `components.css` — this pattern appears in all repos.~~

### ~~36. Coloured-border live-status container variants (`.live-status-container`, `.next-productions-container`, `.ingroei-container`)~~
~~**What:** `.table-container` variants with `background: #CFD9DE` (mink) and a coloured left/full border: plum, sea-blue, cherry respectively.~~
~~**Where:** `Productieplanning running.py` lines 1020–1033~~
~~**Integration:** Add `.card--border-purple`, `.card--border-blue`, `.card--border-cherry` modifiers to `components.css`. Background `#CFD9DE` = `--taupe`/`--mink` from Cycrevparts palette — add as `--color-bg-muted` token.~~

### ~~37. Product isotope row colour coding (`.product-rb081`, `.product-i123`, `.product-tl201`, `.product-ga067`, `.product-in111`)~~
~~**What:** `border-left: 10px solid` with the existing isotope colours (Rb=red, I=green, Tl=yellow, Ga=blue, In=cyan). These match the `--color-isotope-*` tokens already in `tokens.css` but have no corresponding CSS classes.~~
~~**Where:** `Productieplanning running.py` lines 1117–1135~~
~~**Integration:** Add `.row--isotope-thallium`, `.row--isotope-gallium`, etc. to `components.css` using the existing `--color-isotope-*` tokens. This closes the gap between the token definitions and their actual use.~~

### ~~38. Row status classes (`.current-production`, `.ending-soon`, `.ending-very-soon`, `.completed`, `.pause-row`, `.info-row`)~~
~~**What:** Table row state modifiers: `#fff9c4` (current), `#ffeb3b` (ending soon), `#ff5252 + pulse` (ending very soon), `text-decoration: line-through; opacity: 0.6` (completed), italic (pause/info).~~
~~**Where:** `Productieplanning running.py` lines 1072–1115~~
~~**Integration:** Add `.row--active`, `.row--warning`, `.row--urgent` (with pulse), `.row--done`, `.row--pause`, `.row--info` to `components.css`. `--color-warning` and `--color-danger` tokens already exist; add `--color-row-active: #fff9c4` and `--color-row-warning: #ffeb3b`.~~

### ~~39. Productieplanning local gantt (`.gantt-container`, `.gantt-header`)~~
~~**What:** Uses same `.gantt-container` class but with `border-bottom: 3px solid #4CAF50` for the header (green) instead of `--color-border`. The gantt rendering itself is full JavaScript/canvas — the CSS classes wrap the container only.~~
~~**Where:** `Productieplanning running.py` lines 1226–1245~~
~~**Integration:** Productieplanning should adopt `gantt.css` from codebase directly. The green border is an override that should be removed or token-ised as `--color-accent-gantt`.~~

---

## Cycrevparts (`app/static/css/main.css` + templates)

### ~~40. Sticky top navbar (`.navbar`, `.navbar-logo`, `.navbar-links`, `.navbar-search`)~~
~~**What:** `position: sticky; top: 0; z-index: 100; height: 56px; background: var(--gradient)` navbar with logo (32px height), link list with active/hover states (semi-transparent white bg), and a transparent-background search input on the right.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 47–109~~
~~**Integration:** Add `navbar.css` partial (or merge into `layout.css` as `.navbar` block). Codebase currently has no navigation component. The `--color-brand-gradient` token exists.~~

### ~~41. Page header with subtitle (`.page-header`, `.page-title`, `.page-subtitle`)~~
~~**What:** `display: flex; justify-content: space-between; align-items: center` header with a `.page-title` (navy, 1.4rem bold) and `.page-subtitle` (muted, 0.9rem) stacked left, and action buttons right.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 119–137~~
~~**Integration:** Add to `layout.css` as `.page-header` alongside existing `.header`. This pattern (title+subtitle pair) is cleaner and more reusable.~~

### ~~42. Card component (`.card`, `.card-header`, `.card-title`)~~
~~**What:** `background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); overflow: hidden` card with a `border-bottom: 2px solid var(--taupe)` header containing a `.card-title`.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 140–160~~
~~**Integration:** Add `.card` to `components.css`. This is the single most reused pattern across all repos (Rooster `.top-box`, Productieplanning `.table-container`, Cycrevparts `.card`). Should be the canonical card.~~

### ~~43. Button size variants (`.btn-sm`, `.btn-lg`)~~
~~**What:** `.btn-sm: padding: 0.3rem 0.7rem; font-size: 0.8rem` and `.btn-lg: padding: 0.65rem 1.4rem; font-size: 1rem`.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 203–204~~
~~**Integration:** Add to `components.css` as `.btn--sm` and `.btn--lg` (or `-sm`/`-lg` to match codebase BEM naming).~~

### ~~44. Secondary and danger button variants (`.btn-secondary`, `.btn-danger`)~~
~~**What:** `.btn-secondary` — navy background, white text, hover darkens. `.btn-danger` — `#C62828` background, white text.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 186–201~~
~~**Integration:** Add `.btn--secondary` and `.btn--danger` to `components.css`. `--color-danger` token already exists.~~

### ~~45. Complete form system~~
~~**What:** `.form-group`, `.form-label` (with `.required` star), `.form-control` (focus glow `rgba(56,117,186,0.12)`), `.form-hint`, `.form-row` (auto-fit grid), `.form-section` (bottom-bordered section), `.form-section-title` (plum uppercase label).~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 206–265~~
~~**Integration:** Add `forms.css` partial and import in `dashboard.css`. This is entirely absent from the codebase. The focus glow should use `var(--color-text-heading-h2)` (sea blue) at 12% opacity.~~

### ~~46. Data table class (`table.data-table`)~~
~~**What:** Navy `#283066` header (vs gradient in codebase), sortable column indicators (`::after` ▲/▼), zebra striping (`tr:nth-child(even): background: #fafafa`), hover row `#eef3fb`, `cursor: pointer` on rows.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 267–310~~
~~**Integration:** Add `.table--data` modifier to `components.css`. The gradient `thead` in codebase is intentional for dashboards; this navy variant is for app-style data entry. Both can coexist as `.table--dashboard` and `.table--data`.~~

### ~~47. Badge system (`.badge` + all variants)~~
~~**What:** `display: inline-flex; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.76rem; font-weight: 600` base, with 9 item-status variants (`badge-in-bedrijf`, `badge-gereviseerd`, `badge-ongereviseerd`, `badge-in-revisie`, `badge-defect`, `badge-nieuw`, `badge-mottenballen`, `badge-onbekend`, `badge-afgevoerd`/`badge-afgekeurd`) and 6 alert-level variants (`badge-ok`, `badge-laag`, `badge-kritiek`, `badge-info`, `badge-warning`, `badge-archief`).~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 312–340~~
~~**Integration:** Add `badges.css` partial (or extend `components.css`). The item-status variants need corresponding `--color-status-*` tokens in `tokens.css`. Alert-level badge colours overlap with VSM cell colours.~~

### ~~48. Alert block system (`.alert`, `.alert-kritiek`, `.alert-laag`, `.alert-info`, `.alert-ok`)~~
~~**What:** `display: flex; gap: 0.75rem; padding: 0.85rem 1rem; border-radius: 6px` with `border-left: 4px solid` per severity. Has `.alert-icon` span for emoji/icon.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 343–357~~
~~**Integration:** Add `.alert` to `components.css`. More versatile than `.tampering-banner` (which is full-width, always danger). This is the general alert pattern. Colours map to existing `--color-success/danger/warning` tokens.~~

### ~~49. Dashboard stat card system (`.stat-grid`, `.stat-card`, `.stat-value`, `.stat-label`)~~
~~**What:** `display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr))` responsive grid of stat cards. Each card has a `border-top: 3px solid` status accent, a large value (`font-size: 2rem`) and a small uppercase label.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 360–393~~
~~**Integration:** Add to `components.css`. Similar concept to codebase's `.kpi-strip` but card-based rather than inline. Both can coexist — `.kpi-strip` for in-table summaries, `.stat-grid` for page-level KPI cards.~~

### ~~50. Timeline component (`.timeline`, `.timeline-item`, `.timeline-date`, `.timeline-actie`, `.timeline-detail`)~~
~~**What:** `padding-left: 1.5rem; border-left: 2px solid var(--mink)` vertical timeline with `::before` dot markers (`width: 8px; height: 8px; border-radius: 50%; background: var(--seablue)`).~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 395–431~~
~~**Integration:** Add `timeline.css` partial or merge into `components.css`. Completely absent from codebase. The dot colour should use `var(--color-text-heading-h2)` (`#3875BA`).~~

### ~~51. Filter bar (`.filter-bar`, `.filter-group`)~~
~~**What:** `display: flex; flex-wrap: wrap; gap: 0.5rem 1rem` white bar with subtle shadow for filter controls. `.filter-group` stacks a small label above each control.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 433–448~~
~~**Integration:** Add `.filter-bar` to `layout.css`. The `.controls` toolbar in Productieplanning serves a similar purpose — consolidate into one pattern.~~

### ~~52. Pagination (`.pagination`)~~
~~**What:** `display: flex; gap: 0.3rem; justify-content: flex-end` with bordered links, hover state, and `.active` navy highlight.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 450–468~~
~~**Integration:** Add `.pagination` to `components.css`. Not currently in codebase at all.~~

### ~~53. Horizontal step indicator (`.steps`, `.step`, `.step.active`, `.step.done`)~~
~~**What:** `display: flex; border-radius: 6px; overflow: hidden` row of equal-width steps. Active = navy bg, done = green bg.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 470–493~~
~~**Integration:** See also item 54 (wizard steps). Two implementations exist — choose one as canonical and document in `components.css`.~~

### ~~54. Wizard steps component (`.wizard-steps`, `.wizard-step`, `.wizard-step-nr`, `.wizard-connector`)~~
~~**What:** A more detailed step indicator: numbered circle (32px, gradient when active, green when done), label text, and `flex: 1; height: 2px` connecting line between steps.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 552–605~~
~~**Integration:** This is more polished than `.steps`. Make `.wizard-steps` the canonical implementation in `components.css` and deprecate the simpler `.steps`. The `_wizard_steps.html` partial in Cycrevparts templates should reference the codebase class.~~

### ~~55. Collapsible details/summary (`.collapsible`)~~
~~**What:** `details.collapsible > summary` styled as a clickable `background: var(--taupe); border-radius: 5px; font-weight: 600` row with `▶`/`▼` CSS-generated arrow.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 495–513~~
~~**Integration:** Add `details.collapsible` pattern to `components.css`. No collapsible pattern exists in codebase.~~

### ~~56. Utility class system~~
~~**What:** `.text-muted`, `.text-danger`, `.text-success`, `.text-plum`, `.text-navy`, `.fw-bold`, `.mt-1/2/3`, `.mb-1/2`, `.d-flex`, `.gap-1/2`, `.align-center`, `.justify-between`, `.flex-wrap`.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 515–531~~
~~**Integration:** Add `utilities.css` partial imported last in `dashboard.css`. The codebase currently has no utility classes — everything is component-scoped.~~

### ~~57. Flash message system (`.flash`, `.flash-success`, `.flash-error`, `.flash-warning`)~~
~~**What:** Left-border coloured notification blocks `border-left: 4px solid` for server-side flash messages.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 533–537~~
~~**Integration:** Merge into `.alert` system (item 48). The pattern is identical — only the naming differs (`.flash` vs `.alert`). Use `.alert` as canonical name.~~

### ~~58. Archived row / label (`.archived-row`, `.archived-label`)~~
~~**What:** `.archived-row td { opacity: 0.55 }` and a small `font-style: italic; background: #eee; border-radius: 10px` inline label.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 539–548~~
~~**Integration:** Add `.row--archived` and `.tag--archived` to `components.css`. Common pattern for soft-deleted records.~~

### ~~59. Responsive breakpoints (`@media (max-width: 768px)`)~~
~~**What:** Hides `.navbar-links`, stacks `.form-row` to 1 column, makes `.stat-grid` 2-column, reduces `.page-container` padding, hides `.wizard-step-label`.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 641–648~~
~~**Integration:** Add a `responsive.css` partial to the codebase. The main dashboard (anthropic-claude-code) is display-only and screen-fixed, so it doesn't need breakpoints — but any Flask app using the codebase does.~~

### ~~60. QR label print layout~~
~~**What:** `@page { size: 62mm 50mm; margin: 0 }` — Brother label printer format. Label uses `display: flex` with a 28mm QR code SVG and text info column. Print-hides screen controls.~~
~~**Where:** `Cycrevparts/app/templates/items/qrlabel.html` lines 7–86~~
~~**Integration:** Add `print-label.css` to codebase for thermal/label printing. Separate from the A4 report print styles needed by Dosiserv/Productieplanning.~~

### ~~61. PDF/A4 report print layout~~
~~**What:** `@page { size: A4 landscape; margin: 1.5cm 1.2cm; @top-left/right/bottom-center }` CSS Paged Media with auto page headers/footers and page counter.~~
~~**Where:** `Cycrevparts/app/templates/rapport/pdf.html` lines 7–60~~
~~**Integration:** Add `print-report.css` partial. The `@page` named-string and counter patterns are reusable across any tabular report.~~

### ~~62. Taupe/mink background colour token~~
~~**What:** `--taupe: #DBD9D6` as page/card body background, `--mink: #CFD9DE` as border/divider. Cycrevparts uses taupe as `body { background }` rather than the codebase's `#f5f5f5`.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 12–14~~
~~**Integration:** Add `--color-bg-muted: #CFD9DE` and `--color-bg-taupe: #DBD9D6` to `tokens.css`. Already partially referenced in Rooster/Productieplanning as `#CFD9DE` hardcoded.~~

### ~~63. Item status colour tokens~~
~~**What:** 9 status colours for physical part states: in-bedrijf `#2E7D32`, gereviseerd `#3875BA`, ongereviseerd `#E65100`, in-revisie `#662678`, defect `#C62828`, nieuw `#00695C`, mottenballen `#78909C`, onbekend `#9E9E9E`, afgevoerd `#424242`.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` lines 21–30~~
~~**Integration:** Add `--color-status-*` tokens to `tokens.css`. `in-revisie` matches `--color-brand-purple`, `defect` matches `--color-danger`, `gereviseerd` matches `--color-text-heading-h2` — use the existing tokens where they align.~~

### ~~64. Navy colour token~~
~~**What:** `--navy: #283066` — a deep navy used as primary text, table headers, and page titles in Cycrevparts.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` line 9~~
~~**Integration:** Add `--color-navy: #283066` to `tokens.css`. Currently the codebase has `--color-vsm-header: #1a5276` (VSM-specific) but no general navy. This is a major brand colour across multiple apps.~~

### ~~65. Cherry colour token~~
~~**What:** `--cherry: #A51C70` — used as `.ingroei-container` border in Productieplanning and part of the colour palette comment in Cycrevparts.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` line 11; `Productieplanning running.py` line 1033~~
~~**Integration:** Add `--color-brand-cherry: #A51C70` to `tokens.css`. Currently absent despite being used in two repos.~~

### ~~66. `system-ui` font stack alternative~~
~~**What:** Cycrevparts uses `system-ui, -apple-system, "Segoe UI", sans-serif` while codebase uses explicit `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`. System-ui is more modern.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` line 36~~
~~**Integration:** Add `--font-body-system: system-ui, -apple-system, "Segoe UI", sans-serif` to `tokens.css` as a separate token. Cycrevparts is an app; the dashboard uses a specific Segoe stack intentionally.~~

### ~~67. Alpine.js x-cloak utility (`[x-cloak]`)~~
~~**What:** `[x-cloak] { display: none !important }` — hides elements before Alpine.js initialises to prevent flash.~~
~~**Where:** `Cycrevparts/app/static/css/main.css` line 631~~
~~**Integration:** Add to `utilities.css` or a future `alpine.css` if Alpine.js is used in other apps. Currently only Cycrevparts uses Alpine.~~

---

## Summary — Implementation Priority

| Priority | Items | Rationale |
|----------|-------|-----------|
| **High** (missing tokens) | ~~62, 63, 64, 65~~ | Token gaps affect every file that references these values |
| **High** (core missing components) | ~~42 (card), 45 (forms), 46 (data-table), 47 (badges), 48 (alerts), 49 (stat cards)~~ | Used in Cycrevparts and partially in other repos |
| **High** (missing layout) | ~~40 (navbar), 41 (page-header), 7 (fixed header)~~ | Required by any multi-page Flask app |
| **Medium** (interaction patterns) | ~~11 (page panels), 12 (toggle chips), 13 (name chips), 50 (timeline)~~ | Already working inline; good to centralise |
| **Medium** (table extensions) | ~~14 (calendar table), 15 (day states), 37 (isotope rows), 38 (row statuses)~~ | Mostly Productieplanning-specific |
| **Medium** (print) | ~~34, 59, 60, 61~~ | Needed when printing reports or labels |
| **Low** (animations/alarm) | ~~31 (glow keyframe), 32 (alarm bar), 33 (changelog modal)~~ | Productieplanning-specific edge cases |
| **Low** (utility classes) | ~~56, 57, 58, 66, 67~~ | Nice-to-have; can be added incrementally |
