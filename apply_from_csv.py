#!/usr/bin/env python3
import csv
import os
import sys
import argparse
import time
from datetime import datetime

from launch_browser_updated import main
#from local_generate import process_job

def generate_resume_and_cover_letter(row_number, csv_file_path, old_resume_file="Umair_resume.pdf"):
    """Generate resume and cover letter for a job if they don't exist"""
    try:
        print(f"📄 Checking if resume and cover letter exist for row {row_number}...")
        
        # Read the specific row to check current filenames
        with open(csv_file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                if i == row_number:
                    current_resume_filename = row.get("resume_filename", "").strip()
                    current_cover_letter_filename = row.get("coverletter_filename", "").strip()
                    break
            else:
                print(f"Error: Row {row_number} not found in CSV")
                return False, None, None
        
        # Check if files already exist
        base_generated_path = "generated"
        resume_path = os.path.join(base_generated_path, current_resume_filename) if current_resume_filename else None
        cover_letter_path = os.path.join(base_generated_path, current_cover_letter_filename) if current_cover_letter_filename else None
        
        # If both files exist, no need to generate
        if (current_resume_filename and current_cover_letter_filename and 
            os.path.isfile(resume_path) and os.path.isfile(cover_letter_path)):
            print(f"✅ Resume and cover letter already exist for row {row_number}")
            return True, current_resume_filename, current_cover_letter_filename
        
        # Generate new files
        print(f"🔄 Generating resume and cover letter for row {row_number}...")
        
        # Call the resume generation function
        success = process_job(csv_file_path, row_number, old_resume_file)
        
        if not success:
            print(f"❌ Failed to generate resume and cover letter for row {row_number}")
            return False, None, None
        
        # Read the updated row to get the new filenames
        with open(csv_file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                if i == row_number:
                    new_resume_filename = row.get("resume_filename", "").strip()
                    new_cover_letter_filename = row.get("coverletter_filename", "").strip()
                    break
            else:
                print(f"Error: Row {row_number} not found in CSV after generation")
                return False, None, None
        
        # Verify the files were actually created
        new_resume_path = os.path.join(base_generated_path, new_resume_filename)
        new_cover_letter_path = os.path.join(base_generated_path, new_cover_letter_filename)
        
        if os.path.isfile(new_resume_path) and os.path.isfile(new_cover_letter_path):
            print(f"✅ Successfully generated resume and cover letter for row {row_number}")
            print(f"   Resume: {new_resume_filename}")
            print(f"   Cover Letter: {new_cover_letter_filename}")
            return True, new_resume_filename, new_cover_letter_filename
        else:
            print(f"❌ Files not found after generation for row {row_number}")
            return False, None, None
            
    except Exception as e:
        print(f"Error generating resume and cover letter for row {row_number}: {e}")
        return False, None, None

def process_single_job(row_number, csv_file_path, base_generated_path, old_resume_file="Umair_resume.pdf"):
    """Process a single job application and return success status"""
    try:
        # Read the specific row
        with open(csv_file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                if i == row_number:
                    break
            else:
                print(f"Error: Row {row_number} not found in CSV")
                return False

        # Extract and validate columns
        try:
            job_url = row["url"].strip()
            resume_filename = row.get("resume_filename", "").strip()
            cover_letter_filename = row.get("coverletter_filename", "").strip()
        except KeyError as e:
            print(f"Error: Missing expected column in CSV: {e}")
            return False

        if not job_url:
            print(f"Error: URL column is empty for row {row_number}")
            return False
        
        # Check if resume and cover letter exist, generate if needed
        if not resume_filename or not cover_letter_filename:
            print(f"📝 Resume or cover letter filename missing for row {row_number}, generating...")
            success, resume_filename, cover_letter_filename = generate_resume_and_cover_letter(
                row_number, csv_file_path, old_resume_file
            )
            if not success:
                print(f"❌ Failed to generate resume and cover letter for row {row_number}")
                return False
        
        # Build absolute paths
        resume_path = os.path.join(base_generated_path, resume_filename)
        cover_letter_path = os.path.join(base_generated_path, cover_letter_filename)

        # Sanity-check file existence
        if not os.path.isfile(resume_path):
            print(f"Error: Resume file not found at {resume_path}")
            return False
        if not os.path.isfile(cover_letter_path):
            print(f"Error: Cover letter file not found at {cover_letter_path}")
            return False

        # Apply for the job
        print(f"\n→ Applying for job (row {row_number}): {job_url}")
        print(f"  Resume:       {resume_path}")
        print(f"  Cover letter: {cover_letter_path}\n")

        # Call the main function and get the result
        result = main(job_url, resume_path, cover_letter_path, row_number, csv_file_path)
        
        # Define success statuses (these indicate handlers have already updated CSV)
        success_statuses = [
            'SUCCESS_COMPLETE',      # Success handler updated CSV
            'HANDLER_SUCCESS',       # Other handlers updated CSV
            'EXTERNAL_REDIRECT',     # External redirect handler updated CSV
            'JOB_UNAVAILABLE',       # Job unavailable handler updated CSV
            'RESUME_ELEMENT_ERROR'   # Resume element handler updated CSV
        ]
        
        # Define failure statuses (these indicate no CSV was updated)
        failure_statuses = [
            'APPLY_BUTTON_NOT_FOUND',
            'UNEXPECTED_ERROR',
            'LLM_GENERATION_FAILED',
            'MAX_STEPS_REACHED',
            'UNEXPECTED_EXCEPTION',
            'UNKNOWN_ERROR'
        ]
        
        print(f"Job processing result: {result}")
        
        # Check if this is a success status (CSV already updated by handler)
        if result in success_statuses:
            print(f"✅ Job completed with status: {result}")
            print(f"📝 CSV already updated by handler - no additional update needed")
            return True
        
        # Check if this is a failure status (need to update CSV)
        elif result in failure_statuses:
            print(f"❌ Job failed with status: {result}")
            # Update CSV with appropriate error status
            error_status = f"Error - {result.replace('_', ' ')}"
            if update_csv_status(row_number, error_status, csv_file_path):
                print(f"📝 Updated CSV with status: {error_status}")
            return False
        
        # Unknown status
        else:
            print(f"⚠️ Unknown result status: {result}")
            # Update CSV with unknown error status
            if update_csv_status(row_number, f"Error - Unknown Status: {result}", csv_file_path):
                print(f"📝 Updated CSV with unknown error status")
            return False

    except Exception as e:
        print(f"Error processing row {row_number}: {e}")
        # Update CSV with exception error status
        if update_csv_status(row_number, f"Error - Exception: {str(e)[:50]}", csv_file_path):
            print(f"📝 Updated CSV with exception error status")
        return False

def update_csv_status(row_number, status, csv_file_path="software_engineer.csv"):
    """Update CSV with application status"""
    try:
        rows = []
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            
            # Add 'Applied' column if it doesn't exist
            if 'Applied' not in fieldnames:
                fieldnames.append('Applied')
            
            # Add 'Application Date' column if it doesn't exist
            if 'Application Date' not in fieldnames:
                fieldnames.append('Application Date')
            
            # Process each row
            for i, row in enumerate(reader, start=1):
                if i == row_number:
                    row['Applied'] = status
                    row['Application Date'] = datetime.now().strftime('%d %B %Y')
                    print(f"Updated row {row_number} with status: {status}")
                rows.append(row)
        
        # Write back to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        return True
    except Exception as e:
        print(f"Error updating CSV: {e}")
        return False

def check_job_status(row_number, csv_file_path):
    """Check if a job has already been processed"""
    try:
        with open(csv_file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                if i == row_number:
                    applied_status = row.get('Applied', '').strip()
                    if applied_status:
                        return applied_status
                    return None
        return None
    except Exception as e:
        print(f"Error checking job status: {e}")
        return None

def get_total_jobs(csv_file_path):
    """Get total number of jobs in CSV"""
    try:
        with open(csv_file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return sum(1 for row in reader)
    except Exception as e:
        print(f"Error counting jobs: {e}")
        return 0

def process_all_jobs(csv_file_path, base_generated_path, start_row=1, max_jobs=None, old_resume_file="Umair_resume.pdf"):
    """Process all jobs in the CSV file sequentially"""
    try:
        total_rows = get_total_jobs(csv_file_path)
        if total_rows == 0:
            print("No jobs found in CSV file")
            return
        
        # Determine end row
        end_row = total_rows
        if max_jobs:
            end_row = min(start_row + max_jobs - 1, total_rows)
        
        print(f"Starting batch processing of jobs from row {start_row} to {end_row} (out of {total_rows} total)")
        print(f"Using resume file: {old_resume_file}")
        print("=" * 70)
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for row_number in range(start_row, end_row + 1):
            print(f"\n{'='*25} Processing Row {row_number}/{end_row} {'='*25}")
            
            try:
                # Check if already processed
                current_status = check_job_status(row_number, csv_file_path)
                if current_status:
                    # Check if it's an error status that should be retried
                    if current_status.startswith("Error -"):
                        print(f"Job {row_number} previously failed with status: '{current_status}'")
                        print("Automatically retrying due to error status...")
                        # Continue to process the job (don't skip)
                    elif current_status in ["Applied Successfully", "Applied"]:
                        print(f"Job {row_number} already successfully applied with status: '{current_status}'")
                        print("Skipping job as it was already successfully processed.")
                        skipped_count += 1
                        continue
                    else:
                        print(f"⏭️  Row {row_number} already processed with status: '{current_status}'")
                        skipped_count += 1
                        continue
                
                # Process the job
                print(f"🔄 Starting application for row {row_number}...")
                success = process_single_job(row_number, csv_file_path, base_generated_path, old_resume_file)
                
                if success:
                    success_count += 1
                    print(f"✅ Job {row_number} completed successfully")
                    # CSV was already updated by the handler - no need to update again
                else:
                    error_count += 1
                    # CSV was already updated by process_single_job - no need to update again
                    print(f"❌ Job {row_number} failed - status already updated in CSV")
                
                # Add delay between jobs to avoid overwhelming the system
                if row_number < end_row:  # Don't wait after the last job
                    print("⏳ Waiting 5 seconds before next job...")
                    time.sleep(5)
                
            except KeyboardInterrupt:
                print(f"\n⚠️  User interrupted processing at row {row_number}")
                # Only update CSV if it hasn't been updated yet
                current_status = check_job_status(row_number, csv_file_path)
                if not current_status:
                    update_csv_status(row_number, "Interrupted - User Stopped")
                break
            except Exception as e:
                error_count += 1
                print(f"❌ Unexpected error processing row {row_number}: {e}")
                # Only update CSV if it hasn't been updated yet
                current_status = check_job_status(row_number, csv_file_path)
                if not current_status:
                    update_csv_status(row_number, "Error - Unexpected Failure")
                continue
        
        print(f"\n{'='*70}")
        print(f"🎯 Batch processing completed!")
        print(f"✅ Successful applications: {success_count}")
        print(f"❌ Failed applications: {error_count}")
        print(f"⏭️  Skipped (already processed): {skipped_count}")
        print(f"📊 Total processed in this session: {success_count + error_count}")
        print(f"📈 Progress: {start_row}-{end_row} of {total_rows} total jobs")
        
    except Exception as e:
        print(f"Error in batch processing: {e}")

def main_wrapper():
    parser = argparse.ArgumentParser(
        description="Apply to jobs from a specified CSV file - sequential or batch processing"
    )
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to the CSV file (e.g., ai.csv, software_engineer.csv)"
    )
    parser.add_argument(
        "row",
        type=str,
        nargs="?",
        default="1",
        help="Row number (1-based) or 'all' to process all jobs (default: 1)"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=1,
        help="Start processing from this row number when using 'all' (default: 1)"
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        help="Maximum number of jobs to process when using 'all' (default: all remaining jobs)"
    )
    parser.add_argument(
        "--resume-file",
        type=str,
        default="Umair_resume.pdf",
        help="Path to the old resume file (default: Umair_resume.pdf)"
    )
    
    args = parser.parse_args()
    
    csv_file_path = args.csv_file
    base_generated_path = "/Users/umairsaeed/Documents/ai/glue/generated"

    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: The file {csv_file_path} was not found.")
        return 1

    # Check if resume file exists
    if not os.path.exists(args.resume_file):
        print(f"Error: Resume file '{args.resume_file}' not found")
        return 1

    # Handle "all" command
    if args.row.lower() == "all":
        process_all_jobs(csv_file_path, base_generated_path, args.start_from, args.max_jobs, args.resume_file)
        return 0
    
    # Handle single row processing
    try:
        row_number = int(args.row)
    except ValueError:
        print("Error: Row must be a number or 'all'")
        return 1

    if row_number < 1:
        print("Error: row number must be >= 1")
        return 1

    # Check if already processed
    current_status = check_job_status(row_number, csv_file_path)
    if current_status:
        # Check if it's an error status that should be retried
        if current_status.startswith("Error -"):
            print(f"Job {row_number} previously failed with status: '{current_status}'")
            print("Automatically retrying due to error status...")
        elif current_status in ["Applied Successfully", "Applied"]:
            print(f"Job {row_number} already successfully applied with status: '{current_status}'")
            print("Skipping job as it was already successfully processed.")
            return 0
        else:
            print(f"Job {row_number} already processed with status: '{current_status}'")
            response = input("Do you want to process it again? (y/N): ")
            if response.lower() != 'y':
                print("Skipping job as requested.")
                return 0

    # Process single job
    success = process_single_job(row_number, csv_file_path, base_generated_path, args.resume_file)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
