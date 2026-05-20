"""
Phase 3 — Sessionizer

Rebuilds the sessions table from raw_events on every run.

Algorithm (three passes):

  Pass 1 — raw intervals
    Walk events ordered by ts_utc.
    Each vpn_connect opens an interval; the next vpn_disconnect closes it.
    A second vpn_connect before a disconnect force-closes the previous
    interval at the new connect time (handles missed-disconnect events).
    A trailing open connect becomes an open-ended interval (end=None).
    office_wlan timestamps that fall inside the open interval are collected.

  Pass 2 — stitch short gaps
    Walk raw intervals in order. If the gap between interval[i].end and
    interval[i+1].start is ≤ stitch_gap_seconds, merge them into one
    interval (inheriting all office_wlan hits from both sides).

  Pass 3 — write sessions
    Truncate sessions, then insert one row per final interval with kind,
    duration_min, and ot_flagged computed fresh.

Run via:  python -m app.sessionizer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from .db import get_connection, get_setting, init_db


# ── Timestamp helper ───────────────────────────────────────────────────────

def _parse_ts(ts_str: str) -> datetime:
    ts = ts_str.rstrip("Z")
    if "." in ts:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ── Raw interval ───────────────────────────────────────────────────────────

@dataclass
class _Interval:
    start: datetime
    end: Optional[datetime]          # None = open-ended
    office_hits: list[datetime] = field(default_factory=list)


# ── OT flag check ──────────────────────────────────────────────────────────

def _ot_flagged(
    start: datetime,
    end: Optional[datetime],
    work_start_str: str,
    work_end_str: str,
    threshold_hours: float,
    tz: ZoneInfo,
    holidays_set: set[str],
) -> int:
    effective_end = end if end is not None else datetime.now(timezone.utc)
    if effective_end <= start:
        return 0

    ws_h, ws_m = map(int, work_start_str.split(":"))
    we_h, we_m = map(int, work_end_str.split(":"))

    ot_seconds = 0.0
    current_day = start.astimezone(tz).date()
    end_day     = effective_end.astimezone(tz).date()

    while current_day <= end_day:
        day_start_utc = datetime(
            current_day.year, current_day.month, current_day.day, 0, 0, 0, tzinfo=tz
        ).astimezone(timezone.utc)
        day_end_utc = day_start_utc + timedelta(days=1)

        seg_s = max(start,        day_start_utc)
        seg_e = min(effective_end, day_end_utc)
        if seg_e <= seg_s:
            current_day += timedelta(days=1)
            continue

        is_weekend  = current_day.weekday() >= 5
        is_holiday  = current_day.isoformat() in holidays_set

        if is_weekend or is_holiday:
            ot_seconds += (seg_e - seg_s).total_seconds()
        else:
            ws_utc = datetime(
                current_day.year, current_day.month, current_day.day,
                ws_h, ws_m, tzinfo=tz
            ).astimezone(timezone.utc)
            we_utc = datetime(
                current_day.year, current_day.month, current_day.day,
                we_h, we_m, tzinfo=tz
            ).astimezone(timezone.utc)

            # Time before work window
            before_end = min(seg_e, ws_utc)
            if before_end > seg_s:
                ot_seconds += (before_end - seg_s).total_seconds()

            # Time after work window
            after_start = max(seg_s, we_utc)
            if seg_e > after_start:
                ot_seconds += (seg_e - after_start).total_seconds()

        current_day += timedelta(days=1)

    return 1 if ot_seconds > threshold_hours * 3600 else 0


# ── Main ───────────────────────────────────────────────────────────────────

def sessionize(conn) -> int:
    work_start    = get_setting(conn, "work_start", "08:30")
    work_end      = get_setting(conn, "work_end",   "17:00")
    stitch_gap    = int(get_setting(conn, "stitch_gap_seconds", "180"))
    ot_thresh     = float(get_setting(conn, "ot_flag_threshold_hours", "4"))
    tz            = ZoneInfo(get_setting(conn, "timezone", "Europe/Amsterdam"))
    holidays_set  = {
        r["date"] for r in conn.execute("SELECT date FROM holidays").fetchall()
    }

    events = conn.execute(
        "SELECT ts_utc, kind FROM raw_events ORDER BY ts_utc ASC"
    ).fetchall()

    # ── Pass 1: build raw intervals ────────────────────────────────────────
    raw: list[_Interval] = []
    open_interval: Optional[_Interval] = None

    for evt in events:
        kind   = evt["kind"]
        evt_ts = _parse_ts(evt["ts_utc"])

        if kind == "vpn_connect":
            if open_interval is not None:
                # Force-close previous interval (missed disconnect)
                open_interval.end = evt_ts
                raw.append(open_interval)
            open_interval = _Interval(start=evt_ts, end=None)

        elif kind == "vpn_disconnect":
            if open_interval is not None:
                open_interval.end = evt_ts
                raw.append(open_interval)
                open_interval = None

        elif kind == "office_wlan":
            if open_interval is not None:
                open_interval.office_hits.append(evt_ts)

    # Flush trailing open interval
    if open_interval is not None:
        raw.append(open_interval)

    # ── Pass 2: stitch short gaps ──────────────────────────────────────────
    stitched: list[_Interval] = []
    for interval in raw:
        if (
            stitched
            and stitched[-1].end is not None
            and interval.end is not None  # never stitch two open-ended intervals
            and (interval.start - stitched[-1].end).total_seconds() <= stitch_gap
        ):
            merged = stitched[-1]
            merged.end = interval.end
            merged.office_hits.extend(interval.office_hits)
        else:
            stitched.append(_Interval(
                start=interval.start,
                end=interval.end,
                office_hits=list(interval.office_hits),
            ))

    # Allow stitching into a trailing open-ended interval too
    # (open-ended always goes last; check if prev closed interval can be merged)
    if len(stitched) >= 2 and stitched[-1].end is None and stitched[-2].end is not None:
        gap = (stitched[-1].start - stitched[-2].end).total_seconds()
        if gap <= stitch_gap:
            base = stitched[-2]
            tail = stitched.pop()
            base.end = None
            base.office_hits.extend(tail.office_hits)

    # ── Pass 3: write sessions ─────────────────────────────────────────────
    conn.execute("DELETE FROM sessions")

    for iv in stitched:
        kind_val = "office" if iv.office_hits else "home_vpn"

        if iv.end is not None:
            dur = max(0, int((iv.end - iv.start).total_seconds() / 60))
        else:
            dur = None

        flagged = _ot_flagged(
            iv.start, iv.end,
            work_start, work_end,
            ot_thresh, tz, holidays_set,
        )

        conn.execute(
            "INSERT INTO sessions(start_ts, end_ts, duration_min, kind, ot_flagged)"
            " VALUES (?,?,?,?,?)",
            (
                _fmt(iv.start),
                _fmt(iv.end) if iv.end else None,
                dur,
                kind_val,
                flagged,
            ),
        )

    conn.commit()

    # ── Replay overrides ───────────────────────────────────────────────────
    # Apply user corrections (confirm / delete) in the order they were made
    # so they survive re-harvests and full sessionizer rebuilds.
    overrides = conn.execute(
        "SELECT start_ts, end_ts, action FROM session_overrides ORDER BY created_at ASC"
    ).fetchall()

    for ov in overrides:
        if ov["action"] == "delete":
            conn.execute(
                "DELETE FROM sessions WHERE start_ts=? AND (end_ts IS ? OR end_ts=?)",
                (ov["start_ts"], ov["end_ts"], ov["end_ts"]),
            )
        elif ov["action"] == "confirm":
            conn.execute(
                "UPDATE sessions SET ot_flagged=0"
                " WHERE start_ts=? AND (end_ts IS ? OR end_ts=?)",
                (ov["start_ts"], ov["end_ts"], ov["end_ts"]),
            )

    conn.commit()
    return len(stitched)


def main() -> None:
    init_db()
    conn = get_connection()
    n = sessionize(conn)
    conn.close()
    print(f"Sessionizer: rebuilt {n} sessions.")


if __name__ == "__main__":
    main()
