# Seek Job Scraper Web App

## Description

This is a simple web application that scrapes job listings from Seek.com.au based on user-provided criteria (job title, location, number of jobs). It displays the scraped job details in a table on the webpage and provides a link to download the data as a CSV file.

## Files Involved

*   **`index.html`**: The main frontend file containing the HTML structure, CSS styling, and JavaScript code. It handles user input, sends requests to the backend, displays the status, shows the results table, and provides the CSV download link.
*   **`server.js`**: A backend server built with Node.js and Express. It serves the `index.html` file, handles GET requests to the `/scrape` endpoint, executes the Python scraping script (`scrape_omayzi.py`), receives the results, serves the generated CSV files, and sends the job data back to the frontend as JSON.
*   **`scrape_omayzi.py`**: The core Python script that performs the web scraping. It uses Selenium to control a headless Chrome browser and BeautifulSoup to parse HTML content from Seek.com.au. It extracts job details, saves them to a CSV file, and prints the results (job data and CSV filename) as a JSON string to standard output.

## Requirements

*   **Node.js and npm:** Required to run the `server.js` backend. Download from [https://nodejs.org/](https://nodejs.org/).
*   **Python 3.x:** Required to run the `scrape_omayzi.py` script. Download from [https://www.python.org/](https://www.python.org/).
*   **pip:** Python's package installer (usually comes with Python).
*   **Google Chrome:** The script uses ChromeDriver, which requires Google Chrome to be installed.

## Setup Instructions

1.  **Clone or Download:** Obtain the project files (`index.html`, `server.js`, `scrape_omayzi.py`) and place them in a single directory on your local machine.
2.  **Install Node.js Dependencies:**
    *   Open your terminal or command prompt.
    *   Navigate (`cd`) to the project directory.
    *   Run the command: `npm install express`
3.  **Install Python Dependencies:**
    *   In the same terminal, run the command: `pip install selenium webdriver-manager beautifulsoup4`
    *   *(Note: `webdriver-manager` will automatically download and manage the appropriate ChromeDriver version for your installed Chrome browser the first time the Python script runs).*

## Running the Application

1.  **Start the Node.js Server:**
    *   Make sure you are in the project directory in your terminal.
    *   Run the command: `node server.js`
    *   You should see output indicating the server is listening on `http://localhost:3000`.
2.  **Access the Web App:**
    *   Open your web browser (like Chrome, Firefox, etc.).
    *   Navigate to the address: `http://localhost:3000`
3.  **Use the Scraper:**
    *   Fill in the "Job Title", "Location" (e.g., "Melbourne VIC"), and "Number of Jobs to Scrape" fields.
    *   Click the "Scrape Jobs" button.
4.  **View Results:**
    *   Wait for the scraping process to complete. Status updates will appear on the page. This can take several minutes depending on the number of jobs requested.
    *   Once finished, the scraped job details will be displayed in a table.
    *   A link to download the generated CSV file (e.g., `seek_software-engineer_melbourne-vic_20250409_131018.csv`) will appear above the table.

## Important Notes

*   **Scraping Time:** Web scraping individual pages is time-consuming. Be patient, especially when requesting a larger number of jobs.
*   **Website Changes:** Web scraping scripts are sensitive to changes in the target website's structure. If Seek.com.au updates its layout, the selectors in `scrape_omayzi.py` (e.g., `data-automation` attributes) may need to be updated for the script to continue working correctly.
*   **Terms of Service:** Always be mindful of the website's terms of service (robots.txt, usage policies) regarding automated scraping. Use responsibly.

## AI Prompt to Recreate This Project

If you want to recreate this project using an AI assistant, you can use the following prompt:

```
Objective: Create a web application that allows users to scrape job listings from Seek.com.au, view the results, and download them as a CSV file.

Core Components:

1.  **Frontend (`index.html`):**
    *   Create an HTML page with CSS for basic styling.
    *   Include input fields for:
        *   Job Title (text input)
        *   Location (text input, e.g., "Sydney NSW")
        *   Number of Jobs (number input, default 5, min 1)
    *   Add a "Scrape Jobs" submit button.
    *   Include a `div` element (`id="status"`) to display status messages (e.g., "Requesting...", "Scraping job 1/5...", "Error...", "Completed").
    *   Include a `div` element (`id="csv-link"`) to display a download link for the generated CSV file.
    *   Include a `div` element (`id="results"`) where the scraped job data will be displayed as an HTML table.
    *   Write JavaScript code to:
        *   Handle the form submission.
        *   Prevent default form submission.
        *   Clear previous results and status messages.
        *   Get values from input fields.
        *   Perform basic validation (fields not empty, number >= 1).
        *   Construct the request URL for the backend `/scrape` endpoint, including query parameters (`jobTitle`, `location`, `numJobs`).
        *   Use the `fetch` API to send a GET request to the backend `/scrape` endpoint.
        *   Update the status `div` during the process.
        *   Handle the JSON response from the server. The expected response format is an object: `{"jobs": [array_of_job_objects], "csv_file": "filename.csv"}`. Also handle potential error responses.
        *   If a `csv_file` is present in the response, create and display a download link (`<a>` tag with `download` attribute) in the `csv-link` div.
        *   If the `jobs` array is present and not empty, call a function `createTable(jobsData)` to generate the HTML table and display it in the `results` div.
        *   If the `jobs` array is empty, display a "No jobs found" message.
        *   Implement the `createTable(jobsData)` function to dynamically generate an HTML table from the array of job objects. The table headers should be: "Job Title", "Company Name", "Location", "Salary/Pay Range", "Job Type", "Date Posted", "Key Responsibilities", "Required Skills/Qualifications", "Phone Number", "Email", "Full Job Description", "Job URL". Make the "Job URL" a clickable link opening in a new tab. Use `<pre>` tags for the "Full Job Description" cell to preserve formatting. Handle missing data gracefully (e.g., display '-').

2.  **Backend (`server.js`):**
    *   Use Node.js and the Express framework (`npm install express`).
    *   Serve static files from the project directory (specifically `index.html` and the generated CSV files).
    *   Set up the server to listen on port 3000.
    *   Create a GET endpoint `/scrape`.
    *   In the `/scrape` endpoint:
        *   Retrieve `jobTitle`, `location`, and `numJobs` from the request query parameters (`req.query`). Validate their presence.
        *   Construct the command to execute the Python scraper script (`scrape_omayzi.py`). Use `child_process.exec`. The command should be like: `python scrape_omayzi.py "Job Title" "Location" "NumJobs"`. Ensure arguments are properly quoted/escaped.
        *   Execute the Python command. Handle potential errors during execution (e.g., Python not found, script errors). Log `stderr` from the Python script for debugging.
        *   Capture the `stdout` from the Python script.
        *   Parse the `stdout` as JSON. Handle JSON parsing errors.
        *   Send the parsed JSON object back to the frontend with a 200 status code.
        *   If any errors occur (script execution, JSON parsing), send an appropriate error status code (e.g., 500) and a JSON error message back to the frontend.

3.  **Python Scraper (`scrape_omayzi.py`):**
    *   Use Python 3.
    *   Required libraries: `selenium`, `webdriver-manager`, `beautifulsoup4`, `json`, `csv`, `sys`, `re`, `time`, `datetime`, `os`. Ensure these are installed (`pip install ...`).
    *   Read `jobTitle`, `location`, `numJobs` from command-line arguments (`sys.argv`).
    *   Implement helper functions:
        *   `format_for_url(text)`: Converts text to lowercase and replaces spaces with hyphens for use in Seek URLs.
        *   `get_driver()`: Initializes and returns a headless Selenium Chrome WebDriver using `webdriver-manager` to handle the ChromeDriver automatically. Include user-agent spoofing and options to bypass detection (`--headless`, `--no-sandbox`, `--disable-dev-shm-usage`, disable automation flags, navigator.webdriver=undefined).
        *   `extract_contact_info(text)`: Uses regular expressions (`re`) to find potential phone numbers and email addresses within a block of text. Return found contacts or '-'.
        *   `get_job_links_from_search(driver, jobTitle, location, numJobs_limit)`: Navigates to the Seek search results page, waits for job cards (`article[data-card-type='JobCard']`) to load, parses the HTML with BeautifulSoup, extracts unique job page URLs (up to `numJobs_limit`), and returns them as a list. Handle potential errors during page load or link extraction.
        *   `scrape_job_details(driver, job_url)`: Navigates to an individual job URL, waits for content to load, parses the HTML with BeautifulSoup, and extracts the following details into a dictionary: "Job Title", "Company Name", "Location", "Salary/Pay Range", "Job Type", "Date Posted", "Full Job Description", "Job URL". Use specific `data-automation` attributes (e.g., `job-detail-title`, `advertiser-name`, `jobAdDetails`) as primary selectors, but include fallback selectors (e.g., based on class names containing keywords like 'JobTitle', 'AdvertiserName', 'job-description') if the primary ones fail. For "Key Responsibilities" and "Required Skills/Qualifications", use placeholder text like "See Full Description". Call `extract_contact_info` on the full description to get "Phone Number" and "Email". Return the dictionary. Handle errors during scraping of a single page.
        *   `save_to_csv(job_details, job_title, location)`: Takes the list of scraped job dictionaries. If the list is not empty, creates a unique filename (e.g., `seek_jobtitle_location_timestamp.csv`), writes the data (including headers) to the CSV file using the `csv` module (handle potential encoding issues), prints a success message to stderr, and returns the filename. Returns `None` if there's an error or no data.
    *   Implement the main execution logic (`if __name__ == "__main__":`):
        *   Get command-line arguments.
        *   Initialize the WebDriver using `get_driver()`.
        *   Call `get_job_links_from_search` to get the list of job URLs.
        *   Iterate through the job links:
            *   Call `scrape_job_details` for each link.
            *   Append the resulting dictionary to a list (`all_job_details`).
            *   Include a short, variable delay (`time.sleep`) between scraping each job page (e.g., 2-3 seconds).
        *   After the loop (or if an error occurs), ensure the WebDriver is closed (`driver.quit()`) in a `finally` block.
        *   Call `save_to_csv` with the `all_job_details` list.
        *   Create the final result dictionary: `{"jobs": all_job_details, "csv_file": csv_filename}`.
        *   Print this final dictionary to standard output as a JSON string (`json.dumps`).
    *   Include `try...except` blocks for error handling throughout the process. Print informative error messages to `stderr` (`sys.stderr`).

4.  **Setup and Running Instructions (for the final user):**
    *   Include comments in the code or a separate README explaining how to install dependencies (`npm install express`, `pip install selenium webdriver-manager beautifulsoup4`) and how to run the application (`node server.js`, then access `http://localhost:3000`).

Code Style: Use clear variable names, add comments for complex logic, and ensure robust error handling with informative feedback to the user (via status messages) and the console/stderr.
