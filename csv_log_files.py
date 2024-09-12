import os
import csv
import mimetypes


def log_files_with_details(directory, output_csv):
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["type", "extension", "full_path"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for root, dirs, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                file_type, _ = mimetypes.guess_type(full_path)
                if file_type is None:
                    file_type = "unknown"
                extension = os.path.splitext(file)[1].lower()
                writer.writerow(
                    {"full_path": full_path, "type": file_type, "extension": extension}
                )


source_directory = "path/to/directory"
output_csv_path = "file_details_log.csv"

log_files_with_details(source_directory, output_csv_path)
