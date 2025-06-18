#!/usr/bin/env python3
import csv
import os
import sys
import argparse

from launch_browser_updated import main

def main_wrapper():
    parser = argparse.ArgumentParser(
        description="Apply to a specific job from software_engineer.csv by row number"
    )
    parser.add_argument(
        "row",
        type=int,
        nargs="?",
        default=1,
        help="1-based row number in the CSV to process (default: 1)"
    )
    args = parser.parse_args()
    row_number = args.row

    if row_number < 1:
        print("Error: row number must be >= 1")
        return 1

    csv_file_path = "software_engineer.csv"
    base_generated_path = "/Users/umairsaeed/Documents/ai/glue/generated"

    # 1) Open CSV and pick the desired row
    try:
        with open(csv_file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                if i == row_number:
                    break
            else:
                total = i if 'i' in locals() else 0
                print(f"Error: CSV has only {total} data rows; no row {row_number}")
                return 1
    except FileNotFoundError:
        print(f"Error: The file {csv_file_path} was not found.")
        return 1

    # 2) Extract and validate columns
    try:
        job_url               = row["url"].strip()
        resume_filename       = row["resume_filename"].strip()
        cover_letter_filename = row["coverletter_filename"].strip()
    except KeyError as e:
        print(f"Error: Missing expected column in CSV: {e}")
        return 1

    if not job_url:
        print("Error: URL column is empty.")
        return 1
    if not resume_filename or not cover_letter_filename:
        print("Error: One of resume_filename or coverletter_filename is empty.")
        return 1

    # 3) Build absolute paths
    resume_path       = os.path.join(base_generated_path, resume_filename)
    cover_letter_path = os.path.join(base_generated_path, cover_letter_filename)

    # 4) Sanity-check file existence
    if not os.path.isfile(resume_path):
        print(f"Error: Resume file not found at {resume_path}")
        return 1
    if not os.path.isfile(cover_letter_path):
        print(f"Error: Cover letter file not found at {cover_letter_path}")
        return 1

    # 5) Hand off to your existing browser script
    print(f"\n→ Applying for job (row {row_number}): {job_url}")
    print(f"  Resume:       {resume_path}")
    print(f"  Cover letter: {cover_letter_path}\n")

    try:
        success = main(job_url, resume_path, cover_letter_path)
        return 0 if success else 1
    except Exception as e:
        print(f"Application script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
