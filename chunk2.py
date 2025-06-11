#!/usr/bin/env python3
import os
import sys
import json
import pandas as pd
from slugify import slugify
from zlm import AutoApplyModel
from dotenv import load_dotenv
import numpy as np

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs("generated", exist_ok=True)

def load_user_data():
    """Load user data from a JSON file or return default data."""
    try:
        with open("user_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[WARN] user_data.json not found. Using default data.")
        return {
            "name": "Your Name",
            "email": "your.email@example.com",
            "phone": "Your Phone",
            "location": "Your Location",
            "summary": "Your professional summary",
            "experience": [
                {
                    "title": "Job Title",
                    "company": "Company Name",
                    "location": "Location",
                    "start_date": "Start Date",
                    "end_date": "End Date",
                    "description": "Job description"
                }
            ],
            "education": [
                {
                    "degree": "Degree Name",
                    "school": "School Name",
                    "location": "Location",
                    "graduation_date": "Graduation Date"
                }
            ],
            "skills": ["Skill 1", "Skill 2", "Skill 3"]
        }

def main(csv_path):
    """Main function to process jobs and generate resumes/cover letters."""
    # Load environment variables
    load_dotenv()
    
    # Ensure required directories exist
    ensure_directories()
    
    # Load user data
    user_data = load_user_data()
    
    # Read CSV
    print(f"[INFO] Reading {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure columns exist and convert to string type
    for col in ("resume_filename", "coverletter_filename"):
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("").astype(str)
    
    # Filter only jobs that still need docs
    to_do = df[(df["resume_filename"].str.strip() == "") | (df["coverletter_filename"].str.strip() == "")]
    
    if to_do.empty:
        print("[INFO] All jobs already have résumé & cover letter—nothing to do.")
        return
    
    print(f"[INFO] Found {len(to_do)} jobs to process")
    
    # Initialize ResumeFlow model
    resume_llm = AutoApplyModel(
        api_key=os.getenv("OPENAI_API_KEY"),
        provider="GPT",
        model="gpt-4",
        downloads_dir="generated"
    )
    
    # Set the resume file path
    resume_path = os.path.join("resources", "resume.pdf")
    if not os.path.exists(resume_path):
        print(f"[ERROR] Resume file not found at {resume_path}")
        return
    
    # Process each job
    for idx, row in to_do.iterrows():
        try:
            print(f"\n[INFO] Processing job {idx + 1}/{len(to_do)}: {row['title']} at {row['company']}")
            
            # Extract job details
            job_details, jd_path = resume_llm.job_details_extraction(url=row["url"])
            
            # Generate safe filenames
            safe_company = slugify(row["company"])
            safe_title = slugify(row["title"])
            
            # Generate resume
            try:
                print(f"[INFO] Generating resume for {row['company']}")
                resume_path, resume_details = resume_llm.resume_builder(job_details, user_data)
                if resume_path:
                    df.loc[idx, 'resume_filename'] = os.path.basename(resume_path)
            except Exception as e:
                print(f"[ERROR] Failed to generate resume: {e}")
            
            # Generate cover letter
            try:
                print(f"[INFO] Generating cover letter for {row['company']}")
                cv_text, cv_path = resume_llm.cover_letter_generator(job_details, user_data)
                if cv_path:
                    df.loc[idx, 'coverletter_filename'] = os.path.basename(cv_path)
            except Exception as e:
                print(f"[ERROR] Failed to generate cover letter: {e}")
            
            print(f"[SUCCESS] Generated documents for {row['company']}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process job at {row['company']}: {str(e)}")
            continue
    
    # Write updated CSV
    df.to_csv(csv_path, index=False)
    print(f"\n[SUCCESS] Updated {csv_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chunk2.py <jobs_csv_file>")
        sys.exit(1)
    main(sys.argv[1]) 