from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
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

def update_csv_with_job_unavailable(job_url, row_number=None, status="Not Available", csv_file_path="software_engineer.csv"):
    """
    Update CSV file with job unavailable status.
    Creates 'Applied' column if it doesn't exist, then adds status and date.
    """
    try:
        # Use the provided CSV file and row number
        if not os.path.exists(csv_file_path):
            print(f"[Job Unavailable Handler] CSV file not found: {csv_file_path}")
            return False
        print(f"[Job Unavailable Handler] Updating row {row_number} in {csv_file_path}")
        
        # Read existing CSV data
        rows = []
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            
            # Add 'Applied' column if it doesn't exist
            if 'Applied' not in fieldnames:
                fieldnames.append('Applied')
                print("[Job Unavailable Handler] Created 'Applied' column")
            
            # Add 'Application Date' column if it doesn't exist
            if 'Application Date' not in fieldnames:
                fieldnames.append('Application Date')
                print("[Job Unavailable Handler] Created 'Application Date' column")
            
            # Process each row
            for i, row in enumerate(reader, start=1):
                # Update the specific row number
                if i == row_number:
                    # Update this row with job unavailable status
                    row['Applied'] = status
                    row['Application Date'] = datetime.now().strftime('%d %B %Y')  # e.g., "23 June 2025"
                    print(f"[Job Unavailable Handler] Updated row {row_number} with status: {status}")
                
                rows.append(row)
        
        # Write back to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"[Job Unavailable Handler] Successfully updated CSV with job unavailable status")
        return True
        
    except Exception as e:
        print(f"[Job Unavailable Handler] Error updating CSV: {e}")
        return False

def handle_job_unavailable(driver, job_url=None, row_number=None):
    """
    Handle cases where the job is no longer available.
    Detects various error indicators and provides appropriate logging.
    Also updates CSV with "Not Available" status.
    
    Args:
        driver: Selenium WebDriver instance
        job_url: The original job URL (optional, for CSV updates)
        row_number: The row number in the original CSV file to update
        
    Returns:
        bool: True if job is unavailable (should stop automation), False otherwise
    """
    try:
        print("[Job Unavailable Handler] Checking for job unavailability indicators...")
        
        # Method 1: Check for the specific SEEK "no longer advertised" message
        try:
            # Look for the exact text from the HTML you provided
            unavailable_h2 = driver.find_element(By.XPATH, "//h2[contains(text(), 'This job is no longer advertised')]")
            if unavailable_h2.is_displayed():
                print("[Job Unavailable Handler] Found 'This job is no longer advertised' message")
                
                # Update CSV with job unavailable status
                if job_url and row_number:
                    if update_csv_with_job_unavailable(job_url, row_number, csv_file_path=csv_file_path):
                        print("[Job Unavailable Handler] ✅ CSV updated with 'Not Available' status")
                    else:
                        print("[Job Unavailable Handler] ⚠️ Failed to update CSV")
                
                return True
        except NoSuchElementException:
            pass
        
        # Method 2: Check for specific error messages in page content
        error_messages = [
            "This job is no longer available",
            "This job is no longer advertised",
            "Job has been removed",
            "Position has been filled",
            "This position is no longer accepting applications",
            "Job not found",
            "Page not found",
            "404",
            "The job you're looking for doesn't exist",
            "Jobs remain on SEEK for 30 days"
        ]
        
        page_source = driver.page_source.lower()
        for message in error_messages:
            if message.lower() in page_source:
                print(f"[Job Unavailable Handler] Found error message: '{message}'")
                
                # Update CSV with job unavailable status
                if job_url and row_number:
                    if update_csv_with_job_unavailable(job_url, row_number, csv_file_path=csv_file_path):
                        print("[Job Unavailable Handler] ✅ CSV updated with 'Not Available' status")
                    else:
                        print("[Job Unavailable Handler] ⚠️ Failed to update CSV")
                
                return True
        
        # Method 3: Check for error elements by XPath (more specific to SEEK)
        error_selectors = [
            "//h2[contains(text(), 'This job is no longer advertised')]",
            "//h2[contains(text(), 'Job not found')]",
            "//h2[contains(text(), 'Page not found')]",
            "//h2[contains(text(), '404')]",
            "//div[contains(text(), 'This job is no longer available')]",
            "//div[contains(text(), 'Job has been removed')]",
            "//div[contains(text(), 'Position has been filled')]",
            "//div[contains(text(), 'Jobs remain on SEEK for 30 days')]",
            "//div[contains(@class, 'error')]",
            "//div[contains(@class, 'not-found')]",
            "//div[contains(@class, 'unavailable')]",
            "//div[contains(@class, 'expired')]"
        ]
        
        for selector in error_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    print(f"[Job Unavailable Handler] Found error element: {selector}")
                    
                    # Update CSV with job unavailable status
                    if job_url and row_number:
                        if update_csv_with_job_unavailable(job_url, row_number, csv_file_path=csv_file_path):
                            print("[Job Unavailable Handler] ✅ CSV updated with 'Not Available' status")
                        else:
                            print("[Job Unavailable Handler] ⚠️ Failed to update CSV")
                    
                    return True
            except NoSuchElementException:
                continue
        
        # Method 4: Check page title for error indicators
        page_title = driver.title.lower()
        title_error_indicators = [
            "not found",
            "404",
            "error",
            "unavailable",
            "removed",
            "expired",
            "no longer advertised"
        ]
        
        for indicator in title_error_indicators:
            if indicator in page_title:
                print(f"[Job Unavailable Handler] Found error in page title: '{indicator}'")
                
                # Update CSV with job unavailable status
                if job_url and row_number:
                    if update_csv_with_job_unavailable(job_url, row_number, csv_file_path=csv_file_path):
                        print("[Job Unavailable Handler] ✅ CSV updated with 'Not Available' status")
                    else:
                        print("[Job Unavailable Handler] ⚠️ Failed to update CSV")
                
                return True
        
        # Method 5: Check URL for error patterns
        current_url = driver.current_url.lower()
        if "error" in current_url or "404" in current_url:
            print("[Job Unavailable Handler] Found error in URL")
            
            # Update CSV with job unavailable status
            if job_url and row_number:
                if update_csv_with_job_unavailable(job_url, row_number, csv_file_path=csv_file_path):
                    print("[Job Unavailable Handler] ✅ CSV updated with 'Not Available' status")
                else:
                    print("[Job Unavailable Handler] ⚠️ Failed to update CSV")
            
            return True
        
        print("[Job Unavailable Handler] Job appears to be available")
        return False
        
    except Exception as e:
        print(f"[Job Unavailable Handler] Error detecting job availability: {e}")
        return False 