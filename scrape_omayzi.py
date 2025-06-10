import sys
import json
import csv
import os
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re # Keep regex for contact info

# --- Helper Functions ---
def format_for_url(text):
    """Formats text for Seek URL: lowercase, spaces to hyphens."""
    return text.lower().replace(' ', '-')

def get_driver():
    """Initializes and returns a Selenium WebDriver."""
    print("Python: Initializing WebDriver...", file=sys.stderr)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    print("Python: WebDriver Initialized.", file=sys.stderr)
    return driver

def extract_contact_info(text):
    """Extracts phone numbers and email addresses from text."""
    # Simple regex for phone numbers (adjust as needed for different formats)
    phone_regex = r'(\(?\+?\d{1,3}\)?[\s.-]?\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4})'
    # Simple regex for emails
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    phones = re.findall(phone_regex, text)
    emails = re.findall(email_regex, text)

    # Filter out unlikely short numbers that might be IDs etc.
    phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 8]

    phone_str = ', '.join(phones) if phones else '-'
    email_str = ', '.join(emails) if emails else '-'
    return phone_str, email_str

def get_job_links_from_search(driver, jobTitle, location, numJobs_limit):
    """Gets job links from the Seek search results page."""
    print(f"Python: Getting job links for title='{jobTitle}', location='{location}', limit='{numJobs_limit}'", file=sys.stderr)
    formatted_title = format_for_url(jobTitle)
    formatted_location = format_for_url(location)
    base_url = "https://www.seek.com.au"
    search_url = f'{base_url}/{formatted_title}-jobs/in-{formatted_location}'
    print(f"Python: Navigating to search URL: {search_url}", file=sys.stderr)

    try:
        driver.get(search_url)
        # Wait for job cards using Selenium's WebDriverWait
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//article[@data-card-type='JobCard']"))
        )
        print("Python: Search results page loaded.", file=sys.stderr)
        time.sleep(2) # Extra pause
        html_content = driver.page_source
    except Exception as e:
        print(f"Python: Error loading search results page {search_url}: {e}", file=sys.stderr)
        return [] # Return empty list on error

    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    # Use find_all with limit if possible, otherwise loop and break
    job_cards = soup.find_all('article', attrs={'data-card-type': 'JobCard'})
    print(f"Python: Found {len(job_cards)} potential job cards on search page.", file=sys.stderr)

    for job_card in job_cards:
        if len(links) >= numJobs_limit:
            print(f"Python: Reached job link limit of {numJobs_limit}.", file=sys.stderr)
            break

        # Try finding the link within the h3 tag first (more specific)
        link_element = job_card.find('h3', {'data-automation': 'job-title'})
        if link_element:
             link_element = link_element.find('a') # Get the 'a' tag inside h3

        # Fallback selectors from scrape_seek.py
        if not link_element:
             link_element = job_card.find('a', {'data-automation': 'jobTitle'})
        if not link_element:
             link_element = job_card.find('a', href=re.compile(r'/job/')) # General fallback

        if link_element and link_element.has_attr('href'):
            href = link_element['href']
            if href.startswith('/job/'):
                full_url = base_url + href.split('?')[0] # Clean URL parameters
                if full_url not in links: # Avoid duplicates
                    links.append(full_url)
        else:
            print("Python: Found job card without a valid title link.", file=sys.stderr)

    print(f"Python: Extracted {len(links)} unique job links.", file=sys.stderr)
    return links

def scrape_job_details(driver, job_url):
    """Scrapes detailed information from a single job page using logic from scrape_seek.py."""
    print(f"Python: Scraping details from: {job_url}", file=sys.stderr)
    details = {
        "Job Title": "-", "Company Name": "-", "Location": "-", "Salary/Pay Range": "-",
        "Key Responsibilities": "-", "Required Skills/Qualifications": "-", "Date Posted": "-",
        "Job Type": "-", "Phone Number": "-", "Email": "-", "Full Job Description": "-",
        "Job URL": job_url
    }

    try:
        driver.get(job_url)
        # Wait for a common element, maybe the job title or description area
        WebDriverWait(driver, 15).until(
             EC.presence_of_element_located((By.XPATH, "//h1[@data-automation='job-detail-title'] | //div[@data-automation='jobAdDetails'] | //div[contains(@class,'job-description')]"))
        )
        print(f"Python: Job details page loaded: {job_url}", file=sys.stderr)
        time.sleep(2) # Increased pause slightly
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- Extract data using BeautifulSoup - Selectors adapted from scrape_seek.py ---

        # Title
        title = soup.find('h1', {'data-automation': 'job-detail-title'})
        details["Job Title"] = title.text.strip() if title else '-'
        if details["Job Title"] == '-': # Fallback selector
             title = soup.find('h1', class_=lambda x: x and 'JobTitle' in x) # Approximate class match
             details["Job Title"] = title.text.strip() if title else '-'

        # Company
        company = soup.find('span', {'data-automation': 'advertiser-name'})
        details["Company Name"] = company.text.strip() if company else '-'
        if details["Company Name"] == '-' : # Fallback using link
             company_link = soup.find('a', {'data-automation': 'job-header-company-name'}) # Check if this exists
             details["Company Name"] = company_link.text.strip() if company_link else '-'
        if details["Company Name"] == '-': # Generic fallback
             company = soup.find('span', class_=lambda x: x and 'AdvertiserName' in x) # Approximate class match
             details["Company Name"] = company.text.strip() if company else '-'

        # Location
        location_element = soup.find('span', {'data-automation': 'job-detail-location'})
        details["Location"] = location_element.text.strip() if location_element else '-'
        # Note: Fallbacks for location from scrape_seek.py were complex and might need more context, skipping for now.

        # Salary
        salary = soup.find('span', {'data-automation': 'job-detail-salary'})
        details["Salary/Pay Range"] = salary.text.strip() if salary else '-'
        # Skipping generic fallback for salary as it's often unreliable

        # Job Type / Classification (Simplified approach)
        job_type_element = soup.find('span', {'data-automation': 'job-detail-work-type'})
        details["Job Type"] = job_type_element.text.strip() if job_type_element else '-'
        # Could add classification logic here if needed

        # Date Posted
        date_posted_element = soup.find('span', {'data-automation': 'job-detail-date'})
        details["Date Posted"] = date_posted_element.text.strip() if date_posted_element else '-'
        # Skipping generic fallback

        # Full description
        description_div = soup.find('div', {'data-automation': 'jobAdDetails'})
        details["Full Job Description"] = description_div.get_text(separator='\n', strip=True) if description_div else '-'
        if details["Full Job Description"] == '-': # Fallback
             description_div = soup.find('div', class_=lambda x: x and 'job-description' in x) # Approximate class match
             details["Full Job Description"] = description_div.get_text(separator='\n', strip=True) if description_div else '-'

        # Extract Responsibilities & Skills (Placeholder - requires specific logic based on description structure)
        details["Key Responsibilities"] = "See Full Description"
        details["Required Skills/Qualifications"] = "See Full Description"

        # Extract contacts using the helper function
        if details["Full Job Description"] != '-':
            details["Phone Number"], details["Email"] = extract_contact_info(details["Full Job Description"])
        else:
            details["Phone Number"], details["Email"] = "-", "-"


        print(f"Python: Successfully extracted: {details['Job Title']} | {details['Company Name']} | {details['Location']}", file=sys.stderr)

    except Exception as e:
        print(f"Python: Error scraping details for {job_url}: {e}", file=sys.stderr)
        details["Job Title"] = f"Error scraping details" # Keep other fields as '-'

    return details

def save_to_csv(job_details, job_title, location):
    """Saves the job details to a CSV file."""
    if not job_details:
        print("Python: No job details to save to CSV.", file=sys.stderr)
        return None
    
    # Create a filename based on search parameters and timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"seek_{format_for_url(job_title)}_{format_for_url(location)}_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Get field names from the first job detail dictionary
            fieldnames = list(job_details[0].keys())
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in job_details:
                # Handle potential encoding issues
                sanitized_job = {}
                for key, value in job.items():
                    if isinstance(value, str):
                        # Replace problematic characters or encoding issues
                        sanitized_job[key] = value.replace('\x00', '').encode('utf-8', 'ignore').decode('utf-8')
                    else:
                        sanitized_job[key] = value
                
                writer.writerow(sanitized_job)
        
        print(f"Python: Successfully saved {len(job_details)} jobs to {filename}", file=sys.stderr)
        return filename
    except Exception as e:
        print(f"Python: Error saving to CSV: {e}", file=sys.stderr)
        return None

def scrape_seek_jobs(jobTitle, location, numJobs):
    """Main function to orchestrate scraping using Selenium."""
    print("Python: Starting scrape_seek_jobs...", file=sys.stderr)
    driver = None
    all_job_details = []
    csv_filename = None
    
    try:
        limit = int(numJobs)
    except ValueError:
        print(f"Python: Invalid numJobs '{numJobs}', defaulting to 5.", file=sys.stderr)
        limit = 5

    try:
        driver = get_driver()
        job_links = get_job_links_from_search(driver, jobTitle, location, limit)

        if not job_links:
            print("Python: No job links found on search results page.", file=sys.stderr)
            return json.dumps({"jobs": [], "csv_file": None})

        print(f"Python: Found {len(job_links)} links. Scraping details for each...", file=sys.stderr)
        for i, link in enumerate(job_links):
            print(f"--- Scraping Job {i+1}/{len(job_links)} ---", file=sys.stderr)
            details = scrape_job_details(driver, link)
            all_job_details.append(details)
            # Add a delay between requests
            sleep_time = 2 + (i % 2) # Variable sleep 2-3 seconds
            print(f"Python: Sleeping for {sleep_time} seconds...", file=sys.stderr)
            time.sleep(sleep_time)
        
        # Save to CSV if we have job details
        if all_job_details:
            csv_filename = save_to_csv(all_job_details, jobTitle, location)

    except Exception as e:
        print(f"Python: General error in scrape_seek_jobs: {e}", file=sys.stderr)
        # Still try to save partial results to CSV
        if all_job_details:
            csv_filename = save_to_csv(all_job_details, jobTitle, location)
        return json.dumps({
            "error": f"An error occurred during scraping process: {e}",
            "partial_results": all_job_details,
            "csv_file": csv_filename
        })
    finally:
        if driver:
            driver.quit()
            print("Python: WebDriver closed.", file=sys.stderr)

    print(f"Python: Finished scraping. Returning {len(all_job_details)} detailed job results.", file=sys.stderr)
    if csv_filename:
        print(f"Python: Data also saved to CSV file: {csv_filename}", file=sys.stderr)
    
    return json.dumps({
        "jobs": all_job_details,
        "csv_file": csv_filename
    })
    return json.dumps(all_job_details)


if __name__ == "__main__":
    # Restored main block to be called by server.js
    if len(sys.argv) != 4:
        print(json.dumps({"error": "Usage: python scrape_omayzi.py <jobTitle> <location> <numJobs>"}))
        sys.exit(1)

    job_title_arg = sys.argv[1]
    location_arg = sys.argv[2]
    num_jobs_arg = sys.argv[3]

    # Call the main orchestrating function
    result_json = scrape_seek_jobs(job_title_arg, location_arg, num_jobs_arg)
    print(result_json) # Print the final JSON result to stdout
    
    # Note: The CSV file is already saved by the scrape_seek_jobs function
