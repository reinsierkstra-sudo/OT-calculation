"""
Phase 6 — Holiday seeding

Seeds the holidays table from python-holidays for the configured country.
Never overwrites source='manual' rows.
"""

from datetime import date
from .db import get_connection, get_setting, init_db


def seed_holidays(conn, year: int, country: str) -> int:
    try:
        import holidays as hol_lib
    except ImportError:
        print("python-holidays not installed.")
        return 0

    country_holidays = hol_lib.country_holidays(country, years=year)
    added = 0
    for d, name in country_holidays.items():
        date_str = d.isoformat()
        existing = conn.execute(
            "SELECT source FROM holidays WHERE date=?", (date_str,)
        ).fetchone()
        if existing and existing["source"] == "manual":
            continue
        conn.execute(
            "INSERT OR REPLACE INTO holidays(date, name, source) VALUES (?,?,?)",
            (date_str, name, "auto")
        )
        added += 1
    conn.commit()
    return added


def seed_for_configured_years(conn) -> None:
    country    = get_setting(conn, "holidays_country", "NL")
    span       = int(get_setting(conn, "seed_years_around_current", "2"))
    this_year  = date.today().year
    total = 0
    for yr in range(this_year - span, this_year + span + 1):
        n = seed_holidays(conn, yr, country)
        total += n
        print(f"  Seeded {n} holidays for {yr} ({country})")
    print(f"Total: {total} holidays seeded.")


def main() -> None:
    init_db()
    conn = get_connection()
    seed_for_configured_years(conn)
    conn.close()


if __name__ == "__main__":
    main()
