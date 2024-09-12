import os
import shutil
import hashlib
import csv
import sys
import time
import signal


def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def prepopulate_log(src, log_file):
    if not os.path.exists(log_file):
        with open(log_file, "w", newline="") as csvfile:
            fieldnames = ["file", "status"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for root, dirs, files in os.walk(src):
                for file in files:
                    src_file = os.path.join(root, file)
                    writer.writerow({"file": src_file, "status": "pending"})


def truncate_filename(src_file, max_length):
    if len(src_file) <= max_length:
        return src_file
    else:
        separator = "/" if "/" in src_file else "\\"
        truncated_part = src_file[-max_length:]
        first_separator_index = truncated_part.find(separator)
        if first_separator_index != -1:
            return f"..{truncated_part[first_separator_index:]}"
        else:
            return f"..{truncated_part}"


def copy_files(src, dst, log_file):
    if not os.path.exists(dst):
        os.makedirs(dst)

    with open(log_file, "r+", newline="") as csvfile:
        fieldnames = ["file", "status"]
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        total_files = len(rows)
        copied_files = 0
        spinner = ["|", "/", "-", "\\"]
        max_filename_length = 48  # Adjust this length as needed
        save_interval = 100  # Save every 100 files

        def signal_handler(sig, frame):
            # Mark the last file being processed with "interrupted"
            if copied_files > 0:
                rows[copied_files - 1]["status"] = "error: interrupted"
            # Move the file pointer to the beginning of the file
            csvfile.seek(0)
            writer.writeheader()
            writer.writerows(rows)
            print("\nProcess interrupted. CSV file saved.")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        for row in rows:
            if row["status"] == "success":
                continue

            src_file = row["file"]
            copied_files += 1
            dst_file = os.path.join(dst, os.path.relpath(src_file, src))
            dst_dir = os.path.dirname(dst_file)

            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            try:
                shutil.copy2(src_file, dst_file)
                if calculate_md5(src_file) != calculate_md5(dst_file):
                    row["status"] = "corruption detected"
                else:
                    row["status"] = "success"
            except Exception as e:
                row["status"] = f"error: {e}"

            # Truncate the file name if it's too long
            display_file = truncate_filename(src_file, max_filename_length)
            # Update the progress indicator
            progress_message = f"{spinner[copied_files % len(spinner)]} Copied: {copied_files} out of {total_files} - {display_file}"
            sys.stdout.write(f"\r{progress_message.ljust(max_filename_length + 30)}")
            sys.stdout.flush()

            # Save the CSV file every 100 files
            if copied_files % save_interval == 0:
                csvfile.seek(0)
                writer.writeheader()
                writer.writerows(rows)

        # Final save of the CSV file
        csvfile.seek(0)
        writer.writeheader()
        writer.writerows(rows)


source_directory = "path/to/directory"
destination_directory = "test_dst"
log_file_path = "log.csv"

# Prepopulate the log file with all potential filenames if it doesn't exist
prepopulate_log(source_directory, log_file_path)

# Copy files and update the log file
copy_files(source_directory, destination_directory, log_file_path)
