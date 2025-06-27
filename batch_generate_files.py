#!/usr/bin/env python3
import csv
import os
import sys
import argparse
from datetime import datetime
import pandas as pd

# Import the resume generation function
from local_generate import generate_resume_and_cover_letter
from read_csv_job import get_job_by_row_index, update_csv_with_filenames

def generate_files_for_csv(csv_file, start_row=1, max_jobs=None, resume_file="Umair_resume.pdf"):
    """
    Generate resume and cover letter files for all jobs in a CSV file
    
    Args:
        csv_file (str): Path to the CSV file
        start_row (int): Starting row number (1-indexed)
        max_jobs (int): Maximum number of jobs to process (None for all)
        resume_file (str): Path to the old resume file
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        total_rows = len(df)
        
        if total_rows == 0:
            print("No jobs found in CSV file")
            return
        
        # Determine end row
        end_row = total_rows
        if max_jobs:
            end_row = min(start_row + max_jobs - 1, total_rows)
        
        print(f"Starting batch file generation for jobs from row {start_row} to {end_row} (out of {total_rows} total)")
        print(f"Using resume file: {resume_file}")
        print("=" * 70)
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for row_number in range(start_row, end_row + 1):
            print(f"\n{'='*25} Processing Row {row_number}/{end_row} {'='*25}")
            
            try:
                # Get job info from CSV - handle NaN values properly
                job_info = get_job_by_row_index(csv_file, row_number)
                
                if not job_info:
                    print(f"❌ Row {row_number}: No job description found, skipping...")
                    error_count += 1
                    continue
                
                row_index, job_description = job_info
                
                # Handle NaN values in job description
                if pd.isna(job_description) or job_description is None:
                    print(f"❌ Row {row_number}: Job description is empty/NaN, skipping...")
                    error_count += 1
                    continue
                
                # Convert to string and strip whitespace
                job_description = str(job_description).strip()
                
                if not job_description:
                    print(f"❌ Row {row_number}: Job description is empty after stripping, skipping...")
                    error_count += 1
                    continue
                
                print(f"🔗 Job Description: {job_description[:100]}...")
                
                # Check if files already exist for this row
                current_resume_filename = df.iloc[row_number - 1].get('resume_filename', '')
                current_cover_letter_filename = df.iloc[row_number - 1].get('coverletter_filename', '')
                if pd.isna(current_resume_filename):
                    current_resume_filename = ''
                if pd.isna(current_cover_letter_filename):
                    current_cover_letter_filename = ''
                current_resume_filename = current_resume_filename.strip()
                current_cover_letter_filename = current_cover_letter_filename.strip()
                
                base_generated_path = "generated"
                resume_path = os.path.join(base_generated_path, current_resume_filename) if current_resume_filename else None
                cover_letter_path = os.path.join(base_generated_path, current_cover_letter_filename) if current_cover_letter_filename else None
                
                # If both files exist, skip
                if (current_resume_filename and current_cover_letter_filename and 
                    os.path.isfile(resume_path) and os.path.isfile(cover_letter_path)):
                    print(f"⏭️  Row {row_number}: Files already exist, skipping...")
                    print(f"   Resume: {current_resume_filename}")
                    print(f"   Cover Letter: {current_cover_letter_filename}")
                    skipped_count += 1
                    continue
                
                # Generate files for this job
                print(f"📄 Generating resume and cover letter for row {row_number}...")
                resume_path, cv_path = generate_resume_and_cover_letter(
                    job_description=job_description,
                    old_resume_path=resume_file
                )
                
                if resume_path and cv_path:
                    resume_filename = os.path.basename(resume_path)
                    coverletter_filename = os.path.basename(cv_path)
                    
                    # Update CSV with filenames
                    update_csv_with_filenames(
                        csv_file_path=csv_file,
                        row_index=row_index,
                        resume_filename=resume_filename,
                        coverletter_filename=coverletter_filename
                    )
                    
                    print(f"✅ Successfully generated files for row {row_number}")
                    print(f"   Resume: {resume_filename}")
                    print(f"   Cover Letter: {coverletter_filename}")
                    success_count += 1
                else:
                    print(f"❌ Failed to generate files for row {row_number}")
                    error_count += 1
                
            except Exception as e:
                print(f"❌ Error processing row {row_number}: {e}")
                error_count += 1
                continue
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📊 BATCH FILE GENERATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total jobs processed: {end_row - start_row + 1}")
        print(f"Successful generations: {success_count}")
        print(f"Failed generations: {error_count}")
        print(f"Skipped (files already exist): {skipped_count}")
        print(f"Success rate: {(success_count / (end_row - start_row + 1)) * 100:.1f}%")
        print(f"Files saved to: generated/")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

def check_existing_files(csv_file):
    """Check which jobs already have files generated"""
    try:
        df = pd.read_csv(csv_file)
        total_rows = len(df)
        
        if total_rows == 0:
            print("No jobs found in CSV file")
            return
        
        print(f"📋 Checking existing files for {total_rows} jobs...")
        print("=" * 50)
        
        files_exist = 0
        files_missing = 0
        
        for row_number in range(1, total_rows + 1):
            current_resume_filename = df.iloc[row_number - 1].get('resume_filename', '').strip()
            current_cover_letter_filename = df.iloc[row_number - 1].get('coverletter_filename', '').strip()
            
            base_generated_path = "generated"
            resume_path = os.path.join(base_generated_path, current_resume_filename) if current_resume_filename else None
            cover_letter_path = os.path.join(base_generated_path, current_cover_letter_filename) if current_cover_letter_filename else None
            
            if (current_resume_filename and current_cover_letter_filename and 
                os.path.isfile(resume_path) and os.path.isfile(cover_letter_path)):
                files_exist += 1
                print(f"✅ Row {row_number}: Files exist")
            else:
                files_missing += 1
                print(f"❌ Row {row_number}: Files missing")
        
        print(f"\n📊 Summary:")
        print(f"Jobs with files: {files_exist}")
        print(f"Jobs missing files: {files_missing}")
        print(f"Completion: {(files_exist / total_rows) * 100:.1f}%")
        
    except Exception as e:
        print(f"Error checking files: {e}")

def main():
    parser = argparse.ArgumentParser(description='Generate resume and cover letter files for all jobs in a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file containing job URLs')
    parser.add_argument('--start-from', type=int, default=1, help='Starting row number (default: 1)')
    parser.add_argument('--max-jobs', type=int, help='Maximum number of jobs to process')
    parser.add_argument('--resume-file', default='Umair_resume.pdf', help='Path to the old resume file (default: Umair_resume.pdf)')
    parser.add_argument('--check-only', action='store_true', help='Only check existing files, do not generate')
    
    args = parser.parse_args()
    
    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found")
        sys.exit(1)
    
    # Check if resume file exists
    if not os.path.exists(args.resume_file):
        print(f"Error: Resume file '{args.resume_file}' not found")
        sys.exit(1)
    
    # Check only mode
    if args.check_only:
        check_existing_files(args.csv_file)
        return
    
    # Generate files
    generate_files_for_csv(args.csv_file, args.start_from, args.max_jobs, args.resume_file)

if __name__ == "__main__":
    main() 