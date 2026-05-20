"""
Entry point — start the LaptopHours dashboard.

    python run.py            # start normally (harvests on launch)
    python run.py --diagnose # print Event Log diagnostic and exit
"""

import sys

from app.db import init_db, get_connection, get_setting
from app.holidays_seed import seed_for_configured_years
from app.server import app


def main():
    init_db()

    conn = get_connection()
    seed_for_configured_years(conn)
    conn.close()

    # Diagnostic mode — print what the harvester can see and exit
    if "--diagnose" in sys.argv:
        from app.harvester import diagnose
        conn = get_connection()
        diagnose(conn)
        conn.close()
        return

    # Harvest on startup so the dashboard has fresh data immediately
    print("Harvesting Event Log data...")
    try:
        from app.harvester import harvest
        from app.sessionizer import sessionize
        conn = get_connection()
        counts = harvest(conn)
        n_sess = sessionize(conn)
        conn.close()
        total = sum(counts.values())
        print(
            f"  {total} new events "
            f"({counts['vpn_connect']} connect, "
            f"{counts['vpn_disconnect']} disconnect, "
            f"{counts['office_wlan']} office_wlan), "
            f"{n_sess} sessions rebuilt."
        )
    except Exception as exc:
        print(f"  Harvest skipped: {exc}")

    conn = get_connection()
    host = get_setting(conn, "server_host", "127.0.0.1")
    port = int(get_setting(conn, "server_port", "5000"))
    conn.close()

    print(f"LaptopHours running at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
