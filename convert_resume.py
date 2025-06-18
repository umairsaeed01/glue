import os
from dotenv import load_dotenv
from zlm import AutoApplyModel
import json

# Load environment variables
load_dotenv()

def convert_resume_to_json(pdf_path: str, output_path: str = "resume.json"):
    """
    Convert a PDF resume to JSON format and add GitHub and LinkedIn links.
    
    Args:
        pdf_path (str): Path to the PDF resume file
        output_path (str): Path to save the JSON file
    """
    # Initialize the model
    resume_llm = AutoApplyModel(
        api_key=os.getenv("OPENAI_API_KEY"),
        provider="GPT",
        model="gpt-3.5-turbo"
    )

    try:
        # Convert PDF to JSON
        print("Converting PDF to JSON...")
        resume_json = resume_llm.resume_to_json(pdf_path)
        
        # Add GitHub and LinkedIn links
        print("Adding GitHub and LinkedIn links...")
        resume_json["media"] = {
            "github": "https://github.com/umairsaeed01",
            "linkedin": "https://www.linkedin.com/in/umirsaed"
        }
        
        # Save to JSON file
        print(f"Saving to {output_path}...")
        with open(output_path, "w") as f:
            json.dump(resume_json, f, indent=2)
            
        print("Conversion complete!")
        return resume_json
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return None

if __name__ == "__main__":
    # Path to your PDF resume
    pdf_path = "/Users/umairsaeed/Documents/ai/glue/resources/resume.pdf"
    
    # Convert to JSON
    resume_json = convert_resume_to_json(pdf_path)
    
    if resume_json:
        print("\nResume JSON structure:")
        print(json.dumps(resume_json, indent=2)) 