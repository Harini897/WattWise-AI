import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "database" / "wattwise.db"

if not DB_PATH.exists():
    raise SystemExit(f"Database not found: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def section(title):
    print(f"\n{'=' * 55}")
    print(title)
    print("=" * 55)

try:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    section("WATTWISE AI DATA QUALITY REPORT")

    print("Database:", DB_PATH)
    print("\nAvailable tables:")
    for table in sorted(tables):
        print("-", table)

    section("TABLE RECORD COUNTS")

    important_tables = [
        "energy_readings",
        "daily_energy_summary",
        "consumers",
        "transformers",
        "mappings",
        "sandia_sample_consumers",
        "sandia_sample_transformers",
        "sandia_sample_mappings",
        "sandia_validation_runs",
    ]

    for table in important_tables:
        if table in tables:
            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            print(f"{table}: {count}")
        else:
            print(f"{table}: NOT FOUND")

    if "energy_readings" in tables:
        section("ENERGY READING OVERVIEW")

        row = conn.execute("""
    SELECT
        MIN(date(substr(reading_date, 7, 4) || '-' ||
                substr(reading_date, 4, 2) || '-' ||
                substr(reading_date, 1, 2))),
        MAX(date(substr(reading_date, 7, 4) || '-' ||
                substr(reading_date, 4, 2) || '-' ||
                substr(reading_date, 1, 2))),
        COUNT(*),
        SUM(CASE WHEN global_active_power IS NULL THEN 1 ELSE 0 END)
    FROM energy_readings
""").fetchone()
        
        print("First date:", row[0])
        print("Last date:", row[1])
        print("Total readings:", row[2])
        print("Missing active power:", row[3])

        section("MISSING VALUES BY COLUMN")

        columns = [
            "reading_date",
            "reading_time",
            "global_active_power",
            "global_reactive_power",
            "voltage",
            "global_intensity",
            "sub_metering_1",
            "sub_metering_2",
            "sub_metering_3",
        ]

        for column in columns:
            count = conn.execute(
                f'SELECT COUNT(*) FROM energy_readings '
                f'WHERE "{column}" IS NULL'
            ).fetchone()[0]
            print(f"{column}: {count}")

        section("DUPLICATE READINGS")

        duplicates = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT reading_date, reading_time
                FROM energy_readings
                GROUP BY reading_date, reading_time
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        print("Duplicate date-time groups:", duplicates)

        section("NEGATIVE MEASUREMENT VALUES")

        numeric_columns = [
            "global_active_power",
            "global_reactive_power",
            "voltage",
            "global_intensity",
            "sub_metering_1",
            "sub_metering_2",
            "sub_metering_3",
        ]

        for column in numeric_columns:
            count = conn.execute(
                f'SELECT COUNT(*) FROM energy_readings '
                f'WHERE "{column}" < 0'
            ).fetchone()[0]
            print(f"{column}: {count}")

    if "daily_energy_summary" in tables:
        section("DAILY SUMMARY QUALITY")

        row = conn.execute("""
            SELECT
                COUNT(*),
                MIN(reading_date),
                MAX(reading_date),
                SUM(missing_readings),
                SUM(valid_readings)
            FROM daily_energy_summary
        """).fetchone()

        print("Summary dates:", row[0])
        print("First summary date:", row[1])
        print("Last summary date:", row[2])
        print("Total valid readings:", row[4])
        print("Total missing readings:", row[3])

        invalid = conn.execute("""
            SELECT COUNT(*)
            FROM daily_energy_summary
            WHERE valid_readings < 0
               OR missing_readings < 0
               OR measured_energy_kwh < 0
        """).fetchone()[0]

        print("Rows with negative summary values:", invalid)

        inconsistent = conn.execute("""
    SELECT COUNT(*)
    FROM daily_energy_summary
    WHERE valid_readings + missing_readings != 1440
      AND reading_date NOT IN (
          (SELECT MIN(reading_date) FROM daily_energy_summary),
          (SELECT MAX(reading_date) FROM daily_energy_summary)
      )
""").fetchone()[0]

print("Incomplete interior days:", inconsistent)


    section("REPORT STATUS")
    print("Report completed successfully.")
    print("No database records were modified.")

finally:
    conn.close()
