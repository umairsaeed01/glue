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

def update_csv_with_application_status(job_url, row_number=None, status="Applied", csv_file_path="software_engineer.csv"):
    """
    Update CSV file with application status.
    Creates 'Applied' column if it doesn't exist, then adds status and date.
    """
    try:
        # Use the provided CSV file and row number
        if not os.path.exists(csv_file_path):
            print(f"[Success Handler] CSV file not found: {csv_file_path}")
            return False
        print(f"[Success Handler] Updating row {row_number} in {csv_file_path}")
        
        # Read existing CSV data
        rows = []
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            
            # Add 'Applied' column if it doesn't exist
            if 'Applied' not in fieldnames:
                fieldnames.append('Applied')
                print("[Success Handler] Created 'Applied' column")
            
            # Add 'Application Date' column if it doesn't exist
            if 'Application Date' not in fieldnames:
                fieldnames.append('Application Date')
                print("[Success Handler] Created 'Application Date' column")
            
            # Process each row
            for i, row in enumerate(reader, start=1):
                # Update the specific row number
                if i == row_number:
                    # Update this row with application status
                    row['Applied'] = status
                    row['Application Date'] = datetime.now().strftime('%d %B %Y')  # e.g., "23 June 2025"
                    print(f"[Success Handler] Updated row {row_number} with status: {status}")
                
                rows.append(row)
        
        # Write back to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"[Success Handler] Successfully updated CSV with application status")
        return True
        
    except Exception as e:
        print(f"[Success Handler] Error updating CSV: {e}")
        return False

def handle_success_page(driver, job_url, row_number=None):
    """
    Handle the success page after job application submission.
    
    Args:
        driver: Selenium WebDriver instance
        job_url: The original job URL
        row_number: The row number in the original CSV file to update
        
    Returns:
        str: 'SUCCESS_COMPLETE' if success page was handled successfully and should exit
             True if success page was handled but continue processing
             False if not on success page or handling failed
    """
    try:
        print("[Success Handler] Processing success page...")
        
        # Wait for success page to load
        time.sleep(2)
        
        # Check if we're on the success page
        current_url = driver.current_url
        if "/apply/success" not in current_url:
            print("[Success Handler] Not on success page")
            return False
        
        # Look for success indicators
        success_indicators = [
            "//h1[contains(text(), 'Application submitted')]",
            "//h1[contains(text(), 'Success')]",
            "//h1[contains(text(), 'Good luck')]",  # New: matches "Good luck, Umair"
            "//h1[@id='applicationSent']",  # New: matches the specific ID
            "//span[contains(text(), 'Your application has been sent')]",  # New: matches the specific text
            "//div[contains(text(), 'Your application has been submitted')]",
            "//div[contains(text(), 'Application submitted successfully')]",
            "//div[contains(text(), 'Thank you for your application')]"
        ]
        
        success_found = False
        for indicator in success_indicators:
            try:
                element = driver.find_element(By.XPATH, indicator)
                if element.is_displayed():
                    print(f"[Success Handler] Found success indicator: {indicator}")
                    success_found = True
                    break
            except NoSuchElementException:
                continue
        
        if not success_found:
            # Check page title
            page_title = driver.title.lower()
            if "success" in page_title or "submitted" in page_title:
                success_found = True
                print("[Success Handler] Success indicated by page title")
        
        # Additional check: Look for specific success messages in page source
        if not success_found:
            page_source = driver.page_source
            success_texts = [
                "Good luck",
                "Your application has been sent",
                "application has been sent",
                "Application submitted",
                "Thank you for your application"
            ]
            
            for text in success_texts:
                if text in page_source:
                    print(f"[Success Handler] Found success text in page source: '{text}'")
                    success_found = True
                    break
        
        if success_found:
            print("[Success Handler] ✅ Job applied successfully!")
            
            # Update CSV with application status
            if update_csv_with_application_status(job_url, row_number):
                print("[Success Handler] ✅ CSV updated successfully")
            else:
                print("[Success Handler] ⚠️ Failed to update CSV")
            
            # Return special value to indicate application is complete
            return 'SUCCESS_COMPLETE'
        else:
            # Fallback: If we're on the success URL and can't find specific indicators,
            # but the URL pattern is correct, consider it a success
            if "/apply/success" in current_url:
                print("[Success Handler] ⚠️ Could not find specific success indicators, but URL indicates success page")
                print("[Success Handler] ✅ Assuming job applied successfully based on URL!")
                
                # Update CSV with application status
                if update_csv_with_application_status(job_url, row_number):
                    print("[Success Handler] ✅ CSV updated successfully")
                else:
                    print("[Success Handler] ⚠️ Failed to update CSV")
                
                # Return special value to indicate application is complete
                return 'SUCCESS_COMPLETE'
            else:
                print("[Success Handler] Could not confirm success - page may have changed")
                return False
        
    except Exception as e:
        print(f"[Success Handler] Error handling success page: {e}")
        return False 