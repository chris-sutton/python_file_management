import os
import csv
from collections import defaultdict


def aggregate_by_extension(directory, output_csv):
    extension_count = defaultdict(int)

    for root, dirs, files in os.walk(directory):
        for file in files:
            extension = os.path.splitext(file)[1].lower()
            extension_count[extension] += 1

    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["extension", "count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for extension, count in extension_count.items():
            writer.writerow({"extension": extension, "count": count})


source_directory = "path/to/directory"
output_csv_path = "extensions_aggregation.csv"

aggregate_by_extension(source_directory, output_csv_path)
