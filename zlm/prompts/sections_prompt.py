ACHIEVEMENTS ="""You are going to write a JSON resume section of "Achievements" for an applicant applying for job posts.

Step to follow:
1. Analyze my achievements details to match job requirements.
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Craft relevant achievements aligned with the job description.
2. Honesty: Prioritize truthfulness and objective language.
3. Specificity: Prioritize relevance to the specific job over general achievements.
4. Style:
  4.1. Voice: Use active voice whenever possible.
  4.2. Proofreading: Ensure impeccable spelling and grammar.

<achievements>
{section_data}
</achievements>

<job_description>
{job_description}
</job_description>

<example>
"achievements": [
    "Award or achievement explicitly stated from provided resume",
    "Quantifiable achievement directly listed from provided resume",
    "Relevant recognition explicitly mentioned in provided resume"
]

</example>

{format_instructions}
"""

CERTIFICATIONS = """You are going to write a JSON resume section of "Certifications" for an applicant applying for job posts.

Step to follow:
1. Analyze my certification details to match job requirements.
2. Create a JSON resume section that highlights the top 3 strongest matches most relevant to the job description.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Include only the top 3 relevant certifications From the list of certifications in the resume aligned with the job description. Do NOT invent or add certifications not explicitly listed in the resume.
2. Proofreading: Ensure impeccable spelling and grammar.

From the list of certifications in the resume, select ONLY the top 3 certifications that are most relevant to the job description below.
- Do NOT include more than 3 certifications.
- Do NOT invent or add certifications not explicitly listed in the resume.
- If fewer than 3 certifications are present, include only those available.
- Output exactly 3 or fewer, sorted by relevance to the job.
- When making the "Certifications:" heading a clickable link, always use the Skillsoft wallet/profile link if it is present in the certifications section (for example, any link containing `/profile/` and `/wallet`). Do NOT use individual certification or issuer links for the heading. If no wallet/profile link is present, do not make the heading a link.

<CERTIFICATIONS>
{section_data}
</CERTIFICATIONS>

<job_description>
{job_description}
</job_description>

<example>
  "certifications": [
    {{
     "name": "Actual Certification Name from Resume",
    "by": "Issuing Organization",
    "link": "Actual provided link if available"    }}
    ...
  ],
</example>

{format_instructions}
"""

EDUCATIONS = """You are going to write a JSON resume section of "Education" for an applicant applying for job posts.

Step to follow:
1. Analyze my education details to match job requirements.
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
- Maintain truthfulness and objectivity in listing experience.
- Prioritize specificity - with respect to job - over generality.
- Proofread and Correct spelling and grammar errors.
- Aim for clear expression over impressiveness.
- Prefer active voice over passive voice.
- CRITICAL DATE RULE: For to_date field, ONLY use dates explicitly stated in the resume. If no end date is provided, write "" (empty string). NEVER write "Present", "Current", "Ongoing", or any assumed dates. NEVER write "-" for dates.

<Education>
{section_data}
</Education>

<job_description>
{job_description}
</job_description>

<example>
"education": [
  {{
    "degree": "Actual Degree from Resume",
    "university": "Actual University from Resume",
    "from_date": "Actual Start Date",
    "to_date": "Actual End Date" (CRITICAL: If no end date is mentioned in the resume, write ONLY "" (empty string). DO NOT write "Present", "Current", or any other assumed date. Only use dates that are explicitly stated in the original resume.),
    "grade": "Actual Grade (if available)",
    "coursework": [
      "Actual relevant coursework listed from provided resume",
      [and So on ...]
    ]
  }}
  [and So on ...]
],
</example>

EXAMPLES OF CORRECT DATE FORMATTING:
- If resume shows: "July 2022 - Present" → Write: "to_date": "July 2022"
- If resume shows: "July 2022 - " → Write: "to_date": ""
- If resume shows: "July 2022" (no end date) → Write: "to_date": ""
- If resume shows: "July 2022 - May 2025" → Write: "to_date": "May 2025"

{format_instructions}
"""


PROJECTS = """You are going to write a JSON resume section of "Projects" for an applicant applying for job posts.

Step to follow:
1. Analyze my project details to match job requirements.
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
- Maintain truthfulness and objectivity in listing experience.
- Prioritize specificity - with respect to job - over generality.
- Proofread and Correct spelling and grammar errors.
- Aim for clear expression over impressiveness.
- Prefer active voice over passive voice.
- CRITICAL DATE RULE: For to_date field, ONLY use dates explicitly stated in the resume. If no end date is provided, write "" (empty string). NEVER write "Present", "Current", "Ongoing", or any assumed dates. NEVER write "-" for dates.

<Projects>
{section_data}
</Projects>

<job_description>
{job_description}
</job_description>

<example>
"projects": [
  {{
    "title": "Actual Project Title from Resume",
    "from_date": "Actual Start Date",
    "to_date": "Actual End Date" (CRITICAL: If no end date is mentioned in the resume, write ONLY "" (empty string). DO NOT write "Present", "Current", or any other assumed date. Only use dates that are explicitly stated in the original resume.),
    "description": [
      "Actual project description from provided resume",
      [and So on ...]
    ],
    "technologies": [
      "Actual technologies used from provided resume",
      [and So on ...]
    ]
  }}
  [and So on ...]
],
</example>

EXAMPLES OF CORRECT DATE FORMATTING:
- If resume shows: "January 2025 - Present" → Write: "to_date": "January 2025"
- If resume shows: "January 2025 - " → Write: "to_date": ""
- If resume shows: "January 2025" (no end date) → Write: "to_date": ""
- If resume shows: "January 2025 - March 2025" → Write: "to_date": "March 2025"

{format_instructions}
"""

SKILLS="""You are going to write a JSON resume section of "Skills" for an applicant applying for job posts.

Step to follow:
1. Analyze my Skills details to match job requirements.
2. Create a JSON resume section that highlights strongest matches.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
- Specificity: Prioritize relevance to the specific job over general achievements.
- Proofreading: Ensure impeccable spelling and grammar.

<SKILL_SECTION>
{section_data}
</SKILL_SECTION>

<job_description>
{job_description}
</job_description>

<example>
"skill_section": [
    {{
   "name": "Category explicitly from resume (e.g., Programming Languages)",
      "skills": ["Extract relevant skills from the provided resume and job description. Include:

Skills explicitly listed in the resume (which are relevant to job description).
Skills from the job description directly aligned with the candidate's education and professional background. For example, if the candidate studied software engineering but did not explicitly mention "C#" in their resume, yet the job requires "C#", include "C#" in the skills list.
Think contextually, matching the candidate's education and experience with the job requirements."]
    }},
    and so on ...
  ]
</example>
  
  {format_instructions}
  """


EXPERIENCE="""You are going to write a JSON resume section of "Experience" for an applicant applying for job posts.

Step to follow:
1. Analyze my experience details to match job requirements.
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
- Maintain truthfulness and objectivity in listing experience.
- Prioritize specificity - with respect to job - over generality.
- Proofread and Correct spelling and grammar errors.
- Aim for clear expression over impressiveness.
- Prefer active voice over passive voice.
- CRITICAL DATE RULE: For to_date field, ONLY use dates explicitly stated in the resume. If no end date is provided, write "" (empty string). NEVER write "Present", "Current", "Ongoing", or any assumed dates. NEVER write "-" for dates.

<Experience>
{section_data}
</Experience>

<job_description>
{job_description}
</job_description>

<example>
"experience": [
  {{
    "title": "Actual Job Title from Resume",
    "company": "Actual Company from Resume",
    "from_date": "Actual Start Date",
    "to_date": "Actual End Date" (CRITICAL: If no end date is mentioned in the resume, write ONLY "" (empty string). DO NOT write "Present", "Current", or any other assumed date. Only use dates that are explicitly stated in the original resume.),
    "location": "Actual Location from Resume",
    "description": [
      "Actual job description from provided resume",
      [and So on ...]
    ]
  }}
  [and So on ...]
],
</example>

EXAMPLES OF CORRECT DATE FORMATTING:
- If resume shows: "January 2025 - Present" → Write: "to_date": "January 2025"
- If resume shows: "January 2025 - " → Write: "to_date": ""
- If resume shows: "January 2025" (no end date) → Write: "to_date": ""
- If resume shows: "January 2025 - March 2025" → Write: "to_date": "March 2025"

{format_instructions}
"""