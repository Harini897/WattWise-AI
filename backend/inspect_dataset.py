
from pathlib import Path
import csv

# Locate the dataset
file_path = Path("data/raw/household_power_consumption.txt")

# Check whether the file exists
if not file_path.exists():
    print("Dataset not found!")
    print("Please place the TXT file inside data/raw/")
else:
    print("Dataset found!")
    print("File:", file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")

        # Read the column names
        headers = next(reader)

        print("\nColumn names:")
        for column in headers:
            print("-", column)

        print("\nFirst 5 records:")
        for i, row in enumerate(reader):
            print(row)
            if i == 4:
                break