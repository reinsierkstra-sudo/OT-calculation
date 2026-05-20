"""
Phase 1 — Harvester

Reads two Windows Event Log channels via pywin32 and writes raw_events.
Run via:  python -m app.harvester
"""

import logging
import re
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

# Windows Event XML uses single-quoted attributes on this platform:
#   <TimeCreated SystemTime='2024-01-15T08:30:00.123456789Z'/>
#   <Data Name='Name'>nucmed.lan</Data>
# Regexes accept both single and double quotes to be safe.
_RE_SYSTEM_TIME  = re.compile(r"SystemTime=['\"]([^'\"]+)['\"]")
_RE_RECORD_ID    = re.compile(r'<EventRecordID>(\d+)</EventRecordID>')
_RE_EVENT_ID     = re.compile(r'<EventID(?:\s[^>]*)?>(\d+)</EventID>')
# EventData fields: <Data Name='FieldName'>value</Data>
_RE_DATA_FIELD   = re.compile(r"<Data Name=['\"]([^'\"]+)['\"]>(.*?)</Data>", re.DOTALL)


def _xml_system_time(xml: str, fallback: str) -> str:
    """Extract SystemTime and normalise to ISO 8601 UTC string."""
    m = _RE_SYSTEM_TIME.search(xml)
    if not m:
        return fallback
    raw = m.group(1)
    # Windows may give nanoseconds: 2024-01-15T08:30:00.123456789Z
    # Truncate to microseconds so strptime is happy, then re-format.
    raw = raw.rstrip("Z")
    if "." in raw:
        base, frac = raw.split(".", 1)
        frac = frac[:6]          # microseconds max
        raw = f"{base}.{frac}"
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S")
    return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _xml_record_id(xml: str) -> int:
    m = _RE_RECORD_ID.search(xml)
    return int(m.group(1)) if m else 0


def _xml_event_id(xml: str) -> int:
    m = _RE_EVENT_ID.search(xml)
    return int(m.group(1)) if m else 0


def _xml_data_fields(xml: str) -> dict:
    """Return all EventData <Data Name="..."> fields as a dict."""
    return {m.group(1): m.group(2).strip() for m in _RE_DATA_FIELD.finditer(xml)}


def harvest(conn) -> dict:
    try:
        import win32evtlog
    except ImportError:
        print("pywin32 not available — harvester requires Windows.")
        log.warning("pywin32 not available; harvest skipped.")
        return {"vpn_connect": 0, "vpn_disconnect": 0, "office_wlan": 0}

    profile_name = get_setting(conn, "network_profile_name", "nucmed.lan")
    office_ssid  = get_setting(conn, "office_ssid", "NucMed-Corp")

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    counts  = {"vpn_connect": 0, "vpn_disconnect": 0, "office_wlan": 0}

    # ── Channel A: NetworkProfile/Operational ─────────────────────────────
    channel_a = "Microsoft-Windows-NetworkProfile/Operational"
    wm_a = conn.execute(
        "SELECT last_record_no FROM harvester_watermark WHERE channel=?",
        (channel_a,)
    ).fetchone()
    start_a   = (wm_a["last_record_no"] + 1) if wm_a else 0
    max_rec_a = start_a - 1

    try:
        xpath_a = (
            f"*[System[(EventID=10000 or EventID=10001)]"
            f" and System[EventRecordID >= {start_a}]]"
        )
        handle_a = win32evtlog.EvtQuery(
            channel_a, win32evtlog.EvtQueryForwardDirection, xpath_a
        )
        while True:
            batch = win32evtlog.EvtNext(handle_a, 50)
            if not batch:
                break
            for evt in batch:
                try:
                    xml       = win32evtlog.EvtRender(evt, win32evtlog.EvtRenderEventXml)
                    rec_no    = _xml_record_id(xml)
                    event_id  = _xml_event_id(xml)
                    fields    = _xml_data_fields(xml)
                    ts_utc    = _xml_system_time(xml, now_utc)

                    # Confirm this is our target network profile
                    name = fields.get("Name", "")
                    if name.lower() != profile_name.lower():
                        continue

                    kind = "vpn_connect" if event_id == 10000 else "vpn_disconnect"

                    conn.execute(
                        "INSERT OR IGNORE INTO raw_events"
                        "(ts_utc, channel, event_id, kind, record_number, raw_xml)"
                        " VALUES (?,?,?,?,?,?)",
                        (ts_utc, channel_a, event_id, kind, rec_no, xml)
                    )
                    counts[kind] += 1
                    if rec_no > max_rec_a:
                        max_rec_a = rec_no

                except Exception as exc:
                    log.error("channel_a event parse error: %s", exc)

    except Exception as exc:
        log.error("channel_a query failed: %s", exc)

    if max_rec_a >= start_a:
        conn.execute(
            "INSERT OR REPLACE INTO harvester_watermark(channel, last_record_no, last_run_utc)"
            " VALUES (?,?,?)",
            (channel_a, max_rec_a, now_utc)
        )

    # ── Channel B: WLAN-AutoConfig/Operational ────────────────────────────
    channel_b = "Microsoft-Windows-WLAN-AutoConfig/Operational"
    wm_b = conn.execute(
        "SELECT last_record_no FROM harvester_watermark WHERE channel=?",
        (channel_b,)
    ).fetchone()
    start_b   = (wm_b["last_record_no"] + 1) if wm_b else 0
    max_rec_b = start_b - 1

    try:
        xpath_b = (
            f"*[System[EventID=8002]"
            f" and System[EventRecordID >= {start_b}]]"
        )
        handle_b = win32evtlog.EvtQuery(
            channel_b, win32evtlog.EvtQueryForwardDirection, xpath_b
        )
        while True:
            batch = win32evtlog.EvtNext(handle_b, 50)
            if not batch:
                break
            for evt in batch:
                try:
                    xml      = win32evtlog.EvtRender(evt, win32evtlog.EvtRenderEventXml)
                    rec_no   = _xml_record_id(xml)
                    fields   = _xml_data_fields(xml)
                    ts_utc   = _xml_system_time(xml, now_utc)

                    # WLAN-AutoConfig event 8002 carries the SSID in various field names
                    ssid = (
                        fields.get("SSID")
                        or fields.get("ProfileName")
                        or fields.get("InterfaceDescription")
                        or ""
                    )
                    if ssid.lower() != office_ssid.lower():
                        continue

                    conn.execute(
                        "INSERT OR IGNORE INTO raw_events"
                        "(ts_utc, channel, event_id, kind, record_number, raw_xml)"
                        " VALUES (?,?,?,?,?,?)",
                        (ts_utc, channel_b, 8002, "office_wlan", rec_no, xml)
                    )
                    counts["office_wlan"] += 1
                    if rec_no > max_rec_b:
                        max_rec_b = rec_no

                except Exception as exc:
                    log.error("channel_b event parse error: %s", exc)

    except Exception as exc:
        log.error("channel_b query failed: %s", exc)

    if max_rec_b >= start_b:
        conn.execute(
            "INSERT OR REPLACE INTO harvester_watermark(channel, last_record_no, last_run_utc)"
            " VALUES (?,?,?)",
            (channel_b, max_rec_b, now_utc)
        )

    conn.commit()
    return counts


def diagnose(conn) -> None:
    """Print a diagnostic report to stdout — useful when no data appears."""
    try:
        import win32evtlog
    except ImportError:
        print("[ERROR] pywin32 not installed. Run: pip install pywin32")
        return

    profile_name = get_setting(conn, "network_profile_name", "nucmed.lan")
    office_ssid  = get_setting(conn, "office_ssid", "NucMed-Corp")

    print(f"Looking for network profile : '{profile_name}'")
    print(f"Looking for office SSID     : '{office_ssid}'")
    print()

    for channel, xpath, label, name_field in [
        (
            "Microsoft-Windows-NetworkProfile/Operational",
            "*[System[(EventID=10000 or EventID=10001)]]",
            "NetworkProfile (connect/disconnect)",
            "Name",
        ),
        (
            "Microsoft-Windows-WLAN-AutoConfig/Operational",
            "*[System[EventID=8002]]",
            "WLAN-AutoConfig (office WiFi)",
            "SSID",
        ),
    ]:
        print(f"── {label}")
        print(f"   Channel : {channel}")
        try:
            handle = win32evtlog.EvtQuery(
                channel, win32evtlog.EvtQueryReverseDirection, xpath
            )
            # Pull up to 50 events to collect all unique name/SSID values
            batch = win32evtlog.EvtNext(handle, 50)
            if not batch:
                print("   Result  : NO events found in this channel")
            else:
                print(f"   Result  : {len(batch)} event(s) scanned")

                # Show parsed details of first 3
                for evt in batch[:3]:
                    xml    = win32evtlog.EvtRender(evt, win32evtlog.EvtRenderEventXml)
                    rec_no = _xml_record_id(xml)
                    ev_id  = _xml_event_id(xml)
                    ts     = _xml_system_time(xml, "?")
                    fields = _xml_data_fields(xml)
                    print(f"     RecordID={rec_no}  EventID={ev_id}  Time={ts}")
                    print(f"     Fields  : {dict(list(fields.items())[:8])}")

                # Collect all unique values for the key name field
                seen = set()
                for evt in batch:
                    xml    = win32evtlog.EvtRender(evt, win32evtlog.EvtRenderEventXml)
                    fields = _xml_data_fields(xml)
                    # Try multiple candidate field names
                    for candidate in (name_field, "Name", "SSID", "ProfileName",
                                      "InterfaceDescription", "Description"):
                        val = fields.get(candidate, "")
                        if val:
                            seen.add(f"{candidate}='{val}'")
                            break

                print(f"   All unique name/SSID values found in these events:")
                for v in sorted(seen):
                    print(f"     {v}")

        except Exception as exc:
            print(f"   [ERROR] Cannot read channel: {exc}")
        print()


def main() -> None:
    from .db import init_db
    init_db()
    conn = get_connection()

    import sys
    if "--diagnose" in sys.argv:
        diagnose(conn)
        conn.close()
        return

    counts = harvest(conn)
    conn.close()

    total = sum(counts.values())
    print(
        f"Harvested {total} new events "
        f"({counts['vpn_connect']} vpn_connect, "
        f"{counts['vpn_disconnect']} vpn_disconnect, "
        f"{counts['office_wlan']} office_wlan)."
    )

    from .sessionizer import sessionize
    conn = get_connection()
    n = sessionize(conn)
    conn.close()
    print(f"Sessionizer: {n} sessions rebuilt.")


if __name__ == "__main__":
    main()
