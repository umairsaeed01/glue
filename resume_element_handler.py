import csv
import os
from datetime import datetime

def update_csv_with_resume_element_error(row_number, status="Can't Find Resume Element", csv_file_path="software_engineer.csv"):
    """
    Update CSV file with resume element error status.
    Creates 'Applied' column if it doesn't exist, then adds status and date.
    """
    try:
        # Use the provided CSV file and row number
        if not os.path.exists(csv_file_path):
            print(f"[Resume Element Handler] CSV file not found: {csv_file_path}")
            return False
        print(f"[Resume Element Handler] Updating row {row_number} in {csv_file_path}")
        
        # Read existing CSV data
        rows = []
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            
            # Add 'Applied' column if it doesn't exist
            if 'Applied' not in fieldnames:
                fieldnames.append('Applied')
                print("[Resume Element Handler] Created 'Applied' column")
            
            # Add 'Application Date' column if it doesn't exist
            if 'Application Date' not in fieldnames:
                fieldnames.append('Application Date')
                print("[Resume Element Handler] Created 'Application Date' column")
            
            # Process each row
            for i, row in enumerate(reader, start=1):
                # Update the specific row number
                if i == row_number:
                    # Update this row with resume element error status
                    row['Applied'] = status
                    row['Application Date'] = datetime.now().strftime('%d %B %Y')  # e.g., "23 June 2025"
                    print(f"[Resume Element Handler] Updated row {row_number} with status: {status}")
                
                rows.append(row)
        
        # Write back to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"[Resume Element Handler] Successfully updated CSV with resume element error status")
        return True
        
    except Exception as e:
        print(f"[Resume Element Handler] Error updating CSV: {e}")
        return False 