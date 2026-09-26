
import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Locate the database
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "data" / "database" / "wattwise.db"


def main():
    if not DB_FILE.exists():
        print("Database not found!")
        return

    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    # Create a table for daily summaries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_energy_summary (
            reading_date TEXT PRIMARY KEY,
            measured_energy_kwh REAL,
            valid_readings INTEGER,
            missing_readings INTEGER
        )
    """)

    # Read electricity measurements
    cursor.execute("""
        SELECT reading_date, global_active_power
        FROM energy_readings
    """)

    daily_data = defaultdict(
        lambda: {
            "energy": 0.0,
            "valid": 0,
            "missing": 0
        }
    )

    print("Calculating daily electricity consumption...")

    for date_text, power in cursor.fetchall():

        # Convert date from DD/MM/YYYY to YYYY-MM-DD
        try:
            date_obj = datetime.strptime(date_text, "%d/%m/%Y")
            date_key = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue

        # Count missing measurements
        if power is None:
            daily_data[date_key]["missing"] += 1
            continue

        # Each reading represents power in kW for a one-minute interval.
        # Convert kW to kWh by dividing by 60.
        daily_data[date_key]["energy"] += power / 60
        daily_data[date_key]["valid"] += 1

    # Save the daily summaries
    summary_rows = []

    for date_key, values in daily_data.items():
        summary_rows.append((
            date_key,
            round(values["energy"], 4),
            values["valid"],
            values["missing"]
        ))

    cursor.executemany("""
        INSERT OR REPLACE INTO daily_energy_summary (
            reading_date,
            measured_energy_kwh,
            valid_readings,
            missing_readings
        ) VALUES (?, ?, ?, ?)
    """, summary_rows)

    connection.commit()

    print("\nDaily energy calculation completed!")
    print("Days processed:", len(summary_rows))

    # Display the first five daily summaries
    print("\nFirst 5 daily summaries:")

    cursor.execute("""
        SELECT reading_date, measured_energy_kwh,
               valid_readings, missing_readings
        FROM daily_energy_summary
        ORDER BY reading_date
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(row)

    connection.close()


if __name__ == "__main__":
    main()