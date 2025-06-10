# ResumeFlow: An LLM-facilitated Pipeline for Personalized Resume Generation and Refinement 

[![Demo Page](https://img.shields.io/badge/Project-Demo-FF4B4B?logo=streamlit)](https://resumeflow.streamlit.app/)
[![ACM Digital Library](https://img.shields.io/badge/ACM-0085CA?logo=acm&logoColor=fff&style=flat)](https://dl.acm.org/doi/10.1145/3626772.3657680)
[![arxiv paper](https://img.shields.io/badge/arXiv-Paper-B31B1B?logo=arxiv)](https://arxiv.org/abs/2402.06221)
[![PyPI Latest Release](https://img.shields.io/pypi/v/zlm.svg?label=PyPI&color=3775A9&logo=pypi)](https://pypi.org/project/zlm/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/zlm.svg?label=PyPI%20downloads&color=blueviolet&target=blank)](https://pypi.org/project/zlm/)
[![GitHub issues open](https://img.shields.io/github/issues/Ztrimus/job-llm.svg?color=orange&label=Issues&logo=github)](https://github.com/Ztrimus/job-llm/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-success.svg?logo)](https://github.com/Ztrimus/job-llm/blob/main/LICENSE)

[![Click here to see image of "Auto Job Aligned Personalized Resume Generation Pipeline"](https://github.com/Ztrimus/job-llm/blob/main/resources/auto_job_apply_workflow.jpg)](https://github.com/Ztrimus/job-llm/blob/main/resources/auto_job_apply_workflow.jpg)
<br>For **Video Demonstration** visit the YouTube link: https://youtu.be/Agl7ugyu1N4

Project can be:
 - Access as a **Web Tool** from https://resumeflow.streamlit.app/
 - Install as a **Python Package** from https://pypi.org/project/zlm/
 - Download as **Source Code** from https://github.com/Ztrimus/job-llm.git
 
All other known bugs, fixes, feedbacks, and feature requests can be reported on the [GitHub issues](https://github.com/Ztrimus/job-llm/issues) page.

**Empower others, just like they helped you!** Contribute to this open source project & make a difference. ✨ *Create a branch, improve the code, & raise a pull request!*

#### Author & Contributor List

 - [Saurabh Zinjad](https://linkedin.com/in/saurabhzinjad) | [Ztrimus](https://github.com/Ztrimus) | szinjad@asu.edu
 - [Amey Bhilegaonkar](https://www.linkedin.com/in/amey-bhilegaonkar) | [ameygoes](https://github.com/ameygoes) | abhilega@asu.edu
 - [Amrita Bhattacharjee](https://www.linkedin.com/in/amritabh) | [Amritabh](https://github.com/Amritabh) | abhatt43@asu.edu

## 1. Introduction:
### 1.1. Our Proposal
We're aiming to create a automated system that makes applying for jobs a breeze. Job hunting has many stages, and we see a chance to automate things and use LLM (Language Model) to make it even smoother. We're looking at different ways, both the usual and some new ideas, to integrate LLM into the job application process. The goal is to reduce how much you have to do and let LLM do its thing, making the whole process easier for you.
### 1.2. References
- [40+ AWESOME RESUME STATISTICS [2023]: WHAT JOB SEEKERS NEED TO KNOW](https://www.zippia.com/advice/resume-statistics/)
### 1.3. Refer to this [Paper](https://arxiv.org/abs/2402.06221) for more details.

## 2. Setup, Installation and Usage
### 2.1. Prerequisites
 - OS : Linux, Mac
 - Python : 3.11.6 and above
 - LLM API key: [OpenAI](https://platform.openai.com/account/api-keys) OR [Gemini Pro](https://ai.google.dev/)

### 2.2. Package Installation - Use as Library

```bash
pip install zlm
```

 - Usage

```python
from zlm import AutoApplyModel

job_llm = AutoApplyModel(
    api_key="PROVIDE_API_KEY", 
    provider="ENTER PROVIDER <gemini> or <openai>",
    downloads_dir="[optional] ENTER FOLDER PATH WHERE FILE GET DOWNLOADED, By default, 'downloads' folder"
)

job_llm.resume_cv_pipeline(
    "ENTER_JOB_URL", 
    "YOUR_MASTER_RESUME_DATA" # .pdf or .json
) # Return and downloads curated resume and cover letter.
```

### 2.4. Setup & Run Code - Use as Project

```sh
git clone https://github.com/Ztrimus/job-llm.git
cd job-llm
```
 1. Create and activate python environment (use `python -m venv .env` or conda or etc.) to avoid any package dependency conflict.
 2. Install [Poetry package](https://python-poetry.org/docs/basic-usage/) (dependency management and packaging tool)
    ```bash
    pip install poetry
    ```
 3. Install all required packages.
     - Refer [pyproject.toml](pyproject.toml) or [poetry.lock](poetry.lock) for list of packages.
        ```bash
        poetry install
        ```
        OR
     - If above command not working, we also provided [requirements.txt](resources/requirements.txt) file. But, we recommend using poetry.
        ```bash
        pip install -r resources/requirements.txt
        ```
4. We also need to install following packages to conversion of latex to pdf
    - For linux
        ```bash
        sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-fonts-extra
        ```
        NOTE: try `sudo apt-get update` if terminal unable to locate package.
    - For Mac
        ```bash
        brew install basictex
        sudo tlmgr install enumitem fontawesome
        ```
5. If you want to run ollama models
    ```sh
    ollama pull llama3.1
    ```
6. Run following script to get result
```bash
>>> python main.py /
    --url "JOB_POSTING_URL" /
    --master_data="JSON_USER_MASTER_DATA" /
    --api_key="YOUR_LLM_PROVIDER_API_KEY" / # put api_key considering provider
    --downloads_dir="DOWNLOAD_LOCATION_FOR_RESUME_CV" /
    --provider="openai" # openai, gemini
```

## 3. Citations
If you find JobLLM useful in your research or applications, please consider giving us a star 🌟 and citing it.

```bibtex
@inproceedings{10.1145/3626772.3657680,
author = {Zinjad, Saurabh Bhausaheb and Bhattacharjee, Amrita and Bhilegaonkar, Amey and Liu, Huan},
title = {ResumeFlow: An LLM-facilitated Pipeline for Personalized Resume Generation and Refinement},
series = {SIGIR '24},
booktitle = {Proceedings of the 47th International ACM SIGIR Conference on Research and Development in Information Retrieval},
publisher = {Association for Computing Machinery},
doi = {10.1145/3626772.3657680},
url = {https://doi.org/10.1145/3626772.3657680},
year = {2024},
isbn = {9798400704314},
location = {Washington DC, USA},
address = {New York, NY, USA},
}
```

```bibtex
@misc{zinjad2024resumeflow,
      title={ResumeFlow: An LLM-facilitated Pipeline for Personalized Resume Generation and Refinement}, 
      author={Saurabh Bhausaheb Zinjad and Amrita Bhattacharjee and Amey Bhilegaonkar and Huan Liu},
      year={2024},
      eprint={2402.06221},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```

## 4. License
JobLLM is under the MIT License and is supported for commercial usage.

## 5. TODO
Need to find way to install following command in streamlit
```sh
ollama
playwright
"ollama pull llama3.1"
"ollama pull bge-m3"
```

## 4. References
 - [Prompt engineering Guidelines](https://platform.openai.com/docs/guides/prompt-engineering)
 - [Overleaf LaTex Resume Template](https://www.overleaf.com/latex/templates/jakes-resume-anonymous/cstpnrbkhndn)
 - [Combining LaTeX with Python](https://tug.org/tug2019/slides/slides-ziegenhagen-python.pdf)
 - [OpenAI Documentation](https://platform.openai.com/docs/api-reference/chat/create)
