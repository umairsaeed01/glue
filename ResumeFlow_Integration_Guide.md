# ResumeFlow: AI-Powered Resume and Cover Letter Generator

## Project Overview
ResumeFlow is an intelligent system that automatically generates tailored resumes and cover letters based on job descriptions. It uses AI (specifically LLMs like GPT-4 and Gemini) to analyze job requirements and create personalized application materials that highlight relevant skills and experiences.

### Key Features
- Automated resume tailoring to match job requirements
- Cover letter generation
- PDF generation with professional formatting
- Support for multiple LLM providers (OpenAI, Gemini, Ollama)
- Web interface for easy interaction
- Command-line interface for automation

### Project Structure
The project is organized into several key components:

1. Web Interface (`web_app.py`)
2. Core Package (`zlm/`)
3. Utility Modules
4. Templates and Resources
5. Configuration Files

Let's examine each component in detail:

## 1. Web Interface (web_app.py)
The main entry point for the web application. It provides a user-friendly interface for:
- Uploading resumes
- Entering job descriptions
- Selecting LLM providers
- Generating and downloading tailored resumes and cover letters

```python
# web_app.py
import os
import json
from dotenv import load_dotenv
import base64
import shutil
import zipfile
import streamlit as st

from zlm import AutoApplyModel
from zlm.utils.utils import display_pdf, download_pdf, read_file, read_json
from zlm.utils.metrics import jaccard_similarity, overlap_coefficient, cosine_similarity
from zlm.variables import LLM_MAPPING

# ... [Previous code content] ...
```

## 2. Core Package (zlm/)

### 2.1 Main Package (__init__.py)
The core package that coordinates the entire resume generation process.

```python
# zlm/__init__.py
import os
import json
import re
import validators
import numpy as np
import streamlit as st

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from zlm.schemas.sections_schemas import ResumeSchema
from zlm.utils import utils
from zlm.utils.latex_ops import latex_to_pdf
from zlm.utils.llm_models import ChatGPT, Gemini, OllamaModel
from zlm.utils.data_extraction import read_data_from_url, extract_text
from zlm.utils.metrics import jaccard_similarity, overlap_coefficient, cosine_similarity, vector_embedding_similarity
from zlm.prompts.resume_prompt import CV_GENERATOR, RESUME_WRITER_PERSONA, JOB_DETAILS_EXTRACTOR, RESUME_DETAILS_EXTRACTOR
from zlm.schemas.job_details_schema import JobDetails
from zlm.variables import DEFAULT_LLM_MODEL, DEFAULT_LLM_PROVIDER, LLM_MAPPING, section_mapping

# ... [Previous code content] ...
```

### 2.2 Variables (variables.py)
Configuration variables and mappings for the project.

```python
# zlm/variables.py
from zlm.prompts.sections_prompt import EXPERIENCE, SKILLS, PROJECTS, EDUCATIONS, CERTIFICATIONS, ACHIEVEMENTS
from zlm.schemas.sections_schemas import Achievements, Certifications, Educations, Experiences, Projects, SkillSections

# ... [Previous code content] ...
```

## 3. Utility Modules

### 3.1 Data Extraction (utils/data_extraction.py)
Handles extraction of data from PDFs and URLs.

```python
# zlm/utils/data_extraction.py
import re
import json
import PyPDF2
import requests
from bs4 import BeautifulSoup
import streamlit as st
from langchain_community.document_loaders import PlaywrightURLLoader, UnstructuredURLLoader, WebBaseLoader

# ... [Previous code content] ...
```

### 3.2 LLM Models (utils/llm_models.py)
Implements different LLM providers and their interactions.

```python
# zlm/utils/llm_models.py
import json
import textwrap
from openai import OpenAI
import openai
import pandas as pd
import streamlit as st
from openai import OpenAI
from langchain_community.llms.ollama import Ollama
from langchain_ollama import OllamaEmbeddings
import google.generativeai as genai
from google.generativeai.types.generation_types import GenerationConfig

# ... [Previous code content] ...
```

### 3.3 LaTeX Operations (utils/latex_ops.py)
Handles LaTeX template rendering and PDF generation.

```python
# zlm/utils/latex_ops.py
import os
import jinja2
import streamlit as st
from zlm.utils.utils import write_file, save_latex_as_pdf

# ... [Previous code content] ...
```

### 3.4 Metrics (utils/metrics.py)
Implements various similarity metrics for matching resumes to job descriptions.

```python
# zlm/utils/metrics.py
import re
import json
import math
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise
from zlm.utils.utils import key_value_chunking
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize

# ... [Previous code content] ...
```

## 4. Templates and Resources

### 4.1 Resume Prompts (prompts/resume_prompt.py)
Contains the prompts used for generating resumes and cover letters.

```python
# zlm/prompts/resume_prompt.py
# ... [Previous code content] ...
```

### 4.2 Section Prompts (prompts/sections_prompt.py)
Contains prompts for different resume sections.

```python
# zlm/prompts/sections_prompt.py
# ... [Previous code content] ...
```

## 5. Configuration Files

### 5.1 Environment Variables (.env)
Contains API keys and other configuration.

```
OPENAI_API_KEY=your_api_key_here
```

### 5.2 Project Dependencies (pyproject.toml)
Lists all project dependencies.

```toml
# pyproject.toml
[tool.poetry]
name = "zlm"
version = "0.1.0"
description = "AI-powered resume and cover letter generator"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
streamlit = "^1.31.0"
openai = "^1.12.0"
google-generativeai = "^0.3.2"
langchain = "^0.1.0"
beautifulsoup4 = "^4.12.0"
PyPDF2 = "^3.0.0"
jinja2 = "^3.1.0"
nltk = "^3.8.0"
scikit-learn = "^1.4.0"
fpdf = "^1.7.0"
markdown-pdf = "^0.0.1"
python-dotenv = "^1.0.0"
validators = "^0.22.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

## Integration Guide

### Step 1: Setup
1. Install dependencies:
```bash
pip install poetry
poetry install
```

2. Set up environment variables:
```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Step 2: Running the Application
1. Web Interface:
```bash
streamlit run web_app.py
```

2. Command Line:
```bash
python main.py -u "JOB_POSTING_URL" -m "PATH_TO_MASTER_DATA" -d "DOWNLOAD_DIR" -p "openai" -l "MODEL_NAME"
```

### Step 3: Integration Points
To integrate this into a larger project:

1. Import the core package:
```python
from zlm import AutoApplyModel
```

2. Initialize the model:
```python
resume_llm = AutoApplyModel(
    api_key="YOUR_API_KEY",
    provider="openai",
    model="gpt-4",
    downloads_dir="path/to/output"
)
```

3. Generate resume and cover letter:
```python
# Extract user data
user_data = resume_llm.user_data_extraction("path/to/resume.pdf")

# Extract job details
job_details, jd_path = resume_llm.job_details_extraction(url="JOB_POSTING_URL")

# Generate resume
resume_path, resume_details = resume_llm.resume_builder(job_details, user_data)

# Generate cover letter
cv_path = resume_llm.cover_letter_generator(job_details, user_data)
```

## Customization Points

1. **Templates**: Modify LaTeX templates in `zlm/templates/` to change resume formatting
2. **Prompts**: Adjust prompts in `zlm/prompts/` to change generation style
3. **Schemas**: Update schemas in `zlm/schemas/` to modify data structure
4. **Metrics**: Customize similarity metrics in `zlm/utils/metrics.py`

## Best Practices

1. Always validate input data before processing
2. Use appropriate error handling for API calls
3. Implement rate limiting for API requests
4. Cache generated content when possible
5. Monitor API usage and costs
6. Keep templates and prompts up to date
7. Regularly update dependencies

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**:
   - Verify API key in .env file
   - Check API key permissions
   - Ensure proper environment variable loading

2. **PDF Generation Issues**:
   - Install required LaTeX packages
   - Check template syntax
   - Verify file permissions

3. **Web Scraping Issues**:
   - Install required packages (unstructured, playwright)
   - Check URL accessibility
   - Verify network connectivity

4. **Performance Issues**:
   - Use appropriate model size
   - Implement caching
   - Optimize prompt length

## Future Improvements

1. Add support for more LLM providers
2. Implement resume parsing improvements
3. Add more template options
4. Enhance error handling
5. Add unit tests
6. Implement caching system
7. Add progress tracking
8. Enhance security features

## License
This project is licensed under the MIT License. See the LICENSE file for details. 