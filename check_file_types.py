import os
import csv
import mimetypes
from collections import defaultdict


def aggregate_by_file_type(directory, output_csv):
    file_type_count = defaultdict(int)

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_type, _ = mimetypes.guess_type(file_path)
            if file_type is None:
                file_type = "unknown"
            file_type_count[file_type] += 1

    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["file_type", "count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for file_type, count in file_type_count.items():
            writer.writerow({"file_type": file_type, "count": count})


source_directory = "path/to/directory"
output_csv_path = "file_types_aggregation.csv"

aggregate_by_file_type(source_directory, output_csv_path)
