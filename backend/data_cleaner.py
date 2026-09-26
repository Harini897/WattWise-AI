
import csv
import sqlite3
from pathlib import Path

# File locations
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "household_power_consumption.txt"
DB_FILE = BASE_DIR / "data" / "database" / "wattwise.db"

# Create the database folder if it doesn't exist
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

# Database table structure
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS energy_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_date TEXT NOT NULL,
    reading_time TEXT NOT NULL,
    global_active_power REAL,
    global_reactive_power REAL,
    voltage REAL,
    global_intensity REAL,
    sub_metering_1 REAL,
    sub_metering_2 REAL,
    sub_metering_3 REAL
);
"""

def convert_number(value):
    """Convert a measurement to a number or None."""
    value = value.strip()

    if value == "" or value == "?":
        return None

    return float(value)

def main():
    if not INPUT_FILE.exists():
        print("ERROR: Dataset file not found!")
        print(INPUT_FILE)
        return

    print("Connecting to SQLite database...")

    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute(CREATE_TABLE)
    connection.commit()

    insert_sql = """
    INSERT INTO energy_readings (
        reading_date, reading_time,
        global_active_power, global_reactive_power,
        voltage, global_intensity,
        sub_metering_1, sub_metering_2, sub_metering_3
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    batch = []
    batch_size = 5000
    total_rows = 0
    missing_values = 0

    print("Reading and cleaning dataset...")

    try:
        with open(INPUT_FILE, "r", encoding="utf-8-sig") as file:
            reader = csv.reader(file, delimiter=";")

            headers = next(reader)

            for row in reader:
                if len(row) != 9:
                    continue

                # Skip empty lines
                if not any(value.strip() for value in row):
                    continue

                cleaned_row = [
                    row[0].strip(),
                    row[1].strip()
                ]

                for value in row[2:]:
                    number = convert_number(value)

                    if number is None:
                        missing_values += 1

                    cleaned_row.append(number)

                batch.append(tuple(cleaned_row))
                total_rows += 1

                # Insert records in batches
                if len(batch) >= batch_size:
                    cursor.executemany(insert_sql, batch)
                    connection.commit()
                    batch.clear()

                    print(f"Processed {total_rows} records...")

            # Insert remaining records
            if batch:
                cursor.executemany(insert_sql, batch)
                connection.commit()

        print("\nData processing completed!")

        cursor.execute("SELECT COUNT(*) FROM energy_readings")
        stored_rows = cursor.fetchone()[0]

        print("Rows processed:", total_rows)
        print("Rows stored in database:", stored_rows)
        print("Missing measurement values:", missing_values)
        print("Database location:", DB_FILE)

    except (ValueError, csv.Error, sqlite3.Error, OSError) as error:
        print("An error occurred:", error)

    finally:
        connection.close()

if __name__ == "__main__":
    main()