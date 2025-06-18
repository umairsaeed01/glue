import os
from dotenv import load_dotenv
from zlm import AutoApplyModel
import json
from read_csv_job import get_first_job_description, update_csv_with_filenames, get_pending_jobs

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
        
        return resume_path, cv_path
        
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        return None, None

if __name__ == "__main__":
    # Example usage
    csv_file_path = "software_engineer.csv"
    old_resume_path = "resume.pdf"
    
    # Get all pending jobs from CSV
    pending_jobs = get_pending_jobs(csv_file_path)
    
    if not pending_jobs:
        print("No pending jobs found in the CSV file.")
        exit()
    
    print(f"\nProcessing {len(pending_jobs)} pending jobs...")
    
    # Process each pending job
    for row_index, job_description in pending_jobs:
        print(f"\nProcessing job at row {row_index + 1}...")
        
        # Generate resume and cover letter
        resume_path, cv_path = generate_resume_and_cover_letter(
            job_description=job_description,
            old_resume_path=old_resume_path
        )
        
        # If generation was successful, update the CSV with the filenames
        if resume_path and cv_path:
            # Extract just the filenames from the paths
            resume_filename = os.path.basename(resume_path)
            coverletter_filename = os.path.basename(cv_path)
            
            # Update the CSV with the generated filenames
            update_csv_with_filenames(
                csv_file_path=csv_file_path,
                row_index=row_index,
                resume_filename=resume_filename,
                coverletter_filename=coverletter_filename
            )
        else:
            print(f"Failed to generate documents for row {row_index + 1}")
    
    print("\nAll pending jobs have been processed!") 