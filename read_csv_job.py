import csv
import pandas as pd
import os

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

def get_job_by_row_index(csv_file_path: str, row_number: int):
    """
    Retrieves a specific job by its 1-based row number from the CSV file.
    
    Args:
        csv_file_path (str): The path to the CSV file.
        row_number (int): The 1-based row number of the job to retrieve.
        
    Returns:
        tuple or None: A tuple containing (row_index, job_description) or None if not found.
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        return None
        
    try:
        df = pd.read_csv(csv_file_path)
        
        # Convert 1-based row number to 0-based index
        row_index = row_number - 1
        
        if 0 <= row_index < len(df):
            # Try to find the job description column, checking for common names
            job_description = None
            if 'description' in df.columns:
                job_description = df.loc[row_index, 'description']
            elif 'job_description' in df.columns:
                job_description = df.loc[row_index, 'job_description']

            if pd.notna(job_description):
                return (row_index, job_description)
            else:
                return None
        else:
            return None
            
    except Exception as e:
        print(f"Error reading or processing CSV file: {e}")
        return None

def get_pending_jobs(csv_file_path: str):
    """
    Reads a CSV file and returns a list of job descriptions for pending jobs.
    A job is pending if 'resume_filename' or 'coverletter_filename' is missing.
    
    Args:
        csv_file_path (str): The path to the CSV file.
        
    Returns:
        list: A list of tuples, where each tuple contains (row_index, job_description).
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        return []
        
    try:
        df = pd.read_csv(csv_file_path)
        
        pending_jobs = []
        for index, row in df.iterrows():
            # Check if either filename is missing (NaN)
            if pd.isna(row.get('resume_filename')) or pd.isna(row.get('coverletter_filename')):
                # Check if there is a job description
                job_description = None
                if 'description' in df.columns and pd.notna(row.get('description')):
                    job_description = row['description']
                elif 'job_description' in df.columns and pd.notna(row.get('job_description')):
                    job_description = row['job_description']

                if job_description:
                    pending_jobs.append((index, job_description))
                    
        return pending_jobs
        
    except Exception as e:
        print(f"Error reading or processing CSV file: {e}")
        return []

def update_csv_with_filenames(csv_file_path: str, row_index: int, resume_filename: str, coverletter_filename: str):
    """
    Updates the CSV file with the generated resume and cover letter filenames at a specific row index.
    
    Args:
        csv_file_path (str): The path to the CSV file.
        row_index (int): The 0-based index of the row to update.
        resume_filename (str): The filename of the generated resume.
        coverletter_filename (str): The filename of the generated cover letter.
    """
    try:
        df = pd.read_csv(csv_file_path)
        
        # Ensure the columns exist, if not, add them
        if 'resume_filename' not in df.columns:
            df['resume_filename'] = pd.NA
        if 'coverletter_filename' not in df.columns:
            df['coverletter_filename'] = pd.NA
            
        # Update the specific row
        df.loc[row_index, 'resume_filename'] = resume_filename
        df.loc[row_index, 'coverletter_filename'] = coverletter_filename
        
        # Save the updated DataFrame back to the CSV
        df.to_csv(csv_file_path, index=False)
        print(f"Successfully updated row {row_index + 1} in {csv_file_path}")
        
    except Exception as e:
        print(f"Error updating CSV file: {e}") 