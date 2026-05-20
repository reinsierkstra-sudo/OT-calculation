# LaptopHours — Build Plan

A local Python + SQLite + Flask application that retrospectively reconstructs
work sessions from the Windows Event Log, tracks overtime accrual and
compensation, manages multi-category vacation balances, and presents everything
in an interactive dashboard.

This document is the authoritative spec. Work through the phases in order.
Each phase has a clear definition of done; do not advance until the previous
phase passes its acceptance criteria.

---

## 1. Project goal

Track real laptop usage so the user has objective data for performance reviews.
Specifically:

- Reconstruct work sessions from two Windows Event Log sources: the
  `nucmed.lan` NetworkProfile (session timing) and the `NucMed-Corp`
  WLAN-AutoConfig channel (office vs. home-VPN categorisation).
- Compute overtime: any session time outside contracted office hours on
  weekdays, plus all time on weekends and public holidays.
- Flag suspiciously long OT segments for manual review (configurable threshold,
  outside office hours only — see §3).
- Allow the user to manually log vacation (multiple categories), sick hours,
  and OT compensation taken.
- Present everything via an interactive HTML dashboard with day/week/month/
  custom filters and averages compared to contract.

---

## 2. Signal model (result of diagnostic investigation)

The Windows Security log (lock/unlock events 4800/4801) and sleep/wake events
(Kernel-Power 42/107) are either inaccessible or unreliable on this managed
work laptop. The following two sources are confirmed accessible and produce
clean session data:

### Primary — NetworkProfile `nucmed.lan` (session timing)

| Event ID | Meaning |
|---|---|
| 10000 | `nucmed.lan` became active (VPN connected / arrived at office) |
| 10001 | `nucmed.lan` dropped (VPN disconnected / left office) |

Channel: `Microsoft-Windows-NetworkProfile/Operational`

A work session = the interval between a 10000 and the next 10001 for the
`nucmed.lan` profile. Consecutive sessions separated by less than
`stitch_gap_seconds` (default 180 s) are merged into one to handle brief VPN
drops and network handoffs.

This signal fires for both physical office presence and home-VPN use because
the user's machine auto-connects to the work VPN at home.

### Secondary — WLAN-AutoConfig `NucMed-Corp` (office categorisation)

| Event ID | Meaning |
|---|---|
| 8002 | Successfully associated with `NucMed-Corp` SSID |

Channel: `Microsoft-Windows-WLAN-AutoConfig/Operational`

If at least one Event 8002 for `NucMed-Corp` falls within a work session's
time window → session kind = `office`. Otherwise → `home_vpn`. This
distinction is informational only and does not affect any OT calculations.

---

## 3. Contract & overtime rules

- **Contracted week:** 40 h, Monday through Friday.
- **Office hours:** 08:30–17:00 (8.5 h on the clock, minus 30 min unpaid
  break = 8 h contracted per workday).
- **OT earned:** all session time outside 08:30–17:00 on weekdays + all
  session time on weekends and public holidays. Time inside the office-hours
  window never counts as OT regardless of total hours.
- **OT taken:** logged manually as a balance deduction. Counts toward that
  day's contract credit but never as OT earned.
- **No automatic deductions.** If the user is absent during office hours
  without an entry, the day simply shows as below contract — informational
  only.
- **Public holidays:** auto-seeded from `python-holidays` for `country='NL'`.
  On holidays, contracted hours = 0; all session time counts as OT.

### OT flag rule

Any continuous OT segment (session time falling **outside** 08:30–17:00, or
any session on a weekend/holiday) that exceeds `ot_flag_threshold_hours`
(configurable, default 4 h) is marked `ot_flagged = 1` in the sessions table
and highlighted in the dashboard for manual review. The flag is purely visual —
no automatic correction. The user can confirm (dismiss) or delete the session.

This catches overnight VPN connections that were never disconnected (e.g. a
session running from 15:25 to 03:33 the next morning generates ~10 h of OT,
which exceeds the threshold and is flagged).

---

## 4. Core decisions

| Decision | Choice |
|---|---|
| Session source | `nucmed.lan` NetworkProfile events (retrospective) |
| Office detection | `NucMed-Corp` WLAN event 8002 within session window |
| Background agent | Not required |
| Language | Python 3.11+ |
| Web framework | Flask |
| Database | SQLite (stdlib) |
| Frontend | Server-rendered Jinja templates + Chart.js |
| JS framework | None |
| Storage | Local: `C:\Users\<user>\LaptopHours\data\hours.db` |
| Server bind | `127.0.0.1:5000` |
| Timezone | All timestamps UTC in DB; displayed in `Europe/Amsterdam` |
| Week start | Monday |
| Styling | Deferred to `styling.md` (added to repo by owner) |

---

## 5. Repository layout

```
/laptophours
├── app/
│   ├── __init__.py
│   ├── harvester.py          # Phase 1 — reads Event Log, writes raw_events
│   ├── sessionizer.py        # Phase 3 — derives sessions from raw_events
│   ├── calculator.py         # Phase 4 — OT, balances, aggregates
│   ├── server.py             # Phase 5 — Flask app
│   ├── db.py                 # Schema bootstrap + connection helper
│   ├── holidays_seed.py      # Phase 6
│   ├── templates/
│   └── static/
├── config/
│   └── settings.toml
├── data/
│   └── hours.db              # gitignored
├── scripts/
│   ├── run_harvest.ps1
│   ├── start_dashboard.ps1
│   └── task_scheduler.xml
├── requirements.txt
├── styling.md                # provided by owner
└── BUILD_PLAN.md
```

`requirements.txt`:
```
Flask>=3.0
pywin32>=306
python-holidays>=0.50
tomli; python_version<"3.11"
```

`.gitignore`: `data/`, `__pycache__/`, `*.pyc`, `.venv/`, `*.log`

---

## 6. Configuration (`config/settings.toml`)

```toml
[work]
work_start                = "08:30"
work_end                  = "17:00"
break_minutes             = 30
contract_hours_per_week   = 40
work_days                 = ["Mon","Tue","Wed","Thu","Fri"]
timezone                  = "Europe/Amsterdam"

[harvester]
network_profile_name      = "nucmed.lan"      # work VPN / office profile
office_ssid               = "NucMed-Corp"     # physical office WiFi SSID
stitch_gap_seconds        = 180               # merge gaps shorter than this

[ot_flag]
ot_flag_threshold_hours   = 4                 # flag OT segments longer than this

[holidays]
country                   = "NL"
seed_years_around_current = 2

[server]
host = "127.0.0.1"
port = 5000
```

All values editable from the Settings page in the dashboard; `settings.toml`
is only read on fresh DB initialisation.

---

## 7. Phase 0 — Setup

1. Create the repo structure from §5.
2. Create Python 3.11+ venv, install requirements.
3. Implement `app/db.py`: `get_connection()` opens `data/hours.db`, sets
   `PRAGMA foreign_keys=ON`, bootstraps schema (§8) if fresh, seeds settings
   from `settings.toml`.
4. `python -m app.db --init` creates a fresh DB with all tables and seeded
   settings rows.

**Acceptance:** `python -c "import flask, win32evtlog, holidays; print('ok')`
runs cleanly; `--init` creates `hours.db`.

---

## 8. Phase 2 — Database schema

All `*_ts` columns: ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SS.sssZ`).
All `date` columns: ISO local-date strings (`YYYY-MM-DD`).

```sql
-- Raw events from Event Log
CREATE TABLE raw_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc        TEXT    NOT NULL,
    channel       TEXT    NOT NULL,   -- 'network_profile' | 'wlan'
    event_id      INTEGER NOT NULL,
    kind          TEXT    NOT NULL,   -- 'vpn_connect'|'vpn_disconnect'|'office_wlan'
    record_number INTEGER NOT NULL,
    raw_xml       TEXT,
    UNIQUE (channel, record_number)
);
CREATE INDEX idx_raw_events_ts ON raw_events(ts_utc);

CREATE TABLE harvester_watermark (
    channel        TEXT PRIMARY KEY,
    last_record_no INTEGER NOT NULL,
    last_run_utc   TEXT    NOT NULL
);

-- Derived work sessions
CREATE TABLE sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts     TEXT    NOT NULL,
    end_ts       TEXT,                  -- NULL while open-ended
    duration_min INTEGER,               -- NULL while open-ended
    kind         TEXT    NOT NULL DEFAULT 'unknown',
                                        -- 'office' | 'home_vpn' | 'unknown'
    ot_flagged   INTEGER NOT NULL DEFAULT 0   -- 1 if OT segment > threshold
);
CREATE INDEX idx_sessions_start ON sessions(start_ts);

-- Vacation / sick / OT-taken entries
CREATE TABLE vacation_categories (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT    NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE vacation_grants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL REFERENCES vacation_categories(id),
    year          INTEGER NOT NULL,
    hours_granted REAL    NOT NULL,
    note          TEXT,
    UNIQUE (category_id, year)
);

CREATE TABLE manual_entries (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    kind                 TEXT    NOT NULL,   -- 'vacation'|'sick'|'ot_taken'
    date                 TEXT    NOT NULL,
    start_time           TEXT,               -- 'HH:MM', NULL = full day
    hours                REAL    NOT NULL,
    vacation_category_id INTEGER REFERENCES vacation_categories(id),
    note                 TEXT,
    created_at           TEXT    NOT NULL,
    CHECK (kind IN ('vacation','sick','ot_taken')),
    CHECK (kind != 'vacation' OR vacation_category_id IS NOT NULL)
);
CREATE INDEX idx_manual_entries_date ON manual_entries(date);

CREATE TABLE holidays (
    date   TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('auto','manual'))
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

**Acceptance:** All constraints enforced; settings seeded from TOML on fresh
init.

---

## 9. Phase 1 — Harvester (`app/harvester.py`)

Reads two Event Log channels via `pywin32` (`win32evtlog.EvtQuery`).

### Channel A — NetworkProfile/Operational

Query: EventID 10000 OR 10001, profile name = `network_profile_name` setting.

| Event | kind stored |
|---|---|
| 10000 (`nucmed.lan` connected) | `vpn_connect` |
| 10001 (`nucmed.lan` disconnected) | `vpn_disconnect` |

Parse `Name` field from EventData XML to confirm profile name before storing.

### Channel B — WLAN-AutoConfig/Operational

Query: EventID 8002 (WLAN successfully connected).

| Condition | kind stored |
|---|---|
| EventID 8002, SSID = `office_ssid` setting | `office_wlan` |
| EventID 8002, SSID ≠ `office_ssid` | skip |

Parse `SSID` or `ProfileName` field from EventData XML.

### Idempotency

After each channel, update `harvester_watermark` with the max `record_number`
seen. On subsequent runs, only fetch `record_number > watermark`.

### CLI output

```
Harvested N new events (M vpn_connect, M vpn_disconnect, M office_wlan).
Watermark advanced to <timestamp>.
```

**Acceptance:** Running twice inserts zero new rows on second run. Parse errors
logged to `data/harvest.log`, never crash the process.

---

## 10. Phase 3 — Sessionizer (`app/sessionizer.py`)

Rebuilds the `sessions` table from `raw_events` on every run (cheap, avoids
partial-state bugs).

**Algorithm:**

```
TRUNCATE sessions

events = SELECT * FROM raw_events ORDER BY ts_utc ASC

open_start  = NULL
office_hits = []    # office_wlan timestamps within current session

FOR event IN events:
    IF event.kind == 'vpn_connect':
        IF open_start IS NOT NULL:
            # VPN reconnected without disconnect — check stitch gap
            gap = event.ts - last_event_ts
            IF gap <= stitch_gap_seconds:
                CONTINUE   # treat as same session, absorb reconnect
            ELSE:
                FLUSH session(open_start, last_disconnect_ts, office_hits)
                open_start  = event.ts
                office_hits = []
        ELSE:
            open_start  = event.ts
            office_hits = []

    ELIF event.kind == 'vpn_disconnect':
        IF open_start IS NOT NULL:
            last_disconnect_ts = event.ts

    ELIF event.kind == 'office_wlan':
        IF open_start IS NOT NULL:
            office_hits.append(event.ts)

# After all events: flush any open session
IF open_start IS NOT NULL:
    FLUSH session(open_start, end=NULL, office_hits)   # open-ended

FLUSH session(start, end, office_hits):
    kind = 'office' if office_hits else 'home_vpn'
    dur  = (end - start) in minutes if end else NULL

    ot_flagged = check_ot_flag(start, end, kind)

    INSERT INTO sessions(start_ts, end_ts, duration_min, kind, ot_flagged)
```

### OT flag check

For a session (start, end):
1. Compute the OT segment: all minutes in the session that fall outside
   08:30–17:00 on weekdays, or any minute on weekends/holidays.
2. If OT segment duration > `ot_flag_threshold_hours` × 60 → `ot_flagged = 1`.
3. Applies to office sessions too (e.g., a session ending at 03:00 after
   staying very late).

The most recent open-ended session is updated (not rebuilt) on each harvest
run.

**Acceptance:** Deterministic on re-run. All raw events accounted for.
`ot_flagged` set correctly on the April 14-style overnight session.

---

## 11. Phase 4 — Calculation engine (`app/calculator.py`)

Pure functions over DB data; no side effects.

### Per-day derivations

```
is_workday = date.weekday() IN work_days AND date NOT IN holidays

work_window = [combine(date, work_start), combine(date, work_end)]

sessions_for_day = all sessions overlapping this local date
    (open-ended sessions clipped to now)
    (sessions crossing midnight clipped to [00:00, 24:00))

logged_in_window_min  = sum of session minutes inside work_window (workdays only)
logged_out_window_min = total session minutes − logged_in_window_min

contract_min = (work_end − work_start − break_minutes) × 60  if workday else 0
             = 480 min for standard 08:30–17:00 with 30 min break

ot_earned_min = logged_out_window_min

manual entries on this date:
    vacation_min  = sum(hours × 60) for kind='vacation'
    sick_min      = sum(hours × 60) for kind='sick'
    ot_taken_min  = sum(hours × 60) for kind='ot_taken'

day_credit_min = logged_in_window_min + vacation_min + sick_min + ot_taken_min
                 + (contract_min if date is holiday else 0)

day_delta_min  = day_credit_min − contract_min
```

### Balances

- **OT balance** = Σ `ot_earned_min` (all time) − Σ `ot_taken_min` (all time).
  Flagged sessions contribute their full OT to the balance until the user
  deletes or confirms them.
- **Vacation balance per category, per year** = Σ grants − Σ vacation entries
  for that category and year.

### Aggregates

Weekly, monthly, yearly rollups of: logged time, OT earned, OT taken,
vacation, sick, contract, day-credit, delta.

Averages: per-weekday-name, per-week, per-month — each compared to the
corresponding contract figure.

### Public API

```python
def day_summary(date)      -> DaySummary
def range_summary(start, end) -> RangeSummary
def ot_balance(as_of=None) -> float          # hours
def vacation_balances(year) -> dict[CategoryId, float]
def weekday_averages(start, end) -> dict[str, float]
def flagged_sessions()     -> list[Session]  # all ot_flagged=1
```

**Acceptance:** Unit tests cover: session clipped to midnight; OT flag
triggered above threshold and not triggered below; vacation entry filling
day-credit; holiday day with session = full OT; open-ended session contributing
time up to now.

---

## 12. Phase 5 — Flask dashboard (`app/server.py`)

### Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Overview |
| `/sessions` | GET | Sessions table (filtered) |
| `/sessions/<id>/confirm` | POST | Dismiss OT flag |
| `/sessions/<id>/delete` | POST | Delete session |
| `/aggregates` | GET | Charts and averages |
| `/entries` | GET | Manual entries list |
| `/entries/new` | GET, POST | Add entry |
| `/entries/<id>/edit` | GET, POST | Edit entry |
| `/entries/<id>/delete` | POST | Delete entry |
| `/settings` | GET | Settings page |
| `/settings/work` | POST | Update work hours / contract |
| `/settings/vacation-categories` | POST | Add / rename / deactivate |
| `/settings/vacation-grants` | POST | Add / edit grants |
| `/settings/ot-flag` | POST | Update threshold |
| `/settings/holidays/reseed` | POST | Re-seed holidays for a year |
| `/api/refresh` | POST | Trigger harvest + sessionize on demand |

### Page contents

**Overview (`/`)**
- OT balance, vacation balance per active category (current year), this week
  vs contract, today's open session (if any).
- Flagged sessions count with link to review queue.
- "Refresh now" button.

**Sessions (`/sessions`)**
- Date-range filter (day / week / month / custom).
- Table: start, end, duration, kind (office/home_vpn), in-window, OT,
  flagged indicator.
- Flagged rows highlighted. Each flagged row has "Confirm" and "Delete" 
  actions.
- Footer: sums.

**Aggregates (`/aggregates`)**
- Daily day-credit vs contract bar chart with OT layer.
- Weekly rollup table.
- Weekday averages table (Mon avg … Fri avg) vs contract.

**Entries (`/entries`)**
- Filterable list. Buttons: `+ Vacation`, `+ Sick`, `+ OT taken`.

**Entry form (`/entries/new`)**
- Vacation: date, start_time (optional), hours, category, note.
- Sick: date, start_time (optional), hours, note.
- OT taken: date, hours, note.

**Settings (`/settings`)**
- Work hours, break, contract, work days.
- OT flag threshold (hours, outside office hours).
- Vacation categories: add / rename / deactivate.
- Vacation grants: per category per year.
- Holidays: list, reseed, manual add.

Styling driven by CSS variables in `static/style.css`. Per `styling.md` once
provided.

**Acceptance:** All routes 200. CRUD works end to end. Flagged sessions
visually distinct; confirm and delete actions work. Open-ended session shows
live duration on overview.

---

## 13. Phase 6 — Holiday seeding (`app/holidays_seed.py`)

- `python-holidays`, `country='NL'`.
- Seed on fresh DB init for current year ± `seed_years_around_current`.
- Re-seed from Settings page; never overwrites `source='manual'` rows.

---

## 14. Phase 7 — Automation (`scripts/`)

**`run_harvest.ps1`**
```powershell
$root = "C:\Users\$env:USERNAME\LaptopHours"
Set-Location $root
& "$root\.venv\Scripts\Activate.ps1"
python -m app.harvester *>> "$root\data\harvest.log"
```

**`start_dashboard.ps1`**
```powershell
$root = "C:\Users\$env:USERNAME\LaptopHours"
Set-Location $root
& "$root\.venv\Scripts\Activate.ps1"
Start-Process -WindowStyle Hidden python -ArgumentList "-m","app.server"
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5000"
```

**`task_scheduler.xml`**: importable XML running `run_harvest.ps1` at logon
and every 4 hours, and `start_dashboard.ps1` at logon. Both run as current
user, no elevation, no console window.

---

## 15. Phase 8 — Styling

Pending `styling.md`. Until present, neutral defaults with all colours and
fonts in CSS variables. Applying `styling.md` = update CSS variables only.

---

## 16. Definition of done

1. `python -m app.harvester` populates `raw_events` and triggers sessionizer.
2. Dashboard at `http://127.0.0.1:5000` is fully usable.
3. OT balance and vacation balances match hand-calculation against the raw
   data.
4. April 14-style overnight session (15:25 → 03:33) is flagged and appears
   highlighted in the sessions view.
5. Task Scheduler tasks run silently and unattended.
6. Styling applied per `styling.md`.

---

## 17. Constraints for the implementer

- Do not create files outside the layout in §5 without owner approval.
- Do not invent features not specified here.
- Do not assume SSID names — they come from `settings.toml` only.
- No external network calls at runtime. Holiday data via `python-holidays`
  (offline) at seed time only.
- No telemetry, no cloud uploads. Local only.
- CSS in `static/style.css`, theme via variables. No CSS framework.
- All times displayed in `Europe/Amsterdam`. All DB storage in UTC.
- Week starts Monday. ISO week numbering.
- Stop after each phase and verify acceptance criteria before continuing.
