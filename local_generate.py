import os
import argparse
from dotenv import load_dotenv
from zlm import AutoApplyModel
import json
from read_csv_job import get_pending_jobs, update_csv_with_filenames, get_job_by_row_index

# Load environment variables
load_dotenv()

def generate_resume_and_cover_letter(job_description: str, old_resume_path: str, output_dir: str = "generated"):
    """
    Generate a tailored resume and cover letter based on a job description and old resume.
    
    Args:
        job_description (str): The job description text
        old_resume_path (str): Path to the old resume file (PDF)
        output_dir (str): Directory to save generated files
    """
    # Initialize the model
    resume_llm = AutoApplyModel(
        api_key=os.getenv("OPENAI_API_KEY"),
        provider="GPT",
        model="gpt-3.5-turbo",
        downloads_dir=output_dir
    )

    try:
        # Extract user data from resume
        print("Extracting user data from resume...")
        user_data = resume_llm.user_data_extraction(old_resume_path)
        
        # Extract job details from description
        print("Extracting job details...")
        job_details, jd_path = resume_llm.job_details_extraction(job_site_content=job_description)
        
        # Generate new resume
        print("Generating tailored resume...")
        resume_path, resume_details = resume_llm.resume_builder(job_details, user_data)
        
        # Generate cover letter
        print("Generating cover letter...")
        cv_details, cv_path = resume_llm.cover_letter_generator(job_details, user_data)
        
        print("\nGeneration complete!")
        print(f"Resume saved to: {resume_path}")
        print(f"Cover letter saved to: {cv_path}")
        
        # Print estimated cost as per user's formula
        # Formula: cost = 1500 * 0.000005 + 500 * 0.00002 = $0.0175
        input_cost = 1500 * 0.000005
        output_cost = 500 * 0.00002
        total_cost = input_cost + output_cost
        print(f"Estimated cost for this generation: ${total_cost:.4f}")

        return resume_path, cv_path
        
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        return None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate resume and cover letter for jobs in a CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file containing job listings.")
    parser.add_argument("row_number", type=int, nargs='?', help="Optional: Specify a 1-based row number to process only that job.")
    args = parser.parse_args()

    csv_file_path = args.csv_file
    row_to_process = args.row_number
    old_resume_path = "Umair_resume.pdf"
    
    if row_to_process is not None:
        print(f"Processing job at row {row_to_process} from {csv_file_path}...")
        job_info = get_job_by_row_index(csv_file_path, row_to_process)
        
        if job_info:
            row_index, job_description = job_info
            resume_path, cv_path = generate_resume_and_cover_letter(
                job_description=job_description,
                old_resume_path=old_resume_path
            )
            
            if resume_path and cv_path:
                resume_filename = os.path.basename(resume_path)
                coverletter_filename = os.path.basename(cv_path)
                
                update_csv_with_filenames(
                    csv_file_path=csv_file_path,
                    row_index=row_index,
                    resume_filename=resume_filename,
                    coverletter_filename=coverletter_filename
                )
            else:
                print(f"Failed to generate documents for row {row_to_process}")
        else:
            print(f"Could not find job at row {row_to_process} or it has no job description.")

    else:
        pending_jobs = get_pending_jobs(csv_file_path)
        
        if not pending_jobs:
            print("No pending jobs found in the CSV file.")
            exit()
        
        print(f"\nProcessing {len(pending_jobs)} pending jobs...")
        
        for row_index, job_description in pending_jobs:
            print(f"\nProcessing job at row {row_index + 1}...")
            
            resume_path, cv_path = generate_resume_and_cover_letter(
                job_description=job_description,
                old_resume_path=old_resume_path
            )
            
            if resume_path and cv_path:
                resume_filename = os.path.basename(resume_path)
                coverletter_filename = os.path.basename(cv_path)
                
                update_csv_with_filenames(
                    csv_file_path=csv_file_path,
                    row_index=row_index,
                    resume_filename=resume_filename,
                    coverletter_filename=coverletter_filename
                )
            else:
                print(f"Failed to generate documents for row {row_index + 1}")
    
    print("\nProcessing complete!") 