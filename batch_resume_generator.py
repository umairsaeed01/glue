#!/usr/bin/env python3
import csv
import os
import sys
import argparse
from datetime import datetime
import pandas as pd

# Import the resume generation function
from local_generate import process_job

def generate_resumes_for_csv(csv_file, start_row=1, max_jobs=None, resume_file="Umair_resume.pdf"):
    """
    Generate resumes for all jobs in a CSV file
    
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
        
        print(f"Starting batch resume generation for jobs from row {start_row} to {end_row} (out of {total_rows} total)")
        print(f"Using resume file: {resume_file}")
        print("=" * 70)
        
        success_count = 0
        error_count = 0
        
        for row_number in range(start_row, end_row + 1):
            print(f"\n{'='*25} Processing Row {row_number}/{end_row} {'='*25}")
            
            try:
                # Get job URL from CSV
                job_url = df.iloc[row_number - 1]['url'].strip()
                
                if not job_url:
                    print(f"❌ Row {row_number}: Empty URL, skipping...")
                    error_count += 1
                    continue
                
                print(f"🔗 Job URL: {job_url}")
                
                # Generate resume for this job
                print(f"📄 Generating resume for row {row_number}...")
                result = process_job(csv_file, row_number, resume_file)
                
                if result:
                    print(f"✅ Successfully generated resume for row {row_number}")
                    success_count += 1
                else:
                    print(f"❌ Failed to generate resume for row {row_number}")
                    error_count += 1
                
            except Exception as e:
                print(f"❌ Error processing row {row_number}: {e}")
                error_count += 1
                continue
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*70}")
        print(f"Total jobs processed: {end_row - start_row + 1}")
        print(f"Successful generations: {success_count}")
        print(f"Failed generations: {error_count}")
        print(f"Success rate: {(success_count / (end_row - start_row + 1)) * 100:.1f}%")
        print(f"Resumes saved to: generated/")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

def main():
    parser = argparse.ArgumentParser(description='Generate resumes for all jobs in a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file containing job URLs')
    parser.add_argument('--start-from', type=int, default=1, help='Starting row number (default: 1)')
    parser.add_argument('--max-jobs', type=int, help='Maximum number of jobs to process')
    parser.add_argument('--resume-file', default='Umair_resume.pdf', help='Path to the old resume file (default: Umair_resume.pdf)')
    
    args = parser.parse_args()
    
    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found")
        sys.exit(1)
    
    # Check if resume file exists
    if not os.path.exists(args.resume_file):
        print(f"Error: Resume file '{args.resume_file}' not found")
        sys.exit(1)
    
    # Generate resumes
    generate_resumes_for_csv(args.csv_file, args.start_from, args.max_jobs, args.resume_file)

if __name__ == "__main__":
    main() 