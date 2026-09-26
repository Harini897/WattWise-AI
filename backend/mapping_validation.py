import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/database/wattwise.db")

def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    try:
        total = conn.execute("""
            SELECT COUNT(*) FROM sandia_sample_mappings
        """).fetchone()[0]

        if total == 0:
            raise ValueError("No sample mapping records found.")

        mismatches = conn.execute("""
            SELECT customer_id, reference_transformer_id, error_label
            FROM sandia_sample_mappings
            WHERE reference_transformer_id != error_label
            ORDER BY customer_id
        """).fetchall()

        incorrect = len(mismatches)
        correct = total - incorrect
        accuracy = correct / total * 100
        error_rate = incorrect / total * 100

        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sandia_validation_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_customers INTEGER NOT NULL,
                    matching_labels INTEGER NOT NULL,
                    mismatched_labels INTEGER NOT NULL,
                    baseline_accuracy REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    run_timestamp TEXT NOT NULL
                )
            """)

            conn.execute("""
                INSERT INTO sandia_validation_runs (
                    total_customers,
                    matching_labels,
                    mismatched_labels,
                    baseline_accuracy,
                    error_rate,
                    run_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                total,
                correct,
                incorrect,
                accuracy,
                error_rate,
                datetime.now(timezone.utc).isoformat()
            ))

        print("=" * 45)
        print("WATTWISE AI - MAPPING VALIDATION")
        print("=" * 45)
        print(f"Total customers: {total}")
        print(f"Matching labels: {correct}")
        print(f"Mismatched labels: {incorrect}")
        print(f"Baseline accuracy: {accuracy:.2f}%")
        print(f"Error rate: {error_rate:.2f}%")

        print("\nMISMATCHED LABELS:")
        if mismatches:
            for customer, reference, error in mismatches:
                print(
                    f"{customer} | Reference: {reference} | "
                    f"Error: {error}"
                )
        else:
            print("No mismatches found.")

        print("\nValidation report saved to SQLite.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
