"""
Entry point — start the LaptopHours dashboard.

    python run.py
"""

from app.db import init_db, get_connection
from app.holidays_seed import seed_for_configured_years
from app.server import app
from app.db import get_setting


def main():
    init_db()
    conn = get_connection()
    seed_for_configured_years(conn)
    host = get_setting(conn, "server_host", "127.0.0.1")
    port = int(get_setting(conn, "server_port", "5000"))
    conn.close()

    print(f"LaptopHours running at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
