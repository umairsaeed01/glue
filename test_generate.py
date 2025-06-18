import os
import json
from dotenv import load_dotenv
from zlm import AutoApplyModel

# Load environment variables
load_dotenv()

# Minimal user data (customize as needed)
user_data = {
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

# Save user data to a JSON file for the pipeline
user_data_path = "user_data.json"
with open(user_data_path, "w") as f:
    json.dump(user_data, f, indent=2)

# Job description (replace with your actual job description)
job_description = """
C++ Software Engineer
Forge Dynamics Pty Ltd
View all jobs

Sydney NSW
Engineering - Software (Information & Communication Technology)
Contract/Temp
$130,000 – $160,000 per year
Posted 22h ago
•
Less than 20 applicants


About us

We are a small, Australian-owned and operated company delivering cutting-edge telemetry-analytics solutions for the Defence sector. We move fast, embrace modern C++, and offer you the freedom to work fully remote or from our Sydney offices on your terms.

Qualifications & Experience

Bachelor's degree in Engineering (preferred) or Computer Science
5+ years (2× Mid-Level roles) / 10+ years (1× Senior role) of low-latency, high-performance desktop C++ development
Strong mastery of modern C++ (C++20+) and the STL
Proven track record in low-latency algorithm development, high-throughput networking, and time-series relational databases
Experience building Windows desktop applications with Visual Studio (or equivalent)
Solid understanding of multithreading, IPC, and real-time ("soft"-deterministic) systems
Sound knowledge and practical use of object-oriented design principles and abstraction patterns
Baseline AGSVA security clearance required; NV1 or higher preferred
Desirable Skills & Experience

Experience with CMake and Ninja build systems
Experience in cross-compilation for Linux targets
Experience in data science and/or machine learning
Experience in refactoring and optimising existing code to drive higher performance
Experience in front-end UI integration in C++ (e.g. Qt or other desktop frameworks)
Experience with parallel/GPU compute (CUDA, OpenCL), hardware-accelerated graphics APIs (OpenGL, DirectX) and 3D engine platforms (Unreal, Omniverse)
Experience in Agile software development and tooling (e.g. Git, Jira, Confluence)
Tasks & Responsibilities

Design, develop and optimise C++ modules for data ingestion, processing and analytics
Develop and implement high-performance, low-latency, scalable data processing pipelines and networking architectures
Build and maintain test suites, continuous integration pipelines and conduct code reviews
Contribute to architectural decisions in a small, cross-functional team
Mentor junior and mid-level engineers (senior role)
Benefits

Flexible work – fully remote or hybrid from our modern Sydney office
Impactful projects – mission-critical Defence systems
Career growth – clear pathways to senior and technical-lead roles
Collaborative culture – small teams, short feedback loops, direct stakeholder access
Employer questions
Your application will include the following questions:
Which of the following statements best describes your right to work in Australia?
How many years' experience do you have as a software engineer?
Do you hold Australian Security Clearance?
Which of the following programming languages are you experienced in?
Have you completed a qualification in engineering?
"""

# Path to the old resume file
old_resume_path = "resources/resume"

# Initialize the model
resume_llm = AutoApplyModel(
    api_key=os.getenv("OPENAI_API_KEY"),
    provider="GPT",
    model="gpt-3.5-turbo",
    downloads_dir="generated"
)

# Run the resume_cv_pipeline with the job description and old resume path
print("Starting resume_cv_pipeline...")
try:
    resume_llm.resume_cv_pipeline(job_description, user_data_path, old_resume_path)
    print("Pipeline completed. Check the generated files in the 'generated' directory.")
except Exception as e:
    print(f"Error during pipeline execution: {e}") 