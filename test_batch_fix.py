#!/usr/bin/env python3
"""
Test script to verify the batch processing fix works correctly.
This script will test a single job to ensure the return value logic is working.
"""

import sys
import os

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apply_from_csv import process_single_job, check_job_status

def test_single_job():
    """Test processing a single job to verify the fix"""
    print("🧪 Testing batch processing fix...")
    print("=" * 50)
    
    csv_file_path = "software_engineer.csv"
    base_generated_path = "/Users/umairsaeed/Documents/ai/glue/generated"
    
    # Check if CSV exists
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    # Test with row 1
    test_row = 1
    
    print(f"📋 Testing with row {test_row}")
    
    # Check initial status
    initial_status = check_job_status(test_row, csv_file_path)
    print(f"📊 Initial status: {initial_status if initial_status else 'Unprocessed'}")
    
    # Process the job
    print(f"\n🔄 Processing job...")
    success = process_single_job(test_row, csv_file_path, base_generated_path)
    
    # Check final status
    final_status = check_job_status(test_row, csv_file_path)
    print(f"📊 Final status: {final_status if final_status else 'Unprocessed'}")
    
    print(f"\n✅ Test completed!")
    print(f"   Success: {success}")
    print(f"   Status: {final_status}")
    
    return success

if __name__ == "__main__":
    test_single_job() 