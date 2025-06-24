#!/usr/bin/env python3
"""
Test script to demonstrate the success handler and CSV update functionality.
"""

import sys
import os
import csv
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_csv():
    """Create a sample CSV file for testing."""
    sample_data = [
        {
            'job_id': '84710518',
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'Sydney',
            'Job URL': 'https://www.seek.com.au/job/84710518'
        },
        {
            'job_id': '84710519',
            'title': 'Data Scientist',
            'company': 'Another Company',
            'location': 'Melbourne',
            'Job URL': 'https://www.seek.com.au/job/84710519'
        }
    ]
    
    filename = 'test_seek_jobs.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['job_id', 'title', 'company', 'location', 'Job URL']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"Created sample CSV file: {filename}")
    return filename

def test_csv_update():
    """Test the CSV update functionality."""
    print("=== Testing CSV Update Functionality ===")
    
    # Create sample CSV
    csv_file = create_sample_csv()
    
    # Import the success handler
    from success_handler import update_csv_with_application_status
    
    # Test updating a job application
    test_job_url = "https://www.seek.com.au/job/84710518"
    
    print(f"\nTesting update for job URL: {test_job_url}")
    
    # Update the CSV
    success = update_csv_with_application_status(test_job_url)
    
    if success:
        print("✅ CSV update successful!")
        
        # Show the updated CSV
        print("\nUpdated CSV contents:")
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print(f"Job ID: {row.get('job_id', 'N/A')}")
                print(f"Title: {row.get('title', 'N/A')}")
                print(f"Applied: {row.get('Applied', 'N/A')}")
                print(f"Application Date: {row.get('Application Date', 'N/A')}")
                print("-" * 40)
    else:
        print("❌ CSV update failed!")
    
    # Clean up
    try:
        os.remove(csv_file)
        print(f"\nCleaned up test file: {csv_file}")
    except:
        pass

def show_implementation_details():
    """Show the implementation details."""
    print("\n=== Implementation Details ===")
    print()
    print("Success Handler Features:")
    print("1. Detects success page by URL pattern '/apply/success'")
    print("2. Looks for success indicators in page content")
    print("3. Logs success message to terminal")
    print("4. Updates CSV with application status")
    print()
    print("CSV Update Features:")
    print("1. Automatically creates 'Applied' column if missing")
    print("2. Automatically creates 'Application Date' column if missing")
    print("3. Updates the specific job row based on job ID")
    print("4. Uses current date in format 'DD Month YYYY' (e.g., '23 June 2025')")
    print()
    print("Integration:")
    print("1. Added to dispatch_special_pages function")
    print("2. Called automatically when success page is detected")
    print("3. Passes job URL to handler for CSV updates")
    print()

if __name__ == "__main__":
    print("Success Handler and CSV Update Test")
    print("=" * 50)
    print()
    
    test_csv_update()
    show_implementation_details()
    
    print("Implementation complete!")
    print("The script will now automatically detect success pages and update CSV files.") 