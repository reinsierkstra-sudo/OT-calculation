"""
Phase 5 — Flask dashboard server

Run via:  python -m app.server
"""

from datetime import datetime, timedelta, timezone, date as date_type
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from .db import get_connection, get_setting, init_db
from .calculator import (
    day_summary,
    flagged_sessions,
    ot_balance,
    range_summary,
    vacation_balances,
    weekday_averages,
    _parse_ts,
    _work_window_utc,
    _overlap_seconds,
    _WEEKDAY_ABBR,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "laptophours-local-secret"


# ── Helpers ────────────────────────────────────────────────────────────────

def _tz(conn) -> ZoneInfo:
    return ZoneInfo(get_setting(conn, "timezone", "Europe/Amsterdam"))


def _today(conn) -> date_type:
    return datetime.now(_tz(conn)).date()


def _format_duration(minutes: float | None) -> str:
    if minutes is None:
        return "—"
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h}h {m:02d}m"


def _enrich_session(s, conn, tz: ZoneInfo, work_start: str, work_end: str):
    """Add display fields to a session row dict."""
    now_utc = datetime.now(timezone.utc)
    d = dict(s)
    s_start = _parse_ts(d["start_ts"])
    s_end   = _parse_ts(d["end_ts"]) if d["end_ts"] else now_utc
    d["start_local"]   = s_start.astimezone(tz).strftime("%d/%m %H:%M")
    d["end_local"]     = (
        s_end.astimezone(tz).strftime("%d/%m %H:%M") if d["end_ts"] else None
    )
    dur = (s_end - s_start).total_seconds() / 60
    d["duration_str"]  = _format_duration(dur)

    # In-window / OT split (use session's calendar date for work window)
    local_start = s_start.astimezone(tz)
    day = local_start.date()
    ws_utc, we_utc = _work_window_utc(day, work_start, work_end, tz)
    in_win = _overlap_seconds(s_start, s_end, ws_utc, we_utc) / 60
    d["in_window_min"] = in_win
    d["ot_min"]        = dur - in_win
    return d


# ── Overview ───────────────────────────────────────────────────────────────

@app.route("/")
def overview():
    conn = get_connection()
    tz   = _tz(conn)
    today = _today(conn)
    work_start = get_setting(conn, "work_start", "08:30")
    work_end   = get_setting(conn, "work_end",   "17:00")

    ot_bal = ot_balance(conn)

    # This week Mon→today
    weekday = today.weekday()
    week_start = today - timedelta(days=weekday)
    rs = range_summary(conn, week_start, today)
    week_delta = round(rs.day_delta_min / 60, 2)

    # Today summary
    ds = day_summary(conn, today)
    today_logged_h = round((ds.logged_in_window_min + ds.logged_out_window_min) / 60, 1)

    # Flagged
    flagged = flagged_sessions(conn)
    flagged_count = len(flagged)

    # Vacation balances
    current_year = today.year
    vac_bal = vacation_balances(conn, current_year)

    # Open session
    open_sess_row = conn.execute(
        "SELECT * FROM sessions WHERE end_ts IS NULL ORDER BY start_ts DESC LIMIT 1"
    ).fetchone()
    open_session = None
    if open_sess_row:
        now_utc = datetime.now(timezone.utc)
        s_start = _parse_ts(open_sess_row["start_ts"])
        dur_min = (now_utc - s_start).total_seconds() / 60
        open_session = {
            "start_local": s_start.astimezone(tz).strftime("%H:%M"),
            "duration_str": _format_duration(dur_min),
            "kind": open_sess_row["kind"],
        }

    # Today's sessions
    today_sessions_raw = conn.execute(
        """SELECT * FROM sessions
           WHERE start_ts < ? AND (end_ts IS NULL OR end_ts > ?)
           ORDER BY start_ts ASC""",
        (
            (datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=tz)
             .astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")),
            (datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=tz)
             .astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")),
        )
    ).fetchall()
    today_sessions = [
        _enrich_session(s, conn, tz, work_start, work_end) for s in today_sessions_raw
    ]

    conn.close()
    return render_template(
        "overview.html",
        today=today,
        ot_balance=ot_bal,
        week_delta=week_delta,
        today_logged_h=today_logged_h,
        flagged_count=flagged_count,
        vac_balances=vac_bal,
        current_year=current_year,
        open_session=open_session,
        today_sessions=today_sessions,
    )


# ── Sessions ───────────────────────────────────────────────────────────────

@app.route("/sessions")
def sessions():
    conn = get_connection()
    tz   = _tz(conn)
    today = _today(conn)
    work_start = get_setting(conn, "work_start", "08:30")
    work_end   = get_setting(conn, "work_end",   "17:00")

    active_range  = request.args.get("range", "")
    active_flagged = bool(request.args.get("flagged"))

    # Determine date range
    if active_range == "today":
        fr = to = today
    elif active_range == "week":
        fr = today - timedelta(days=today.weekday())
        to = today
    elif active_range == "month":
        fr = today.replace(day=1)
        to = today
    else:
        fr_str = request.args.get("from", "")
        to_str = request.args.get("to", "")
        try:
            fr = date_type.fromisoformat(fr_str) if fr_str else today - timedelta(days=30)
        except ValueError:
            fr = today - timedelta(days=30)
        try:
            to = date_type.fromisoformat(to_str) if to_str else today
        except ValueError:
            to = today

    fr_utc = datetime(fr.year, fr.month, fr.day, 0, 0, 0, tzinfo=tz).astimezone(timezone.utc)
    to_utc = datetime(to.year, to.month, to.day, 23, 59, 59, tzinfo=tz).astimezone(timezone.utc)

    query = """SELECT * FROM sessions
               WHERE start_ts < ? AND (end_ts IS NULL OR end_ts > ?)"""
    params = [
        to_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        fr_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    ]
    if active_flagged:
        query += " AND ot_flagged=1"
    query += " ORDER BY start_ts DESC"

    rows = conn.execute(query, params).fetchall()
    sessions_list = [_enrich_session(s, conn, tz, work_start, work_end) for s in rows]

    total_count    = len(sessions_list)
    total_duration = sum((s["in_window_min"] + s["ot_min"]) for s in sessions_list)
    total_in_window = sum(s["in_window_min"] for s in sessions_list)
    total_ot        = sum(s["ot_min"]        for s in sessions_list)

    conn.close()
    return render_template(
        "sessions.html",
        sessions=sessions_list,
        total_count=total_count,
        total_duration_str=_format_duration(total_duration),
        total_in_window=total_in_window,
        total_ot=total_ot,
        active_range=active_range,
        active_flagged=active_flagged,
        filter_from=fr.isoformat(),
        filter_to=to.isoformat(),
    )


@app.route("/sessions/<int:id>/confirm", methods=["POST"])
def session_confirm(id: int):
    conn = get_connection()
    conn.execute("UPDATE sessions SET ot_flagged=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Session flag dismissed.", "success")
    return redirect(request.referrer or url_for("sessions"))


@app.route("/sessions/<int:id>/delete", methods=["POST"])
def session_delete(id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Session deleted.", "success")
    return redirect(request.referrer or url_for("sessions"))


# ── Aggregates ─────────────────────────────────────────────────────────────

@app.route("/aggregates")
def aggregates():
    conn  = get_connection()
    tz    = _tz(conn)
    today = _today(conn)
    work_start = get_setting(conn, "work_start", "08:30")
    work_end   = get_setting(conn, "work_end",   "17:00")

    active_range = request.args.get("range", "month")

    if active_range == "week":
        fr = today - timedelta(days=today.weekday())
        to = today
    elif active_range == "year":
        fr = today.replace(month=1, day=1)
        to = today
    else:
        active_range = "month"
        fr = today.replace(day=1)
        to = today

    rs = range_summary(conn, fr, to)

    # Chart data
    chart_labels   = []
    chart_credit   = []
    chart_ot       = []
    chart_contract = []
    for ds in rs.days:
        chart_labels.append(ds.date.strftime("%d/%m"))
        chart_credit.append(round(ds.logged_in_window_min / 60, 2))
        chart_ot.append(round(ds.ot_earned_min / 60, 2))
        chart_contract.append(round(ds.contract_min / 60, 2))

    # Weekly rollup
    weekly = {}
    for ds in rs.days:
        # ISO week
        iso = ds.date.isocalendar()
        key = (iso.year, iso.week)
        if key not in weekly:
            weekly[key] = {
                "year": iso.year, "week_nr": iso.week,
                "contract_h": 0.0, "logged_h": 0.0,
                "ot_earned_h": 0.0, "ot_taken_h": 0.0,
                "vacation_h": 0.0, "sick_h": 0.0, "delta_h": 0.0,
            }
        weekly[key]["contract_h"]  += ds.contract_min / 60
        weekly[key]["logged_h"]    += (ds.logged_in_window_min + ds.logged_out_window_min) / 60
        weekly[key]["ot_earned_h"] += ds.ot_earned_min / 60
        weekly[key]["ot_taken_h"]  += ds.ot_taken_min / 60
        weekly[key]["vacation_h"]  += ds.vacation_min / 60
        weekly[key]["sick_h"]      += ds.sick_min / 60
        weekly[key]["delta_h"]     += ds.day_delta_min / 60

    for w in weekly.values():
        for k in ["contract_h","logged_h","ot_earned_h","ot_taken_h","vacation_h","sick_h","delta_h"]:
            w[k] = round(w[k], 1)

    weekly_rollup = sorted(weekly.values(), key=lambda w: (w["year"], w["week_nr"]))

    # Weekday averages
    avgs = weekday_averages(conn, fr, to)
    ws_h, ws_m = map(int, work_start.split(":"))
    we_h, we_m = map(int, work_end.split(":"))
    contract_day_h = ((we_h * 60 + we_m) - (ws_h * 60 + ws_m) - int(get_setting(conn, "break_minutes", "30"))) / 60
    weekday_avgs = []
    for wd in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
        avg = avgs.get(wd, 0.0)
        c   = contract_day_h if wd not in ("Sat","Sun") else 0.0
        weekday_avgs.append({
            "day": wd, "avg_h": round(avg/60, 1),
            "contract_h": round(c, 1),
            "delta_h": round(avg/60 - c, 1),
        })

    conn.close()
    return render_template(
        "aggregates.html",
        active_range=active_range,
        chart_labels=chart_labels,
        chart_credit=chart_credit,
        chart_ot=chart_ot,
        chart_contract=chart_contract,
        weekly_rollup=weekly_rollup,
        weekday_avgs=weekday_avgs,
    )


# ── Entries ────────────────────────────────────────────────────────────────

@app.route("/entries")
def entries():
    conn  = get_connection()
    today = _today(conn)

    fr_str   = request.args.get("from", "")
    to_str   = request.args.get("to", "")
    kind_flt = request.args.get("kind", "")

    try:
        fr = date_type.fromisoformat(fr_str) if fr_str else today.replace(day=1)
    except ValueError:
        fr = today.replace(day=1)
    try:
        to = date_type.fromisoformat(to_str) if to_str else today
    except ValueError:
        to = today

    query  = "SELECT e.*, c.name as cat_name FROM manual_entries e LEFT JOIN vacation_categories c ON c.id=e.vacation_category_id WHERE e.date >= ? AND e.date <= ?"
    params: list = [fr.isoformat(), to.isoformat()]
    if kind_flt:
        query += " AND e.kind=?"
        params.append(kind_flt)
    query += " ORDER BY e.date DESC"

    rows = conn.execute(query, params).fetchall()
    entries_list = [dict(r) for r in rows]
    conn.close()

    return render_template(
        "entries.html",
        entries=entries_list,
        filter_from=fr.isoformat(),
        filter_to=to.isoformat(),
        filter_kind=kind_flt,
    )


@app.route("/entries/new", methods=["GET", "POST"])
def entry_new():
    conn  = get_connection()
    today = _today(conn)
    cats  = conn.execute("SELECT * FROM vacation_categories WHERE active=1").fetchall()

    if request.method == "POST":
        kind     = request.form["kind"]
        date_str = request.form["date"]
        hours    = float(request.form["hours"])
        start_t  = request.form.get("start_time") or None
        cat_id   = request.form.get("vacation_category_id") or None
        note     = request.form.get("note") or None
        created  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if kind == "vacation" and not cat_id:
            flash("Please select a vacation category.", "danger")
        else:
            conn.execute(
                "INSERT INTO manual_entries(kind,date,start_time,hours,vacation_category_id,note,created_at)"
                "VALUES (?,?,?,?,?,?,?)",
                (kind, date_str, start_t, hours, cat_id, note, created)
            )
            conn.commit()
            conn.close()
            flash("Entry added.", "success")
            return redirect(url_for("entries"))

    kind_default = request.args.get("kind", "vacation")
    conn.close()
    return render_template(
        "entry_form.html",
        entry=None,
        categories=cats,
        today=today.isoformat(),
        kind=kind_default,
    )


@app.route("/entries/<int:id>/edit", methods=["GET", "POST"])
def entry_edit(id: int):
    conn = get_connection()
    row  = conn.execute("SELECT * FROM manual_entries WHERE id=?", (id,)).fetchone()
    if not row:
        conn.close()
        abort(404)

    cats = conn.execute("SELECT * FROM vacation_categories WHERE active=1").fetchall()
    today = _today(conn)

    if request.method == "POST":
        kind     = request.form["kind"]
        date_str = request.form["date"]
        hours    = float(request.form["hours"])
        start_t  = request.form.get("start_time") or None
        cat_id   = request.form.get("vacation_category_id") or None
        note     = request.form.get("note") or None

        if kind == "vacation" and not cat_id:
            flash("Please select a vacation category.", "danger")
        else:
            conn.execute(
                "UPDATE manual_entries SET kind=?,date=?,start_time=?,hours=?,"
                "vacation_category_id=?,note=? WHERE id=?",
                (kind, date_str, start_t, hours, cat_id, note, id)
            )
            conn.commit()
            conn.close()
            flash("Entry updated.", "success")
            return redirect(url_for("entries"))

    conn.close()
    return render_template(
        "entry_form.html",
        entry=dict(row),
        categories=cats,
        today=today.isoformat(),
        kind=row["kind"],
    )


@app.route("/entries/<int:id>/delete", methods=["POST"])
def entry_delete(id: int):
    conn = get_connection()
    conn.execute("DELETE FROM manual_entries WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Entry deleted.", "success")
    return redirect(url_for("entries"))


# ── Settings ───────────────────────────────────────────────────────────────

@app.route("/settings")
def settings():
    conn = get_connection()
    today = _today(conn)
    current_year = today.year

    s = {
        "work_start":              get_setting(conn, "work_start",  "08:30"),
        "work_end":                get_setting(conn, "work_end",    "17:00"),
        "break_minutes":           get_setting(conn, "break_minutes", "30"),
        "contract_hours_per_week": get_setting(conn, "contract_hours_per_week", "40"),
        "ot_flag_threshold_hours": get_setting(conn, "ot_flag_threshold_hours", "4"),
    }

    vacation_cats = conn.execute("SELECT * FROM vacation_categories ORDER BY name").fetchall()

    vacation_grants = conn.execute(
        "SELECT g.*, c.name as cat_name FROM vacation_grants g "
        "JOIN vacation_categories c ON c.id=g.category_id ORDER BY g.year DESC, c.name"
    ).fetchall()
    vacation_grants = [dict(g) for g in vacation_grants]

    holidays = conn.execute(
        "SELECT * FROM holidays ORDER BY date"
    ).fetchall()

    conn.close()
    return render_template(
        "settings.html",
        s=s,
        vacation_cats=vacation_cats,
        vacation_grants=vacation_grants,
        holidays=holidays,
        current_year=current_year,
    )


@app.route("/settings/work", methods=["POST"])
def settings_work():
    conn = get_connection()
    for key in ("work_start", "work_end", "break_minutes", "contract_hours_per_week"):
        val = request.form.get(key)
        if val is not None:
            conn.execute(
                "INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)", (key, val)
            )
    conn.commit()
    conn.close()
    flash("Work settings saved.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/vacation-categories", methods=["POST"])
def settings_vacation_categories():
    conn   = get_connection()
    action = request.form.get("action")
    if action == "add":
        name = request.form.get("name", "").strip()
        if name:
            try:
                conn.execute("INSERT INTO vacation_categories(name) VALUES (?)", (name,))
                conn.commit()
                flash(f"Category '{name}' added.", "success")
            except Exception:
                flash("Category name already exists.", "danger")
    elif action == "rename":
        cat_id = request.form.get("id")
        name   = request.form.get("name", "").strip()
        active = int(request.form.get("active", "1"))
        if name:
            conn.execute(
                "UPDATE vacation_categories SET name=?, active=? WHERE id=?",
                (name, active, cat_id)
            )
            conn.commit()
            flash("Category updated.", "success")
    conn.close()
    return redirect(url_for("settings"))


@app.route("/settings/vacation-grants", methods=["POST"])
def settings_vacation_grants():
    conn   = get_connection()
    action = request.form.get("action")
    if action == "add":
        conn.execute(
            "INSERT OR REPLACE INTO vacation_grants(category_id,year,hours_granted,note)"
            "VALUES (?,?,?,?)",
            (
                request.form["category_id"],
                int(request.form["year"]),
                float(request.form["hours_granted"]),
                request.form.get("note") or None,
            )
        )
        conn.commit()
        flash("Grant added.", "success")
    elif action == "edit":
        conn.execute(
            "UPDATE vacation_grants SET year=?,hours_granted=?,note=? WHERE id=?",
            (
                int(request.form["year"]),
                float(request.form["hours_granted"]),
                request.form.get("note") or None,
                request.form["id"],
            )
        )
        conn.commit()
        flash("Grant updated.", "success")
    conn.close()
    return redirect(url_for("settings"))


@app.route("/settings/ot-flag", methods=["POST"])
def settings_ot_flag():
    conn = get_connection()
    val  = request.form.get("ot_flag_threshold_hours")
    if val:
        conn.execute(
            "INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)",
            ("ot_flag_threshold_hours", val)
        )
        conn.commit()
    conn.close()
    flash("OT flag threshold saved.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/holidays/reseed", methods=["POST"])
def settings_holidays_reseed():
    conn    = get_connection()
    year    = int(request.form.get("year", datetime.now().year))
    country = get_setting(conn, "holidays_country", "NL")
    from .holidays_seed import seed_holidays
    n = seed_holidays(conn, year, country)
    conn.close()
    flash(f"Seeded {n} holidays for {year}.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/holidays/add", methods=["POST"])
def settings_holidays_add():
    conn = get_connection()
    d    = request.form.get("date", "")
    name = request.form.get("name", "").strip()
    if d and name:
        conn.execute(
            "INSERT OR REPLACE INTO holidays(date,name,source) VALUES (?,?,'manual')",
            (d, name)
        )
        conn.commit()
        flash(f"Holiday {d} added.", "success")
    conn.close()
    return redirect(url_for("settings"))


# ── API ────────────────────────────────────────────────────────────────────

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    try:
        from .harvester  import harvest
        from .sessionizer import sessionize
        from .holidays_seed import seed_for_configured_years

        conn = get_connection()
        counts = harvest(conn)
        n_sess = sessionize(conn)
        conn.close()

        flash(
            f"Refreshed: {sum(counts.values())} new events, {n_sess} sessions rebuilt.",
            "success"
        )
    except Exception as e:
        flash(f"Refresh error: {e}", "danger")
    return redirect(request.referrer or url_for("overview"))


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    init_db()
    from .holidays_seed import seed_for_configured_years
    conn = get_connection()
    seed_for_configured_years(conn)
    conn.close()

    conn = get_connection()
    host = get_setting(conn, "server_host", "127.0.0.1")
    port = int(get_setting(conn, "server_port", "5000"))
    conn.close()

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
