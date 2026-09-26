
import sqlite3
from pathlib import Path

# Locate the database
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "data" / "database" / "wattwise.db"

def main():
    if not DB_FILE.exists():
        print("Database not found!")
        return

    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    print("=" * 50)
    print("       WATTWISE AI DATABASE REPORT")
    print("=" * 50)

    # 1. Count stored records
    cursor.execute("SELECT COUNT(*) FROM energy_readings")
    total = cursor.fetchone()[0]
    print("\nTotal records:", total)

    # 2. Check date range
    cursor.execute("""
        SELECT MIN(reading_date), MAX(reading_date)
        FROM energy_readings
    """)
    date_range = cursor.fetchone()

    print("First date:", date_range[0])
    print("Last date:", date_range[1])

    # 3. Count missing values in each measurement column
    columns = [
        "global_active_power",
        "global_reactive_power",
        "voltage",
        "global_intensity",
        "sub_metering_1",
        "sub_metering_2",
        "sub_metering_3"
    ]

    print("\nMissing values by column:")

    for column in columns:
        query = f"SELECT COUNT(*) FROM energy_readings WHERE {column} IS NULL"
        cursor.execute(query)
        missing = cursor.fetchone()[0]
        print(f"{column}: {missing}")

    # 4. Display the first five records
    print("\nFirst 5 records:")

    cursor.execute("""
        SELECT reading_date, reading_time,
               global_active_power, voltage,
               global_intensity
        FROM energy_readings
        ORDER BY id
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(row)

    connection.close()

if __name__ == "__main__":
    main()