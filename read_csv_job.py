import csv
import pandas as pd

def get_first_job_description(csv_file_path: str) -> str:
    """
    Reads a CSV file, skips the header, and returns the job description
    from the 'description' column of the second row.
    """
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Read the first data row (second row in the CSV)
        try:
            first_data_row = next(reader)
            if 'description' in first_data_row:
                return first_data_row['description']
            else:
                raise ValueError("'description' column not found in CSV.")
        except StopIteration:
            raise ValueError("CSV file is empty or only contains headers.")

def get_pending_jobs(csv_file_path: str) -> list:
    """
    Gets all job descriptions that haven't been processed yet (no resume_filename or coverletter_filename).
    
    Returns:
        list: List of tuples containing (row_index, job_description) for jobs that need processing
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        pending_jobs = []
        
        # Iterate through each row
        for index, row in df.iterrows():
            # Check if either resume_filename or coverletter_filename is empty/NaN
            if pd.isna(row.get('resume_filename')) or pd.isna(row.get('coverletter_filename')):
                if 'description' in row and not pd.isna(row['description']):
                    pending_jobs.append((index, row['description']))
        
        print(f"Found {len(pending_jobs)} jobs pending processing")
        return pending_jobs
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return []

def update_csv_with_filenames(csv_file_path: str, row_index: int, resume_filename: str, coverletter_filename: str):
    """
    Updates the CSV file with the generated resume and cover letter filenames.
    
    Args:
        csv_file_path (str): Path to the CSV file
        row_index (int): Index of the row to update (0-based, excluding header)
        resume_filename (str): Name of the generated resume file
        coverletter_filename (str): Name of the generated cover letter file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Update the specific row with the new filenames
        df.at[row_index, 'resume_filename'] = resume_filename
        df.at[row_index, 'coverletter_filename'] = coverletter_filename
        
        # Save the updated DataFrame back to CSV
        df.to_csv(csv_file_path, index=False)
        print(f"Successfully updated CSV with filenames for row {row_index + 1}")
    except Exception as e:
        print(f"Error updating CSV: {str(e)}") 