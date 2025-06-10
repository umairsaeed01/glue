import time
from urllib.parse import quote_plus, urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime
import re
import os
import csv


def extract_email(text: str) -> str:
    """Extract email address from text."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    """Extract phone number from text."""
    # Match various phone number formats
    phone_patterns = [
        r'\b\d{2}[- ]?\d{4}[- ]?\d{4}\b',  # 02-1234-5678
        r'\b\d{3}[- ]?\d{3}[- ]?\d{3}\b',  # 123-456-789
        r'\b\d{4}[- ]?\d{3}[- ]?\d{3}\b',  # 1234-567-890
        r'\b\+61[- ]?\d{1,2}[- ]?\d{4}[- ]?\d{4}\b',  # +61 2 1234 5678
        r'\b\(\+61\)[- ]?\d{1,2}[- ]?\d{4}[- ]?\d{4}\b'  # (+61) 2 1234 5678
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""


def extract_salary(text: str) -> str:
    """Extract salary information from text."""
    # Common salary patterns
    salary_patterns = [
        r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|-)?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)?\s*(?:per\s+(?:year|annum|month|week|hour)|p\.?a\.?|p\.?m\.?|p\.?w\.?|p\.?h\.?)?',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|-)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)?\s*(?:k|K)\s*(?:per\s+(?:year|annum|month|week|hour)|p\.?a\.?|p\.?m\.?|p\.?w\.?|p\.?h\.?)?',
        r'Salary:\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|-)?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)?',
        r'Remuneration:\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|-)?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)?'
    ]
    
    for pattern in salary_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean up the matched salary
            salary = match.group(0).strip()
            # Remove extra spaces and standardize format
            salary = re.sub(r'\s+', ' ', salary)
            return salary
    return ""


def get_job_description(driver, job_url: str, max_retries: int = 3) -> str:
    """Extract job description from the job detail page."""
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Attempting to fetch description from: {job_url}")
            driver.get(job_url)
            time.sleep(5)  # increased wait time for page load
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 15)
            
            # Try different selectors for job description based on actual HTML structure
            selectors = [
                "div[data-automation='jobAdDetails']",  # Primary selector from actual HTML
                "div._1oozmqe0.bmnci70",  # Class-based selector from actual HTML
                "div[data-automation='jobAdDetails'] div._1oozmqe0.bmnci70",  # Combined selector
                "div._1oozmqe0.l218ib5b.l218ibhf.l218ib6z",  # Outer container class
                "div[data-automation='jobDescription']",  # Fallback to automation attribute
                "div[data-automation='jobDescriptionText']",  # Another fallback
                ".job-description",  # Generic class fallback
                ".job-description__content"  # Another generic class fallback
            ]
            
            # Debug: Print page source to see what we're getting
            print("[DEBUG] Page source length:", len(driver.page_source))
            
            for selector in selectors:
                try:
                    print(f"[DEBUG] Trying selector: {selector}")
                    desc_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    text = desc_elem.text.strip()
                    if text:  # Only return if we found actual text
                        print(f"[DEBUG] Found description with selector: {selector}")
                        return text
                except Exception as e:
                    print(f"[DEBUG] Selector {selector} failed: {str(e)}")
                    continue
            
            # If we get here, try to find any element with job description in its class or data-automation
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, "[class*='description'], [data-automation*='description'], [class*='jobAdDetails']")
                for elem in elements:
                    text = elem.text.strip()
                    if text:
                        print("[DEBUG] Found description using wildcard selector")
                        return text
            except:
                pass
                
            return "Description not found"
        except Exception as e:
            print(f"[WARN] Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            return f"Error fetching description after {max_retries} attempts"


def extract_job_id_from_url(url: str) -> str:
    """Extract the numeric job ID from a Seek URL."""
    try:
        # Parse the URL
        parsed = urlparse(url)
        # Get the path and remove leading/trailing slashes
        path = parsed.path.strip('/')
        # Split by '/' and get the last part
        job_id = path.split('/')[-1]
        # Remove any query parameters
        job_id = job_id.split('?')[0]
        return job_id
    except:
        return "unknown"


def load_existing_jobs(filename: str) -> dict:
    """Load existing jobs from CSV file if it exists."""
    existing_jobs = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_jobs[row['job_id']] = row
            print(f"[INFO] Loaded {len(existing_jobs)} existing jobs from {filename}")
        except Exception as e:
            print(f"[WARN] Failed to load existing jobs: {e}")
    return existing_jobs


def save_jobs_to_csv(filename: str, jobs: list, fieldnames: list) -> bool:
    """Save jobs to CSV file, handling both new and existing files."""
    try:
        # Check if file exists
        file_exists = os.path.exists(filename)
        
        if file_exists:
            # If file exists, only append new jobs
            existing_jobs = load_existing_jobs(filename)
            existing_ids = set(job['job_id'] for job in existing_jobs.values())
            new_jobs = [job for job in jobs if job['job_id'] not in existing_ids]
            
            if not new_jobs:
                print("[INFO] No new jobs to append")
                return True
                
            # Append only new jobs
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerows(new_jobs)
            print(f"[INFO] Appended {len(new_jobs)} new jobs to {filename}")
        else:
            # If file doesn't exist, create new file with all jobs
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(jobs)
            print(f"[INFO] Created new file {filename} with {len(jobs)} jobs")
        
        return True
    except Exception as e:
        print(f"[WARN] Failed to save jobs to CSV: {e}")
        return False


def scrape_seek_jobs(title: str, location: str, limit: int) -> dict:
    """
    Scrape up to `limit` jobs from seek.com.au for the given title+location.
    
    Args:
        title: Job title to search for
        location: Location to search in
        limit: Maximum number of jobs to scrape
        
    Returns:
        dict: Either {
            "jobs": [{"job_id": str, "title": str, "company": str, "location": str, "url": str, "description": str, "email": str, "phone": str, "salary": str}, ...],
            "csv_file": str  # path to saved CSV file
        } or {"error": str} if something went wrong
    """
    # --- set up headless Firefox ---
    opts = Options()
    opts.headless = True
    driver = webdriver.Firefox(options=opts, service=Service())
    new_jobs = []  # Store only new job listings
    page = 1
    consecutive_empty_pages = 0  # Track consecutive pages with no new jobs
    max_empty_pages = 3  # Stop after 3 consecutive empty pages

    # Prepare filename
    safe_title = title.lower().replace(' ', '_')
    csv_file = f"{safe_title}.csv"
    
    # Load existing jobs
    existing_jobs = load_existing_jobs(csv_file)
    print(f"[INFO] Found {len(existing_jobs)} existing jobs")

    try:
        # First, collect all job listings
        while len(new_jobs) < limit and consecutive_empty_pages < max_empty_pages:
            # 1) construct search URL with correct format
            q_title = title.lower().replace(' ', '-')
            q_loc = location.lower().replace(' ', '-')
            
            # First page has a different URL format
            if page == 1:
                url = f"https://www.seek.com.au/{q_title}-jobs/in-{q_loc}"
            else:
                url = f"https://www.seek.com.au/{q_title}-jobs/in-{q_loc}?page={page}"
                
            print(f"[DEBUG] Fetching page {page}: {url}")
            driver.get(url)
            time.sleep(3)  # increased wait time

            # 2) find all job cards on this page
            try:
                cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-automation='normalJob']"))
                )
                
                if not cards:
                    print("[DEBUG] No job cards found with article selector, trying alternative selectors...")
                    cards = driver.find_elements(By.CSS_SELECTOR, "[data-automation='normalJob']")
                    if not cards:
                        cards = driver.find_elements(By.CSS_SELECTOR, "[data-automation='jobCard']")
                
                if not cards:
                    print(f"[DEBUG] No job cards found on page {page}, stopping.")
                    break
                
                print(f"[DEBUG] Found {len(cards)} job cards on page {page}")
                new_jobs_on_page = 0

                # 3) pull data out of each card
                for card in cards:
                    if len(new_jobs) >= limit:
                        break
                        
                    try:
                        # Get job title and URL
                        title_elem = card.find_element(By.CSS_SELECTOR, "[data-automation='jobTitle']")
                        job_title = title_elem.text
                        job_url = title_elem.get_attribute("href")
                        
                        if not job_url:
                            continue
                            
                        # Extract job ID from URL
                        job_id = extract_job_id_from_url(job_url)
                        
                        # Skip if we already have this job
                        if job_id in existing_jobs:
                            print(f"[DEBUG] Skipping existing job: {job_title}")
                            continue
                        
                        # Get company name
                        try:
                            company = card.find_element(By.CSS_SELECTOR, "[data-automation='jobCompany']").text
                        except:
                            company = "Unknown Company"
                        
                        # Get location
                        try:
                            loc = card.find_element(By.CSS_SELECTOR, "[data-automation='jobLocation']").text
                        except:
                            loc = "Unknown Location"

                        new_jobs.append({
                            "job_id": job_id,
                            "title": job_title,
                            "company": company,
                            "location": loc,
                            "url": job_url  # Keep original URL
                        })
                        new_jobs_on_page += 1
                        print(f"[DEBUG] Found new job listing: {job_title} at {company}")
                    except Exception as e:
                        print(f"[WARN] Failed to extract job card: {str(e)}")
                        continue

                print(f"[DEBUG] Page {page} scraped: {new_jobs_on_page} new jobs found on this page, {len(new_jobs)} total new jobs so far.")
                
                # Update consecutive empty pages counter
                if new_jobs_on_page == 0:
                    consecutive_empty_pages += 1
                    print(f"[DEBUG] No new jobs found on page {page}. Consecutive empty pages: {consecutive_empty_pages}")
                else:
                    consecutive_empty_pages = 0  # Reset counter if we found new jobs
                    
                page += 1
                time.sleep(2)  # polite crawling
                
            except Exception as e:
                print(f"[WARN] Error processing page {page}: {str(e)}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_empty_pages:
                    break
                page += 1
                continue

        # Now get descriptions for each new job
        print(f"\n[DEBUG] Getting descriptions for {len(new_jobs)} new jobs...")
        for job in new_jobs:
            try:
                description = get_job_description(driver, job["url"])
                job["description"] = description
                
                # Extract additional information from description
                job["email"] = extract_email(description)
                job["phone"] = extract_phone(description)
                job["salary"] = extract_salary(description)
                
                print(f"[DEBUG] Got description for: {job['title']} at {job['company']}")
                time.sleep(2)  # polite crawling
            except Exception as e:
                print(f"[WARN] Failed to get description for {job['title']}: {str(e)}")
                job["description"] = "Error fetching description"
                job["email"] = ""
                job["phone"] = ""
                job["salary"] = ""

    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

    # Save to CSV
    fieldnames = ["job_id", "title", "company", "location", "url", "description", "email", "phone", "salary"]
    if save_jobs_to_csv(csv_file, new_jobs, fieldnames):
        print(f"[INFO] Successfully processed {len(new_jobs)} new jobs")
    else:
        print(f"[WARN] Failed to save jobs to {csv_file}")
        csv_file = None

    return {
        "new_jobs": new_jobs,
        "csv_file": csv_file,
        "new_jobs_count": len(new_jobs),
        "existing_jobs_count": len(existing_jobs)
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print(json.dumps({"error": "Usage: python seek_scraper.py 'title' 'loc' 'count'"}))
        sys.exit(1)
    
    result = scrape_seek_jobs(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    print(json.dumps(result, indent=2)) 