"""
Phase 4 — Calculation engine

Pure functions over DB data; no side effects.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, date as date_type
from typing import Optional
from zoneinfo import ZoneInfo

from .db import get_connection, get_setting


# ── Helper ─────────────────────────────────────────────────────────────────

def _parse_ts(ts_str: str) -> datetime:
    if ts_str is None:
        return datetime.now(timezone.utc)
    ts_str = ts_str.rstrip("Z")
    if "." in ts_str:
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


def _work_window_utc(d: date_type, work_start_str: str, work_end_str: str, tz: ZoneInfo):
    ws_h, ws_m = map(int, work_start_str.split(":"))
    we_h, we_m = map(int, work_end_str.split(":"))
    ws = datetime(d.year, d.month, d.day, ws_h, ws_m, tzinfo=tz).astimezone(timezone.utc)
    we = datetime(d.year, d.month, d.day, we_h, we_m, tzinfo=tz).astimezone(timezone.utc)
    return ws, we


def _overlap_seconds(a_start, a_end, b_start, b_end) -> float:
    start = max(a_start, b_start)
    end   = min(a_end,   b_end)
    if end <= start:
        return 0.0
    return (end - start).total_seconds()


def _get_config(conn):
    return {
        "work_start":  get_setting(conn, "work_start",  "08:30"),
        "work_end":    get_setting(conn, "work_end",    "17:00"),
        "break_min":   int(get_setting(conn, "break_minutes", "30")),
        "tz":          ZoneInfo(get_setting(conn, "timezone", "Europe/Amsterdam")),
        "work_days":   get_setting(conn, "work_days", "Mon,Tue,Wed,Thu,Fri").split(","),
    }


_WEEKDAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ── Data structures ────────────────────────────────────────────────────────

@dataclass
class DaySummary:
    date: date_type
    is_workday: bool
    is_holiday: bool
    contract_min: int
    logged_in_window_min: float
    logged_out_window_min: float
    ot_earned_min: float
    vacation_min: float
    sick_min: float
    ot_taken_min: float
    day_credit_min: float
    day_delta_min: float
    sessions: list = field(default_factory=list)


@dataclass
class RangeSummary:
    start: date_type
    end: date_type
    total_logged_min: float
    ot_earned_min: float
    ot_taken_min: float
    vacation_min: float
    sick_min: float
    contract_min: float
    day_credit_min: float
    day_delta_min: float
    days: list = field(default_factory=list)


# ── Core functions ─────────────────────────────────────────────────────────

def day_summary(conn, d: date_type) -> DaySummary:
    cfg = _get_config(conn)
    tz  = cfg["tz"]
    now_utc = datetime.now(timezone.utc)

    holidays_set = {
        r["date"] for r in conn.execute("SELECT date FROM holidays").fetchall()
    }

    is_holiday  = d.isoformat() in holidays_set
    weekday_abbr = _WEEKDAY_ABBR[d.weekday()]
    is_workday  = weekday_abbr in cfg["work_days"] and not is_holiday

    contract_min = 0
    if is_workday:
        ws_h, ws_m = map(int, cfg["work_start"].split(":"))
        we_h, we_m = map(int, cfg["work_end"].split(":"))
        total_clock = (we_h * 60 + we_m) - (ws_h * 60 + ws_m)
        contract_min = total_clock - cfg["break_min"]

    # Day boundary in UTC
    day_start_utc = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz).astimezone(timezone.utc)
    day_end_utc   = day_start_utc + timedelta(days=1)

    # Sessions overlapping this day
    sessions = conn.execute(
        "SELECT * FROM sessions WHERE start_ts < ? AND (end_ts IS NULL OR end_ts > ?)",
        (
            day_end_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            day_start_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        )
    ).fetchall()

    ws_utc, we_utc = _work_window_utc(d, cfg["work_start"], cfg["work_end"], tz)

    logged_in_window  = 0.0
    logged_out_window = 0.0

    sess_list = []
    for s in sessions:
        s_start = _parse_ts(s["start_ts"])
        s_end   = _parse_ts(s["end_ts"]) if s["end_ts"] else now_utc

        # Clip to this day
        clipped_start = max(s_start, day_start_utc)
        clipped_end   = min(s_end,   day_end_utc)
        if clipped_end <= clipped_start:
            continue

        total_s = (clipped_end - clipped_start).total_seconds() / 60

        if is_workday:
            in_win = _overlap_seconds(clipped_start, clipped_end, ws_utc, we_utc) / 60
        else:
            in_win = 0.0

        out_win = total_s - in_win
        logged_in_window  += in_win
        logged_out_window += out_win
        sess_list.append(dict(s))

    # Manual entries
    entries = conn.execute(
        "SELECT * FROM manual_entries WHERE date=?", (d.isoformat(),)
    ).fetchall()

    vacation_min = sum(e["hours"] * 60 for e in entries if e["kind"] == "vacation")
    sick_min     = sum(e["hours"] * 60 for e in entries if e["kind"] == "sick")
    ot_taken_min = sum(e["hours"] * 60 for e in entries if e["kind"] == "ot_taken")

    ot_earned_min = logged_out_window

    # On a holiday, the full contracted day credit is earned even with no session
    holiday_credit = contract_min if is_holiday else 0

    day_credit_min = (
        logged_in_window + vacation_min + sick_min + ot_taken_min + holiday_credit
    )
    day_delta_min = day_credit_min - contract_min

    return DaySummary(
        date=d,
        is_workday=is_workday,
        is_holiday=is_holiday,
        contract_min=contract_min,
        logged_in_window_min=logged_in_window,
        logged_out_window_min=logged_out_window,
        ot_earned_min=ot_earned_min,
        vacation_min=vacation_min,
        sick_min=sick_min,
        ot_taken_min=ot_taken_min,
        day_credit_min=day_credit_min,
        day_delta_min=day_delta_min,
        sessions=sess_list,
    )


def range_summary(conn, start: date_type, end: date_type) -> RangeSummary:
    days = []
    current = start
    while current <= end:
        days.append(day_summary(conn, current))
        current += timedelta(days=1)

    return RangeSummary(
        start=start,
        end=end,
        total_logged_min=sum(d.logged_in_window_min + d.logged_out_window_min for d in days),
        ot_earned_min=sum(d.ot_earned_min for d in days),
        ot_taken_min=sum(d.ot_taken_min  for d in days),
        vacation_min=sum(d.vacation_min   for d in days),
        sick_min=sum(d.sick_min           for d in days),
        contract_min=sum(d.contract_min   for d in days),
        day_credit_min=sum(d.day_credit_min for d in days),
        day_delta_min=sum(d.day_delta_min   for d in days),
        days=days,
    )


def ot_balance(conn, as_of: Optional[date_type] = None) -> float:
    """Returns OT balance in hours (earned − taken)."""
    if as_of is None:
        as_of = datetime.now(ZoneInfo(get_setting(conn, "timezone", "Europe/Amsterdam"))).date()

    now_utc = datetime.now(timezone.utc)
    tz = ZoneInfo(get_setting(conn, "timezone", "Europe/Amsterdam"))

    sessions = conn.execute("SELECT start_ts, end_ts FROM sessions").fetchall()
    cfg = _get_config(conn)
    holidays_set = {
        r["date"] for r in conn.execute("SELECT date FROM holidays").fetchall()
    }

    total_ot_seconds = 0.0
    for s in sessions:
        s_start = _parse_ts(s["start_ts"])
        s_end   = _parse_ts(s["end_ts"]) if s["end_ts"] else now_utc
        # Only count up to as_of
        cutoff = datetime(as_of.year, as_of.month, as_of.day, 23, 59, 59, tzinfo=tz).astimezone(timezone.utc)
        s_end = min(s_end, cutoff)
        if s_end <= s_start:
            continue

        # Accumulate OT seconds day by day
        current_day = s_start.astimezone(tz).date()
        end_day     = s_end.astimezone(tz).date()
        while current_day <= end_day:
            day_start_utc = datetime(current_day.year, current_day.month, current_day.day, 0, 0, 0, tzinfo=tz).astimezone(timezone.utc)
            day_end_utc   = day_start_utc + timedelta(days=1)
            seg_s = max(s_start, day_start_utc)
            seg_e = min(s_end,   day_end_utc)
            if seg_e <= seg_s:
                current_day += timedelta(days=1)
                continue

            is_weekend = current_day.weekday() >= 5
            is_holiday = current_day.isoformat() in holidays_set
            weekday_abbr = _WEEKDAY_ABBR[current_day.weekday()]
            is_workday = weekday_abbr in cfg["work_days"] and not is_holiday

            if not is_workday:
                total_ot_seconds += (seg_e - seg_s).total_seconds()
            else:
                ws_utc, we_utc = _work_window_utc(current_day, cfg["work_start"], cfg["work_end"], tz)
                # Before work
                if seg_s < ws_utc:
                    total_ot_seconds += (min(seg_e, ws_utc) - seg_s).total_seconds()
                # After work
                if seg_e > we_utc:
                    total_ot_seconds += (seg_e - max(seg_s, we_utc)).total_seconds()

            current_day += timedelta(days=1)

    ot_earned_h = total_ot_seconds / 3600

    ot_taken_h = conn.execute(
        "SELECT COALESCE(SUM(hours),0) FROM manual_entries WHERE kind='ot_taken'"
    ).fetchone()[0]

    return round(ot_earned_h - ot_taken_h, 2)


def vacation_balances(conn, year: int) -> dict:
    """Returns {category_id: remaining_hours} for the given year."""
    cats = conn.execute(
        "SELECT id, name FROM vacation_categories WHERE active=1"
    ).fetchall()

    result = {}
    for cat in cats:
        granted = conn.execute(
            "SELECT COALESCE(SUM(hours_granted),0) FROM vacation_grants "
            "WHERE category_id=? AND year=?",
            (cat["id"], year)
        ).fetchone()[0]

        used = conn.execute(
            "SELECT COALESCE(SUM(hours),0) FROM manual_entries "
            "WHERE kind='vacation' AND vacation_category_id=? "
            "AND strftime('%Y', date)=?",
            (cat["id"], str(year))
        ).fetchone()[0]

        result[cat["id"]] = {
            "name": cat["name"],
            "granted": granted,
            "used": used,
            "remaining": round(granted - used, 2),
        }
    return result


def weekday_averages(conn, start: date_type, end: date_type) -> dict:
    """Returns per-weekday average worked minutes."""
    totals  = {d: 0.0 for d in range(7)}
    counts  = {d: 0   for d in range(7)}

    current = start
    while current <= end:
        ds = day_summary(conn, current)
        wd = current.weekday()
        totals[wd] += ds.logged_in_window_min + ds.logged_out_window_min
        counts[wd] += 1
        current += timedelta(days=1)

    return {
        _WEEKDAY_ABBR[wd]: round(totals[wd] / counts[wd], 1) if counts[wd] else 0.0
        for wd in range(7)
    }


def flagged_sessions(conn) -> list:
    return conn.execute(
        "SELECT * FROM sessions WHERE ot_flagged=1 ORDER BY start_ts DESC"
    ).fetchall()
