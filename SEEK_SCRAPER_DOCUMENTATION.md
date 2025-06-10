# Seek Job Scraper Project Documentation

## Project Overview
This project is a web application that scrapes job listings from Seek.com.au based on user-provided criteria. It provides a user-friendly interface to search for jobs, displays the results in a table format, and allows downloading the data as a CSV file.

## How It Works
1. The user enters their search criteria (job title, location, number of jobs) in the web interface
2. The request is sent to a Node.js server
3. The server calls a Python script that uses Selenium to scrape Seek.com.au
4. The scraped data is returned to the frontend and displayed in a table
5. A CSV file is generated and made available for download

## Project Structure
The project consists of three main files:
1. `index.html` - Frontend interface
2. `server.js` - Node.js backend server
3. `scrape_omayzi.py` - Python scraping script

## Setup Requirements
- Node.js and npm
- Python 3.x
- Google Chrome browser
- Required Python packages: selenium, webdriver-manager, beautifulsoup4
- Required Node.js package: express

## Installation
1. Install Node.js dependencies:
```bash
npm install express
```

2. Install Python dependencies:
```bash
pip install selenium webdriver-manager beautifulsoup4
```

## Running the Application
1. Start the server:
```bash
node server.js
```

2. Open your browser and navigate to:
```
http://localhost:3000
```

## Code Files

### 1. Frontend (index.html)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scrape Job Here</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        #status { margin-top: 15px; font-style: italic; color: #555; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: fixed; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; word-wrap: break-word; }
        th { background-color: #f2f2f2; }
        td pre { white-space: pre-wrap; font-family: inherit; margin: 0;}
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Scrape Job Here</h1>
    <form id="scrapeForm">
        <label for="jobTitle">Job Title:</label><br>
        <input type="text" id="jobTitle" name="jobTitle" required><br><br>

        <label for="location">Location:</label><br>
        <input type="text" id="location" name="location" required><br><br>

        <label for="numJobs">Number of Jobs to Scrape:</label><br>
        <input type="number" id="numJobs" name="numJobs" value="2" required min="1"><br><br>

        <input type="submit" value="Scrape Jobs">
    </form>

    <div id="status"></div>
    <div id="csv-link"></div>
    <div id="results"></div>

    <script>
        const scrapeForm = document.getElementById('scrapeForm');
        const statusDiv = document.getElementById('status');
        const csvLinkDiv = document.getElementById('csv-link');
        const resultsDiv = document.getElementById('results');

        scrapeForm.onsubmit = async function(event) {
            event.preventDefault();
            resultsDiv.innerHTML = '';
            csvLinkDiv.innerHTML = '';
            statusDiv.textContent = 'Sending request...';

            const jobTitle = document.getElementById('jobTitle').value;
            const location = document.getElementById('location').value;
            const numJobs = document.getElementById('numJobs').value;

            if (!jobTitle || !location || !numJobs) {
                statusDiv.textContent = 'Please fill in all fields.';
                return;
            }
            if (parseInt(numJobs) < 1) {
                statusDiv.textContent = 'Number of jobs must be at least 1.';
                return;
            }

            statusDiv.textContent = `Request sent for "${jobTitle}" in "${location}" (${numJobs} jobs). Waiting for server...`;

            try {
                const url = `/scrape?jobTitle=${encodeURIComponent(jobTitle)}&location=${encodeURIComponent(location)}&numJobs=${encodeURIComponent(numJobs)}`;
                statusDiv.textContent = 'Server received request. Starting scraping process... (This may take several minutes depending on the number of jobs)';

                const response = await fetch(url);

                statusDiv.textContent = 'Processing response from server...';

                if (!response.ok) {
                    let errorMsg = `HTTP error! Status: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        errorMsg += ` - ${errorData.error || 'Unknown server error'}`;
                        if(errorData.details) { errorMsg += ` Details: ${errorData.details}`; }
                    } catch (e) { errorMsg += ` - ${await response.text()}`; }
                    throw new Error(errorMsg);
                }

                const data = await response.json();

                if (data.error) {
                    throw new Error(`Scraping Error: ${data.error}`);
                }

                const jobsData = data.jobs || data;
                const csvFile = data.csv_file;

                if (csvFile) {
                    csvLinkDiv.innerHTML = `
                        <div style="margin: 15px 0; padding: 10px; background-color: #e8f5e9; border-radius: 5px;">
                            <strong>CSV Export:</strong>
                            <a href="${csvFile}" download>Download ${csvFile}</a>
                        </div>
                    `;
                }

                if (Array.isArray(jobsData) && jobsData.length > 0) {
                    statusDiv.textContent = `Scraping completed. Found details for ${jobsData.length} jobs. Displaying results...`;
                    const table = createTable(jobsData);
                    resultsDiv.innerHTML = table;
                } else if (Array.isArray(jobsData) && jobsData.length === 0) {
                    statusDiv.textContent = 'Scraping completed, but no jobs found or details could not be extracted.';
                    resultsDiv.innerHTML = '<p>No job details found.</p>';
                } else {
                    console.error("Received unexpected data format:", data);
                    throw new Error('Received unexpected data format from server.');
                }

            } catch (error) {
                console.error('Error during fetch or processing:', error);
                statusDiv.innerHTML = `<span class="error">Error: ${error.message}</span>`;
                resultsDiv.innerHTML = '';
            }
        };

        function createTable(jobsData) {
            if (!Array.isArray(jobsData)) return '<p>Error: Invalid data for table.</p>';

            const table = document.createElement('table');
            const headerRow = table.insertRow();
            const headers = [
                "Job Title", "Company Name", "Location", "Salary/Pay Range", "Job Type", "Date Posted",
                "Key Responsibilities", "Required Skills/Qualifications",
                "Phone Number", "Email", "Full Job Description", "Job URL"
            ];
            headers.forEach(headerText => {
                const header = document.createElement('th');
                header.textContent = headerText;
                headerRow.appendChild(header);
            });

            jobsData.forEach(job => {
                const tableRow = table.insertRow();
                tableRow.insertCell().textContent = job["Job Title"] || '-';
                tableRow.insertCell().textContent = job["Company Name"] || '-';
                tableRow.insertCell().textContent = job["Location"] || '-';
                tableRow.insertCell().textContent = job["Salary/Pay Range"] || '-';
                tableRow.insertCell().textContent = job["Job Type"] || '-';
                tableRow.insertCell().textContent = job["Date Posted"] || '-';
                tableRow.insertCell().textContent = job["Key Responsibilities"] || '-';
                tableRow.insertCell().textContent = job["Required Skills/Qualifications"] || '-';
                tableRow.insertCell().textContent = job["Phone Number"] || '-';
                tableRow.insertCell().textContent = job["Email"] || '-';
                const descCell = tableRow.insertCell();
                const pre = document.createElement('pre');
                pre.textContent = job["Full Job Description"] || '-';
                descCell.appendChild(pre);
                const urlCell = tableRow.insertCell();
                if (job["Job URL"] && job["Job URL"] !== '-') {
                    const linkElement = document.createElement('a');
                    linkElement.href = job["Job URL"];
                    linkElement.textContent = 'View Original';
                    linkElement.target = '_blank';
                    urlCell.appendChild(linkElement);
                } else {
                    urlCell.textContent = '-';
                }
            });

            return table.outerHTML;
        }
    </script>
</body>
</html>
```

### 2. Backend Server (server.js)
```javascript
const express = require('express');
const { exec } = require('child_process');
const app = express();
const port = 3000;
const path = require('path');

app.use(express.static(__dirname));
app.use(express.json());

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/scrape', async (req, res) => {
    const jobTitle = req.query.jobTitle;
    const location = req.query.location;
    const numJobs = req.query.numJobs;

    if (!jobTitle || !location || !numJobs) {
        console.error('Server: Missing parameters:', { jobTitle, location, numJobs });
        return res.status(400).json({ error: 'Missing job title, location, or number of jobs parameter' });
    }
    console.log(`Server: Received request - title: ${jobTitle}, location: ${location}, number: ${numJobs}`);

    try {
        const pythonExecutable = 'python';
        const scriptPath = path.join(__dirname, 'scrape_omayzi.py');
        const pythonCommand = `${pythonExecutable} "${scriptPath}" "${jobTitle}" "${location}" "${numJobs}"`;

        console.log(`Server: Executing Python command: ${pythonCommand}`);

        const { stdout, stderr } = await new Promise((resolve, reject) => {
            exec(pythonCommand, { maxBuffer: 1024 * 5000 }, (error, stdout, stderr) => {
                if (stderr) {
                    console.error(`Server: Python stderr:\n${stderr}`);
                }
                if (error) {
                    console.error(`Server: Error executing Python command: ${error.message}`);
                    return reject({ status: 500, message: `Error executing Python script: ${error.message}`, stderr: stderr });
                }
                try {
                    const result = JSON.parse(stdout);
                    if (result && result.error) {
                        console.error(`Server: Python script returned an error: ${result.error}`);
                        return reject({ status: 500, message: `Scraping/Parsing Error: ${result.error}` });
                    }
                } catch (parseError) {
                }
                resolve({ stdout, stderr });
            });
        });

        console.log(`Server: Python script stdout length: ${stdout.length}`);
        try {
            const jsonData = JSON.parse(stdout);
            console.log(`Server: Successfully parsed JSON response from Python.`);
            res.setHeader('Content-Type', 'application/json');
            res.status(200).json(jsonData);
        } catch (parseError) {
            console.error(`Server: Failed to parse JSON from Python stdout: ${parseError}`);
            console.error(`Server: Python stdout was:\n${stdout}`);
            res.status(500).json({ error: 'Failed to parse response from scraping script.' });
        }

    } catch (error) {
        console.error(`Server: Error in /scrape route: ${error.message || error}`);
        res.status(error.status || 500).json({
            error: `An error occurred: ${error.message || 'Unknown error'}`,
            details: error.stderr || 'No stderr details'
        });
    }
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
    console.log(`Serving static files from: ${__dirname}`);
});
```

### 3. Python Scraper (scrape_omayzi.py)
```python
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
import re

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
    phone_regex = r'(\(?\+?\d{1,3}\)?[\s.-]?\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4})'
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    phones = re.findall(phone_regex, text)
    emails = re.findall(email_regex, text)

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
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//article[@data-card-type='JobCard']"))
        )
        print("Python: Search results page loaded.", file=sys.stderr)
        time.sleep(2)
        html_content = driver.page_source
    except Exception as e:
        print(f"Python: Error loading search results page {search_url}: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    job_cards = soup.find_all('article', attrs={'data-card-type': 'JobCard'})
    print(f"Python: Found {len(job_cards)} potential job cards on search page.", file=sys.stderr)

    for job_card in job_cards:
        if len(links) >= numJobs_limit:
            print(f"Python: Reached job link limit of {numJobs_limit}.", file=sys.stderr)
            break

        link_element = job_card.find('h3', {'data-automation': 'job-title'})
        if link_element:
             link_element = link_element.find('a')

        if not link_element:
             link_element = job_card.find('a', {'data-automation': 'jobTitle'})
        if not link_element:
             link_element = job_card.find('a', href=re.compile(r'/job/'))

        if link_element and link_element.has_attr('href'):
            href = link_element['href']
            if href.startswith('/job/'):
                full_url = base_url + href.split('?')[0]
                if full_url not in links:
                    links.append(full_url)
        else:
            print("Python: Found job card without a valid title link.", file=sys.stderr)

    print(f"Python: Extracted {len(links)} unique job links.", file=sys.stderr)
    return links

def scrape_job_details(driver, job_url):
    """Scrapes detailed information from a single job page."""
    print(f"Python: Scraping details from: {job_url}", file=sys.stderr)
    details = {
        "Job Title": "-", "Company Name": "-", "Location": "-", "Salary/Pay Range": "-",
        "Key Responsibilities": "-", "Required Skills/Qualifications": "-", "Date Posted": "-",
        "Job Type": "-", "Phone Number": "-", "Email": "-", "Full Job Description": "-",
        "Job URL": job_url
    }

    try:
        driver.get(job_url)
        WebDriverWait(driver, 15).until(
             EC.presence_of_element_located((By.XPATH, "//h1[@data-automation='job-detail-title'] | //div[@data-automation='jobAdDetails'] | //div[contains(@class,'job-description')]"))
        )
        print(f"Python: Job details page loaded: {job_url}", file=sys.stderr)
        time.sleep(2)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        title = soup.find('h1', {'data-automation': 'job-detail-title'})
        details["Job Title"] = title.text.strip() if title else '-'
        if details["Job Title"] == '-':
             title = soup.find('h1', class_=lambda x: x and 'JobTitle' in x)
             details["Job Title"] = title.text.strip() if title else '-'

        company = soup.find('span', {'data-automation': 'advertiser-name'})
        details["Company Name"] = company.text.strip() if company else '-'
        if details["Company Name"] == '-' :
             company_link = soup.find('a', {'data-automation': 'job-header-company-name'})
             details["Company Name"] = company_link.text.strip() if company_link else '-'
        if details["Company Name"] == '-':
             company = soup.find('span', class_=lambda x: x and 'AdvertiserName' in x)
             details["Company Name"] = company.text.strip() if company else '-'

        location_element = soup.find('span', {'data-automation': 'job-detail-location'})
        details["Location"] = location_element.text.strip() if location_element else '-'

        salary = soup.find('span', {'data-automation': 'job-detail-salary'})
        details["Salary/Pay Range"] = salary.text.strip() if salary else '-'

        job_type_element = soup.find('span', {'data-automation': 'job-detail-work-type'})
        details["Job Type"] = job_type_element.text.strip() if job_type_element else '-'

        date_posted_element = soup.find('span', {'data-automation': 'job-detail-date'})
        details["Date Posted"] = date_posted_element.text.strip() if date_posted_element else '-'

        description_div = soup.find('div', {'data-automation': 'jobAdDetails'})
        details["Full Job Description"] = description_div.get_text(separator='\n', strip=True) if description_div else '-'
        if details["Full Job Description"] == '-':
             description_div = soup.find('div', class_=lambda x: x and 'job-description' in x)
             details["Full Job Description"] = description_div.get_text(separator='\n', strip=True) if description_div else '-'

        details["Key Responsibilities"] = "See Full Description"
        details["Required Skills/Qualifications"] = "See Full Description"

        if details["Full Job Description"] != '-':
            details["Phone Number"], details["Email"] = extract_contact_info(details["Full Job Description"])
        else:
            details["Phone Number"], details["Email"] = "-", "-"

        print(f"Python: Successfully extracted: {details['Job Title']} | {details['Company Name']} | {details['Location']}", file=sys.stderr)

    except Exception as e:
        print(f"Python: Error scraping details for {job_url}: {e}", file=sys.stderr)
        details["Job Title"] = f"Error scraping details"

    return details

def save_to_csv(job_details, job_title, location):
    """Saves the job details to a CSV file."""
    if not job_details:
        print("Python: No job details to save to CSV.", file=sys.stderr)
        return None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"seek_{format_for_url(job_title)}_{format_for_url(location)}_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(job_details[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in job_details:
                sanitized_job = {}
                for key, value in job.items():
                    if isinstance(value, str):
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
        
        for job_url in job_links:
            job_details = scrape_job_details(driver, job_url)
            all_job_details.append(job_details)
            time.sleep(2)  # Be nice to the server

        if all_job_details:
            csv_filename = save_to_csv(all_job_details, jobTitle, location)
            result = {
                "jobs": all_job_details,
                "csv_file": csv_filename
            }
        else:
            result = {
                "jobs": [],
                "error": "No jobs found or could not extract details"
            }

    except Exception as e:
        print(f"Python: Error in scrape_seek_jobs: {e}", file=sys.stderr)
        result = {
            "error": f"Error during scraping: {str(e)}"
        }
    finally:
        if driver:
            driver.quit()

    print(json.dumps(result))
    return result

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(json.dumps({"error": "Invalid number of arguments. Usage: python scrape_omayzi.py 'job title' 'location' 'number of jobs'"}))
        sys.exit(1)

    jobTitle = sys.argv[1]
    location = sys.argv[2]
    numJobs = sys.argv[3]

    scrape_seek_jobs(jobTitle, location, numJobs)
```

## Integration Guide
To integrate this scraper into another project:

1. **Frontend Integration:**
   - Copy the HTML/CSS/JavaScript code from `index.html`
   - Modify the form and table structure as needed
   - Update the API endpoint URL if necessary

2. **Backend Integration:**
   - Copy `server.js` and `scrape_omayzi.py`
   - Install required dependencies
   - Modify the server port if needed
   - Update the Python script path in `server.js`

3. **Python Scraper Integration:**
   - The Python script can be used independently
   - Import the `scrape_seek_jobs` function
   - Call it with job title, location, and number of jobs
   - Handle the returned JSON data as needed

## Important Notes
1. The scraper uses Selenium with a headless Chrome browser
2. It includes anti-detection measures
3. The script respects rate limits with delays between requests
4. Error handling is implemented at all levels
5. The scraper extracts comprehensive job details including contact information

## Limitations
1. Dependent on Seek.com.au's HTML structure
2. May need updates if the website changes
3. Rate limiting may affect scraping speed
4. Some job details might not be available for all listings

## Future Improvements
1. Add proxy support for better rate limiting
2. Implement retry mechanisms for failed requests
3. Add more sophisticated contact information extraction
4. Implement parallel scraping for faster results
5. Add support for more job search parameters 