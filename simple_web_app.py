import os
import json
from dotenv import load_dotenv
import streamlit as st
from zlm import AutoApplyModel

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Resume Generator",
    page_icon="📑",
    layout="wide"
)

# Header
st.header("Resume and Cover Letter Generator")

# Input sections
col1, col2 = st.columns(2)

with col1:
    # Job Description Input
    job_description = st.text_area(
        "Paste Job Description",
        height=300,
        placeholder="Paste the job description here..."
    )

with col2:
    # Resume Upload
    uploaded_file = st.file_uploader(
        "Upload Your Resume (PDF or JSON)",
        type=["pdf", "json"]
    )

# Model Selection
col3, col4 = st.columns(2)
with col3:
    provider = st.selectbox(
        "Select Provider",
        ["GPT", "Gemini", "Ollama"]
    )
with col4:
    model = st.selectbox(
        "Select Model",
        ["gpt-3.5-turbo", "gpt-4", "gemini-pro"] if provider != "Ollama" else ["llama2"]
    )

# Generate Button
if st.button("Generate Resume and Cover Letter", type="primary"):
    if not job_description:
        st.error("Please paste a job description")
        st.stop()
    
    if not uploaded_file:
        st.error("Please upload your resume")
        st.stop()

    try:
        # Initialize the model
        resume_llm = AutoApplyModel(
            api_key=os.getenv("OPENAI_API_KEY"),
            provider=provider,
            model=model,
            downloads_dir="generated"
        )

        # Save uploaded file
        os.makedirs("uploads", exist_ok=True)
        file_path = os.path.join("uploads", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Process the resume and job description
        with st.spinner("Processing..."):
            # Extract user data
            user_data = resume_llm.user_data_extraction(file_path)
            
            # Extract job details
            job_details, jd_path = resume_llm.job_details_extraction(job_site_content=job_description)
            
            # Generate resume
            resume_path, resume_details = resume_llm.resume_builder(job_details, user_data)
            
            # Generate cover letter
            cv_details, cv_path = resume_llm.cover_letter_generator(job_details, user_data)

        # Display results
        st.success("Generation complete!")
        
        # Show download buttons
        col5, col6 = st.columns(2)
        with col5:
            with open(resume_path, "rb") as f:
                st.download_button(
                    "Download Resume",
                    f,
                    file_name=os.path.basename(resume_path),
                    mime="application/pdf"
                )
        with col6:
            with open(cv_path, "rb") as f:
                st.download_button(
                    "Download Cover Letter",
                    f,
                    file_name=os.path.basename(cv_path),
                    mime="application/pdf"
                )

        # Clean up
        os.remove(file_path)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}") 