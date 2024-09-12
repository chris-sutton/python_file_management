import os
import shutil
import hashlib
import csv
import sys
import time
import signal
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


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


def copy_files(src, dst, log_file, progress_label, message_label, stop_flag):
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

        for row in rows:
            if row["status"] == "success":
                continue

            if stop_flag.is_set():
                message_label.config(text="Stopping process after current file...")
                row["status"] = "error: interrupted"
                break

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
            progress_label.config(text=progress_message)
            progress_label.update_idletasks()

            # Save the CSV file every 100 files
            if copied_files % save_interval == 0:
                csvfile.seek(0)
                writer.writeheader()
                writer.writerows(rows)
                message_label.config(text=f"Progress saved after {copied_files} files.")

            # Check stop flag more frequently
            if stop_flag.is_set():
                message_label.config(text="Stopping process after current file...")
                row["status"] = "error: interrupted"
                break

        # Final save of the CSV file
        csvfile.seek(0)
        writer.writeheader()
        writer.writerows(rows)
        if not stop_flag.is_set():
            message_label.config(text="File copying process completed.")


def start_copying():
    src = src_dir.get()
    dst = dst_dir.get()
    log = log_file.get()

    if not src or not dst or not log:
        messagebox.showerror("Error", "Please select all directories and log file.")
        return

    stop_flag.clear()
    prepopulate_log(src, log)
    threading.Thread(
        target=copy_files,
        args=(src, dst, log, progress_label, message_label, stop_flag),
    ).start()


def select_src_dir():
    directory = filedialog.askdirectory()
    src_dir.set(directory)


def select_dst_dir():
    directory = filedialog.askdirectory()
    dst_dir.set(directory)


def select_log_file():
    file = filedialog.asksaveasfilename(
        defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
    )
    log_file.set(file)


def stop_copying():
    stop_flag.set()


def on_closing():
    stop_copying()
    # Wait for the copying thread to finish
    while threading.active_count() > 1:
        time.sleep(0.1)
    root.destroy()


# GUI setup
root = tk.Tk()
root.title("File Copy Utility")

src_dir = tk.StringVar()
dst_dir = tk.StringVar()
log_file = tk.StringVar()
stop_flag = threading.Event()

tk.Label(root, text="Source Directory:").grid(
    row=0, column=0, padx=10, pady=5, sticky=tk.W
)
tk.Entry(root, textvariable=src_dir, width=50).grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=select_src_dir).grid(
    row=0, column=2, padx=10, pady=5
)

tk.Label(root, text="Destination Directory:").grid(
    row=1, column=0, padx=10, pady=5, sticky=tk.W
)
tk.Entry(root, textvariable=dst_dir, width=50).grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=select_dst_dir).grid(
    row=1, column=2, padx=10, pady=5
)

tk.Label(root, text="CSV Log File:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
tk.Entry(root, textvariable=log_file, width=50).grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=select_log_file).grid(
    row=2, column=2, padx=10, pady=5
)

tk.Button(root, text="Start Copying", command=start_copying).grid(
    row=3, column=1, padx=10, pady=20
)
tk.Button(root, text="Stop Copying", command=stop_copying).grid(
    row=3, column=2, padx=10, pady=20
)

progress_label = tk.Label(root, text="", width=80, anchor="w")
progress_label.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

message_label = tk.Label(root, text="", width=80, anchor="w")
message_label.grid(row=5, column=0, columnspan=3, padx=10, pady=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
