#!/usr/bin/env python3
import argparse
import json
import sys
from scrape_omayzi import scrape_seek_jobs  # from SEEK_SCRAPER_DOCUMENTATION.md

def main():
    parser = argparse.ArgumentParser(
        description="Chunk 1: scrape SEEK and dump jobs to JSON"
    )
    parser.add_argument("title", help="Job title to search for")
    parser.add_argument("location", help="Location to search for")
    parser.add_argument(
        "limit", type=int, help="Maximum number of jobs to scrape"
    )
    parser.add_argument(
        "-o", "--output",
        default="jobs.json",
        help="Path to output JSON file (default: jobs.json)"
    )
    args = parser.parse_args()

    # Run the existing scraper
    result = scrape_seek_jobs(args.title, args.location, args.limit)
    # The function returns a dict: { "jobs": [...], "csv_file": "…" } or { "error": … }
    if "error" in result:
        print(f"[ERROR] {result['error']}", file=sys.stderr)
        sys.exit(1)

    jobs = result.get("jobs", [])
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)

    print(
        f"[OK] Scraped {len(jobs)} jobs for "
        f"'{args.title}' in '{args.location}'. → {args.output}"
    )

if __name__ == "__main__":
    main() 