#!/usr/bin/env python3
import os
import sys
import json
import pandas as pd
from slugify import slugify
from zlm import AutoApplyModel
from dotenv import load_dotenv
import numpy as np
import streamlit as st

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs("generated", exist_ok=True)
    os.makedirs("resources", exist_ok=True)

def load_user_data():
    """Load user data from JSON file."""
    user_data_path = "user_data.json"
    if not os.path.exists(user_data_path):
        print("[WARN] user_data.json not found. Using default data.")
        return {
            "name": "John Doe",
            "phone": "123-456-7890",
            "email": "john.doe@example.com",
            "media": {
                "github": "https://github.com/johndoe",
                "linkedin": "https://linkedin.com/in/johndoe"
            },
            "work_experience": [],
            "projects": [],
            "skill_section": [],
            "education": [],
            "certifications": [],
            "achievements": []
        }
    
    with open(user_data_path, 'r') as f:
        return json.load(f)

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
        model="gpt-3.5-turbo",  # Changed to a model that supports JSON output
        downloads_dir="generated"
    )
    
    # Process each job
    for idx, row in to_do.iterrows():
        print(f"\n[INFO] Processing job {idx+1}/{len(to_do)}: {row['title']} at {row['company']}")
        
        try:
            # Extract job details
            print("\nExtracting job details...")
            job_details = {
                "job_title": row['title'],
                "company_name": row['company'],
                "description": row['description'],
                "keywords": [],  # Will be extracted from description
                "job_purpose": "",
                "job_duties_and_responsibilities": [],
                "required_qualifications": [],
                "preferred_qualifications": [],
                "company_details": ""
            }
            
            # Generate resume
            print(f"[INFO] Generating resume for {row['company']}")
            resume_path, resume_details = resume_llm.resume_builder(job_details, user_data)
            
            if resume_path and os.path.exists(resume_path):
                df.at[idx, 'resume_filename'] = os.path.basename(resume_path)
                print(f"[SUCCESS] Generated resume: {resume_path}")
            else:
                print(f"[ERROR] Failed to generate resume for {row['company']}")
            
            # Generate cover letter
            print(f"[INFO] Generating cover letter for {row['company']}")
            cv_details, cv_path = resume_llm.cover_letter_generator(job_details, user_data)
            
            if cv_path and os.path.exists(cv_path):
                df.at[idx, 'coverletter_filename'] = os.path.basename(cv_path)
                print(f"[SUCCESS] Generated cover letter: {cv_path}")
            else:
                print(f"[ERROR] Failed to generate cover letter for {row['company']}")
            
            print(f"[SUCCESS] Generated documents for {row['company']}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process job {row['title']} at {row['company']}: {str(e)}")
            continue
    
    # Save updated CSV
    df.to_csv(csv_path, index=False)
    print(f"\n[SUCCESS] Updated {csv_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chunk2.py <csv_file>")
        sys.exit(1)
    
    main(sys.argv[1]) 