"""
Phase 1 — Harvester

Reads two Windows Event Log channels via pywin32 and writes raw_events.
Run via:  python -m app.harvester
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .db import get_connection, get_setting

LOG_PATH = Path(__file__).parent.parent / "data" / "harvest.log"

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def _parse_ts(ts_str: str) -> str:
    """Convert a Win32 SYSTEMTIME-style string to ISO 8601 UTC."""
    # win32evtlog returns datetime objects for TimeCreated
    if isinstance(ts_str, datetime):
        dt = ts_str
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return str(ts_str)


def _xml_field(xml: str, field: str) -> str:
    """Extract a named field value from EventData XML."""
    import re
    pattern = rf'<Data Name="{re.escape(field)}">(.*?)</Data>'
    m = re.search(pattern, xml or "", re.DOTALL)
    return m.group(1).strip() if m else ""


def harvest(conn) -> dict:
    try:
        import win32evtlog
        import win32evtlogutil
        import pywintypes
    except ImportError:
        print("pywin32 not available — harvester requires Windows.")
        log.warning("pywin32 not available; harvest skipped.")
        return {"vpn_connect": 0, "vpn_disconnect": 0, "office_wlan": 0}

    profile_name = get_setting(conn, "network_profile_name", "nucmed.lan")
    office_ssid  = get_setting(conn, "office_ssid", "NucMed-Corp")
    stitch_gap   = int(get_setting(conn, "stitch_gap_seconds", "180"))

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    counts = {"vpn_connect": 0, "vpn_disconnect": 0, "office_wlan": 0}

    # ── Channel A: NetworkProfile ──────────────────────────────────────────
    channel_a = "Microsoft-Windows-NetworkProfile/Operational"
    wm_a = conn.execute(
        "SELECT last_record_no FROM harvester_watermark WHERE channel=?",
        (channel_a,)
    ).fetchone()
    start_record_a = (wm_a["last_record_no"] + 1) if wm_a else 0
    max_record_a = start_record_a - 1

    try:
        query_a = (
            f"*[System[(EventID=10000 or EventID=10001)] "
            f"and System[EventRecordID >= {start_record_a}]]"
        )
        handle_a = win32evtlog.EvtQuery(
            channel_a, win32evtlog.EvtQueryForwardDirection, query_a
        )
        while True:
            events = win32evtlog.EvtNext(handle_a, 50)
            if not events:
                break
            for evt in events:
                try:
                    xml = win32evtlog.EvtRender(evt, win32evtlog.EvtRenderEventXml)
                    record_no = int(_xml_field(xml, "EventRecordID") or "0")
                    # Fallback: parse record number from XML attributes
                    import re
                    if not record_no:
                        m = re.search(r'EventRecordID>(\d+)<', xml)
                        record_no = int(m.group(1)) if m else 0

                    name = _xml_field(xml, "Name")
                    if name.lower() != profile_name.lower():
                        continue

                    # EventID from XML
                    m_id = re.search(r'<EventID>(\d+)</EventID>', xml)
                    event_id = int(m_id.group(1)) if m_id else 0

                    m_ts = re.search(r"SystemTime='([^']+)'", xml)
                    ts_utc = m_ts.group(1).replace("T", "T").rstrip("Z") + "Z" if m_ts else now_utc

                    kind = "vpn_connect" if event_id == 10000 else "vpn_disconnect"

                    conn.execute(
                        "INSERT OR IGNORE INTO raw_events"
                        "(ts_utc, channel, event_id, kind, record_number, raw_xml)"
                        "VALUES (?,?,?,?,?,?)",
                        (ts_utc, channel_a, event_id, kind, record_no, xml)
                    )
                    counts[kind] += 1
                    if record_no > max_record_a:
                        max_record_a = record_no
                except Exception as e:
                    log.error("channel_a event error: %s", e)
    except Exception as e:
        log.error("channel_a query error: %s", e)

    if max_record_a >= start_record_a:
        conn.execute(
            "INSERT OR REPLACE INTO harvester_watermark(channel, last_record_no, last_run_utc)"
            "VALUES (?,?,?)",
            (channel_a, max_record_a, now_utc)
        )

    # ── Channel B: WLAN-AutoConfig ─────────────────────────────────────────
    channel_b = "Microsoft-Windows-WLAN-AutoConfig/Operational"
    wm_b = conn.execute(
        "SELECT last_record_no FROM harvester_watermark WHERE channel=?",
        (channel_b,)
    ).fetchone()
    start_record_b = (wm_b["last_record_no"] + 1) if wm_b else 0
    max_record_b = start_record_b - 1

    try:
        query_b = (
            f"*[System[EventID=8002]"
            f" and System[EventRecordID >= {start_record_b}]]"
        )
        handle_b = win32evtlog.EvtQuery(
            channel_b, win32evtlog.EvtQueryForwardDirection, query_b
        )
        while True:
            events = win32evtlog.EvtNext(handle_b, 50)
            if not events:
                break
            for evt in events:
                try:
                    xml = win32evtlog.EvtRender(evt, win32evtlog.EvtRenderEventXml)
                    import re
                    ssid = _xml_field(xml, "SSID") or _xml_field(xml, "ProfileName")
                    if ssid.lower() != office_ssid.lower():
                        continue

                    m = re.search(r'EventRecordID>(\d+)<', xml)
                    record_no = int(m.group(1)) if m else 0

                    m_ts = re.search(r"SystemTime='([^']+)'", xml)
                    ts_utc = m_ts.group(1).rstrip("Z") + "Z" if m_ts else now_utc

                    conn.execute(
                        "INSERT OR IGNORE INTO raw_events"
                        "(ts_utc, channel, event_id, kind, record_number, raw_xml)"
                        "VALUES (?,?,?,?,?,?)",
                        (ts_utc, channel_b, 8002, "office_wlan", record_no, xml)
                    )
                    counts["office_wlan"] += 1
                    if record_no > max_record_b:
                        max_record_b = record_no
                except Exception as e:
                    log.error("channel_b event error: %s", e)
    except Exception as e:
        log.error("channel_b query error: %s", e)

    if max_record_b >= start_record_b:
        conn.execute(
            "INSERT OR REPLACE INTO harvester_watermark(channel, last_record_no, last_run_utc)"
            "VALUES (?,?,?)",
            (channel_b, max_record_b, now_utc)
        )

    conn.commit()
    return counts


def main() -> None:
    from .db import init_db
    init_db()
    conn = get_connection()
    counts = harvest(conn)
    conn.close()

    total = sum(counts.values())
    print(
        f"Harvested {total} new events "
        f"({counts['vpn_connect']} vpn_connect, "
        f"{counts['vpn_disconnect']} vpn_disconnect, "
        f"{counts['office_wlan']} office_wlan)."
    )

    # Trigger sessionizer after harvest
    from .sessionizer import sessionize
    conn = get_connection()
    sessionize(conn)
    conn.close()


if __name__ == "__main__":
    main()
