"""
Phase 3 — Sessionizer

Rebuilds the sessions table from raw_events on every run.
Run via:  python -m app.sessionizer
"""

from datetime import datetime, timedelta, timezone, date as date_type
from zoneinfo import ZoneInfo

from .db import get_connection, get_setting, init_db


def _parse_ts(ts_str: str) -> datetime:
    """Parse ISO 8601 UTC string to aware datetime."""
    ts_str = ts_str.rstrip("Z")
    if "." in ts_str:
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


def _ot_flagged(
    start: datetime,
    end: datetime | None,
    work_start_str: str,
    work_end_str: str,
    threshold_hours: float,
    tz: ZoneInfo,
    holidays_set: set,
) -> int:
    if end is None:
        end = datetime.now(timezone.utc)

    ws_h, ws_m = map(int, work_start_str.split(":"))
    we_h, we_m = map(int, work_end_str.split(":"))

    ot_minutes = 0
    current = start

    while current < end:
        chunk_end = min(current + timedelta(minutes=1), end)
        local_dt = current.astimezone(tz)
        d = local_dt.date()
        weekday = d.weekday()  # 0=Mon … 6=Sun

        is_weekend = weekday >= 5
        is_holiday = d.isoformat() in holidays_set

        if is_weekend or is_holiday:
            ot_minutes += 1
        else:
            t = local_dt.time()
            work_start_t = local_dt.replace(hour=ws_h, minute=ws_m, second=0, microsecond=0).time()
            work_end_t   = local_dt.replace(hour=we_h, minute=we_m, second=0, microsecond=0).time()
            if t < work_start_t or t >= work_end_t:
                ot_minutes += 1

        current = chunk_end

    return 1 if ot_minutes > threshold_hours * 60 else 0


def _ot_flagged_fast(
    start: datetime,
    end: datetime | None,
    work_start_str: str,
    work_end_str: str,
    threshold_hours: float,
    tz: ZoneInfo,
    holidays_set: set,
) -> int:
    """Faster OT flag check — iterates by day rather than minute-by-minute."""
    if end is None:
        end = datetime.now(timezone.utc)

    if end <= start:
        return 0

    ws_h, ws_m = map(int, work_start_str.split(":"))
    we_h, we_m = map(int, work_end_str.split(":"))

    total_ot_seconds = 0.0

    # Iterate day by day in local time
    local_start = start.astimezone(tz)
    local_end   = end.astimezone(tz)

    current_day = local_start.date()
    end_day     = local_end.date()

    while current_day <= end_day:
        # Build local midnight boundaries for this calendar day
        day_start_local = datetime(
            current_day.year, current_day.month, current_day.day, 0, 0, 0, tzinfo=tz
        )
        day_end_local = datetime(
            current_day.year, current_day.month, current_day.day, 23, 59, 59, tzinfo=tz
        ) + timedelta(seconds=1)

        seg_start = max(start, day_start_local.astimezone(timezone.utc))
        seg_end   = min(end,   day_end_local.astimezone(timezone.utc))
        if seg_end <= seg_start:
            current_day += timedelta(days=1)
            continue

        is_weekend = current_day.weekday() >= 5
        is_holiday = current_day.isoformat() in holidays_set

        if is_weekend or is_holiday:
            total_ot_seconds += (seg_end - seg_start).total_seconds()
        else:
            # Only count time outside work window
            work_start_utc = datetime.combine(
                current_day,
                datetime.strptime(work_start_str, "%H:%M").time(),
                tzinfo=tz
            ).astimezone(timezone.utc)
            work_end_utc = datetime.combine(
                current_day,
                datetime.strptime(work_end_str, "%H:%M").time(),
                tzinfo=tz
            ).astimezone(timezone.utc)

            # Before work
            before_end = min(seg_end, work_start_utc)
            if before_end > seg_start:
                total_ot_seconds += (before_end - seg_start).total_seconds()

            # After work
            after_start = max(seg_start, work_end_utc)
            if seg_end > after_start:
                total_ot_seconds += (seg_end - after_start).total_seconds()

        current_day += timedelta(days=1)

    return 1 if total_ot_seconds > threshold_hours * 3600 else 0


def sessionize(conn) -> int:
    work_start = get_setting(conn, "work_start", "08:30")
    work_end   = get_setting(conn, "work_end",   "17:00")
    stitch_gap = int(get_setting(conn, "stitch_gap_seconds", "180"))
    ot_thresh  = float(get_setting(conn, "ot_flag_threshold_hours", "4"))
    tz_name    = get_setting(conn, "timezone", "Europe/Amsterdam")
    tz         = ZoneInfo(tz_name)

    holidays_rows = conn.execute("SELECT date FROM holidays").fetchall()
    holidays_set  = {r["date"] for r in holidays_rows}

    events = conn.execute(
        "SELECT ts_utc, kind FROM raw_events ORDER BY ts_utc ASC"
    ).fetchall()

    conn.execute("DELETE FROM sessions")

    sessions = []

    open_start: datetime | None = None
    office_hits: list[datetime] = []
    last_disconnect_ts: datetime | None = None
    last_event_ts: datetime | None = None

    for evt in events:
        kind   = evt["kind"]
        evt_ts = _parse_ts(evt["ts_utc"])

        if kind == "vpn_connect":
            if open_start is not None:
                gap = (evt_ts - last_event_ts).total_seconds() if last_event_ts else 999
                if gap <= stitch_gap:
                    last_event_ts = evt_ts
                    continue
                else:
                    sessions.append((open_start, last_disconnect_ts, office_hits[:]))
                    open_start  = evt_ts
                    office_hits = []
            else:
                open_start  = evt_ts
                office_hits = []
            last_disconnect_ts = None

        elif kind == "vpn_disconnect":
            if open_start is not None:
                last_disconnect_ts = evt_ts

        elif kind == "office_wlan":
            if open_start is not None:
                office_hits.append(evt_ts)

        last_event_ts = evt_ts

    # Flush last open session
    if open_start is not None:
        sessions.append((open_start, last_disconnect_ts, office_hits[:]))

    # Insert all sessions
    for (s_start, s_end, o_hits) in sessions:
        kind_val = "office" if o_hits else "home_vpn"
        dur = None
        if s_end is not None:
            dur = max(0, int((s_end - s_start).total_seconds() / 60))

        flagged = _ot_flagged_fast(
            s_start, s_end, work_start, work_end, ot_thresh, tz, holidays_set
        )

        end_str = s_end.strftime("%Y-%m-%dT%H:%M:%S.000Z") if s_end else None
        conn.execute(
            "INSERT INTO sessions(start_ts, end_ts, duration_min, kind, ot_flagged)"
            "VALUES (?,?,?,?,?)",
            (
                s_start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                end_str,
                dur,
                kind_val,
                flagged,
            ),
        )

    conn.commit()
    return len(sessions)


def main() -> None:
    init_db()
    conn = get_connection()
    n = sessionize(conn)
    conn.close()
    print(f"Sessionizer: rebuilt {n} sessions.")


if __name__ == "__main__":
    main()
