import csv
import os
from datetime import datetime
import re

def extract_job_id_from_url(url):
    """Extract job ID from SEEK URL."""
    try:
        # Pattern to match job ID in SEEK URLs
        match = re.search(r'/job/(\d+)', url)
        if match:
            return match.group(1)
        return None
    except:
        return None

def update_csv_with_external_redirect(job_url, row_number=None, status="External Redirect", csv_file_path="software_engineer.csv"):
    """
    Update CSV file with external redirect status.
    Creates 'Applied' column if it doesn't exist, then adds status and date.
    """
    try:
        # Use the provided CSV file and row number
        if not os.path.exists(csv_file_path):
            print(f"[External Redirect Handler] CSV file not found: {csv_file_path}")
            return False
        print(f"[External Redirect Handler] Updating row {row_number} in {csv_file_path}")
        
        # Read existing CSV data
        rows = []
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            
            # Add 'Applied' column if it doesn't exist
            if 'Applied' not in fieldnames:
                fieldnames.append('Applied')
                print("[External Redirect Handler] Created 'Applied' column")
            
            # Add 'Application Date' column if it doesn't exist
            if 'Application Date' not in fieldnames:
                fieldnames.append('Application Date')
                print("[External Redirect Handler] Created 'Application Date' column")
            
            # Process each row
            for i, row in enumerate(reader, start=1):
                # Update the specific row number
                if i == row_number:
                    # Update this row with external redirect status
                    row['Applied'] = status
                    row['Application Date'] = datetime.now().strftime('%d %B %Y')  # e.g., "23 June 2025"
                    print(f"[External Redirect Handler] Updated row {row_number} with status: {status}")
                
                rows.append(row)
        
        # Write back to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"[External Redirect Handler] Successfully updated CSV with external redirect status")
        return True
        
    except Exception as e:
        print(f"[External Redirect Handler] Error updating CSV: {e}")
        return False 