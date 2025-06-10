#!/usr/bin/env python3
import sys
from seek_scraper import scrape_seek_jobs
import json
from datetime import datetime


def save_jobs_no_dupes(jobs: list, title: str) -> str:
    """
    Save jobs to a JSON file.
    
    Args:
        jobs: List of job dictionaries with keys: job_id, title, company, location, url
        title: Job title used in the search
        
    Returns:
        str: Path to the saved JSON file
    """
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"seek_{title.replace(' ', '-')}_{timestamp}.json"
    
    # Save to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    
    return filename


def main(title: str, location: str, limit: int):
    """
    Main function to scrape jobs and save them.
    
    Args:
        title: Job title to search for
        location: Location to search in
        limit: Maximum number of jobs to scrape
    """
    try:
        result = scrape_seek_jobs(title, location, limit)
    except Exception as e:
        print(f"[ERROR] Unexpected exception: {e}", file=sys.stderr)
        sys.exit(1)

    if 'error' in result:
        print(f"[ERROR] {result['error']}", file=sys.stderr)
        sys.exit(1)

    jobs = result.get('jobs', [])
    output_file = save_jobs_no_dupes(jobs, title)
    
    print(f"[OK] Scraped {len(jobs)} jobs for '{title}' in '{location}'.")
    if result.get('csv_file'):
        print(f"[INFO] Also saved to CSV: {result['csv_file']}")
    print(f"[INFO] JSON output: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python glue.py <title> <location> <limit>", file=sys.stderr)
        sys.exit(1)
    
    _, title, location, limit = sys.argv
    main(title, location, int(limit)) 