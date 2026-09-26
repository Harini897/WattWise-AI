
import sqlite3
import html
from pathlib import Path
from datetime import datetime

# --------------------------------------------------
# WattWise AI - Data Engineering Dashboard
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "database" / "wattwise.db"
OUTPUT_PATH = ROOT / "wattwise_dashboard.html"

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")


def safe_number(value, digits=2):
    if value is None:
        return "N/A"
    return f"{value:,.{digits}f}"


def parse_date(value):
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def get_date_range(values):
    dates = [parse_date(v) for v in values if v]
    dates = [d for d in dates if d]

    if not dates:
        return "N/A"

    return (
        f"{min(dates).strftime('%d %b %Y')} — "
        f"{max(dates).strftime('%d %b %Y')}"
    )


def card(title, value, subtitle=""):
    return f"""
    <div class="card">
        <div class="card-title">{html.escape(title)}</div>
        <div class="card-value">{html.escape(str(value))}</div>
        <div class="card-subtitle">{html.escape(str(subtitle))}</div>
    </div>
    """


with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row

    # -------------------------------
    # Raw energy readings
    # -------------------------------
    raw = conn.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(global_active_power) AS valid,
            COUNT(*) - COUNT(global_active_power) AS missing,
            ROUND(SUM(global_active_power) / 60.0, 4) AS energy,
            MIN(reading_date) AS first_date,
            MAX(reading_date) AS last_date
        FROM energy_readings
    """).fetchone()

    raw_dates = [
        row[0] for row in conn.execute(
            "SELECT DISTINCT reading_date FROM energy_readings"
        ).fetchall()
    ]

    # -------------------------------
    # Daily energy summaries
    # -------------------------------
    daily = conn.execute("""
        SELECT
            COUNT(*) AS days,
            ROUND(SUM(measured_energy_kwh), 4) AS energy,
            SUM(valid_readings) AS valid,
            SUM(missing_readings) AS missing,
            SUM(CASE WHEN missing_readings > 0 THEN 1 ELSE 0 END)
                AS incomplete_days,
            SUM(CASE WHEN valid_readings = 0 THEN 1 ELSE 0 END)
                AS empty_days,
            MIN(reading_date) AS first_date,
            MAX(reading_date) AS last_date
        FROM daily_energy_summary
    """).fetchone()

    daily_rows = conn.execute("""
        SELECT reading_date, measured_energy_kwh,
               valid_readings, missing_readings
        FROM daily_energy_summary
        ORDER BY reading_date DESC
        LIMIT 10
    """).fetchall()

    # -------------------------------
    # Mapping database
    # -------------------------------
    tables = {
        row[0] for row in conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
        """).fetchall()
    }

    def table_count(name):
        if name not in tables:
            return "Table missing"
        return conn.execute(
            f'SELECT COUNT(*) FROM "{name}"'
        ).fetchone()[0]

    consumers = table_count("consumers")
    transformers = table_count("transformers")
    mappings = table_count("mappings")

    mapping_status = {}
    if "mappings" in tables:
        columns = {
            row[1] for row in conn.execute(
                "PRAGMA table_info(mappings)"
            ).fetchall()
        }

        if "mapping_status" in columns:
            mapping_status = {
                row[0] or "Unknown": row[1]
                for row in conn.execute("""
                    SELECT mapping_status, COUNT(*)
                    FROM mappings
                    GROUP BY mapping_status
                """).fetchall()
            }


# -------------------------------
# Build daily table
# -------------------------------
daily_html = ""

for row in daily_rows:
    daily_html += f"""
    <tr>
        <td>{html.escape(str(row['reading_date']))}</td>
        <td>{safe_number(row['measured_energy_kwh'], 4)}</td>
        <td>{safe_number(row['valid_readings'], 0)}</td>
        <td>{safe_number(row['missing_readings'], 0)}</td>
    </tr>
    """

# -------------------------------
# Build mapping status section
# -------------------------------
status_html = ""

if mapping_status:
    for status, count in mapping_status.items():
        status_html += f"""
        <div class="status-row">
            <span>{html.escape(str(status))}</span>
            <strong>{count:,}</strong>
        </div>
        """
else:
    status_html = "<p>No mapping records available.</p>"

# -------------------------------
# Create dashboard
# -------------------------------
cards = "".join([
    card("Total Raw Readings", safe_number(raw["total"], 0)),
    card("Valid Active Power Readings", safe_number(raw["valid"], 0)),
    card("Missing Active Power Readings", safe_number(raw["missing"], 0)),
    card("Total Measured Energy", safe_number(raw["energy"], 4) + " kWh"),
    card("Daily Summary Records", safe_number(daily["days"], 0)),
    card("Summary Energy", safe_number(daily["energy"], 4) + " kWh"),
    card("Days With Missing Readings", safe_number(daily["incomplete_days"], 0)),
    card("Days With Zero Valid Readings", safe_number(daily["empty_days"], 0)),
])

mapping_cards = "".join([
    card("Consumers", str(consumers)),
    card("Transformers", str(transformers)),
    card("Mappings", str(mappings)),
])

raw_range = get_date_range(raw_dates)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WattWise AI - Data Engineering Dashboard</title>

<style>
* {{ box-sizing: border-box; }}

body {{
    margin: 0;
    font-family: "Segoe UI", Arial, sans-serif;
    background: #0b1220;
    color: #e5e7eb;
}}

header {{
    padding: 32px 6%;
    background: linear-gradient(135deg, #102b46, #123b35);
    border-bottom: 1px solid #263b4c;
}}

header h1 {{
    margin: 0;
    font-size: 30px;
    color: #6ee7b7;
}}

header p {{
    color: #cbd5e1;
    margin-bottom: 0;
}}

main {{
    max-width: 1300px;
    margin: auto;
    padding: 30px 5%;
}}

h2 {{
    margin-top: 35px;
    color: #6ee7b7;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 16px;
}}

.card {{
    background: #131e30;
    border: 1px solid #26374d;
    border-radius: 14px;
    padding: 22px;
    min-width: 0;
}}

.card-title {{
    font-size: 14px;
    color: #a5b4c8;
}}

.card-value {{
    font-size: 27px;
    font-weight: 700;
    margin: 14px 0;
    color: #6ee7b7;
    overflow-wrap: anywhere;
}}

.card-subtitle {{
    font-size: 12px;
    color: #94a3b8;
}}

.panel {{
    background: #131e30;
    border: 1px solid #26374d;
    border-radius: 14px;
    padding: 22px;
    margin-top: 20px;
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 500px;
}}

th, td {{
    padding: 13px;
    text-align: left;
    border-bottom: 1px solid #26374d;
}}

th {{ color: #6ee7b7; }}

.status-row {{
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #26374d;
}}

.tag {{
    display: inline-block;
    background: #164e3e;
    color: #a7f3d0;
    padding: 7px 12px;
    border-radius: 20px;
    font-size: 12px;
}}

footer {{
    text-align: center;
    padding: 25px;
    color: #94a3b8;
    font-size: 13px;
}}

@media (max-width: 600px) {{
    header h1 {{ font-size: 24px; }}
    main {{ padding: 20px 4%; }}
    .card-value {{ font-size: 23px; }}
}}
</style>
</head>

<body>

<header>
    <h1>⚡ WattWise AI</h1>
    <p>Data Engineering Dashboard | Energy Analytics & Data Quality</p>
    <span class="tag">SQLite Database Connected</span>
</header>

<main>

    <h2>01 — Dataset Overview</h2>
    <div class="grid">
        {card("Raw Dataset", "Household Power Consumption")}
        {card("Raw Data Date Range", raw_range)}
        {card("Daily Summary Date Range", get_date_range(
            [daily["first_date"], daily["last_date"]]
        ))}
    </div>

    <h2>02 — Energy & Data Quality</h2>
    <div class="grid">{cards}</div>

    <div class="panel">
        <h3>Latest Daily Energy Summaries</h3>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Energy (kWh)</th>
                    <th>Valid Readings</th>
                    <th>Missing Readings</th>
                </tr>
            </thead>
            <tbody>{daily_html}</tbody>
        </table>
    </div>

    <h2>03 — Mapping Database</h2>
    <div class="grid">{mapping_cards}</div>

    <div class="panel">
        <h3>Mapping Verification Status</h3>
        {status_html}
    </div>

    <h2>04 — Project Progress</h2>
    <div class="panel">
        <div class="status-row">
            <span>Dataset inspection</span><strong>Completed</strong>
        </div>
        <div class="status-row">
            <span>Data cleaning and SQLite storage</span><strong>Completed</strong>
        </div>
        <div class="status-row">
            <span>Daily energy summaries</span><strong>Generated</strong>
        </div>
        <div class="status-row">
            <span>Data quality reporting</span><strong>Implemented</strong>
        </div>
        <div class="status-row">
            <span>Mapping database structure</span><strong>Created</strong>
        </div>
        <div class="status-row">
            <span>Verified real-world mappings</span><strong>Pending</strong>
        </div>
        <div class="status-row">
            <span>Consumer-to-transformer prediction engine</span><strong>Pending</strong>
        </div>
    </div>

</main>

<footer>
    WattWise AI | Generated from your local SQLite database
</footer>

</body>
</html>
"""

OUTPUT_PATH.write_text(html_content, encoding="utf-8")

print("WattWise AI dashboard generated successfully!")
print("Dashboard location:", OUTPUT_PATH)
print("Raw readings:", raw["total"])
print("Daily summaries:", daily["days"])
print("Consumers:", consumers)
print("Transformers:", transformers)
print("Mappings:", mappings)