#!/usr/bin/env python3
import csv
import sys
from collections import Counter

def check_csv_status(csv_file_path="software_engineer.csv"):
    """Check the status of all jobs in the CSV file"""
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Count statuses
            status_counts = Counter()
            total_jobs = 0
            unprocessed_jobs = []
            
            for i, row in enumerate(reader, start=1):
                total_jobs += 1
                status = row.get('Applied', '').strip()
                if status:
                    status_counts[status] += 1
                else:
                    unprocessed_jobs.append(i)
            
            # Display summary
            print(f"📊 Job Application Status Summary")
            print("=" * 50)
            print(f"Total jobs in CSV: {total_jobs}")
            print(f"Processed jobs: {sum(status_counts.values())}")
            print(f"Unprocessed jobs: {len(unprocessed_jobs)}")
            print()
            
            # Display status breakdown
            if status_counts:
                print("Status Breakdown:")
                for status, count in status_counts.most_common():
                    percentage = (count / total_jobs) * 100
                    print(f"  {status}: {count} ({percentage:.1f}%)")
                print()
            
            # Display unprocessed job numbers
            if unprocessed_jobs:
                print("Unprocessed job row numbers:")
                if len(unprocessed_jobs) <= 20:
                    print(f"  {', '.join(map(str, unprocessed_jobs))}")
                else:
                    print(f"  {', '.join(map(str, unprocessed_jobs[:20]))}...")
                    print(f"  ... and {len(unprocessed_jobs) - 20} more")
                print()
            
            # Display next job to process
            if unprocessed_jobs:
                print(f"Next job to process: Row {unprocessed_jobs[0]}")
                print(f"Command: python apply_from_csv.py {unprocessed_jobs[0]}")
                print()
                print(f"To process all remaining jobs:")
                print(f"Command: python apply_from_csv.py all --start-from {unprocessed_jobs[0]}")
            else:
                print("✅ All jobs have been processed!")
            
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file_path}' not found.")
        return 1
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(check_csv_status()) 