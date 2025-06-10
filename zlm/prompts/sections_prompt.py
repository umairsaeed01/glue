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
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Include relevant certifications aligned with the job description.
2. Proofreading: Ensure impeccable spelling and grammar.

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
    "to_date": "Actual End Date" (If no date mention dont write any thing like None/Nil/-)  ,
    "grade": "Actual Grade (if available)",
    "coursework": [
      "Actual relevant coursework listed from provided resume",
      [and So on ...]
    ]
  }}
  [and So on ...]
],
</example>

{format_instructions}
"""


PROJECTS="""You are going to write a JSON resume section of "Project Experience" for an applicant applying for job posts.

Step to follow:
1. Analyze my projects details to match job requirements.
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Craft highly relevant project experiences aligned with the job description. dont miss any project from the resume put all projects.
2. Content:
  2.1. Bullet points: 3 per experience, closely mirroring job requirements.
  2.2. Impact: Quantify each bullet point for measurable results.
  2.3. Storytelling: Utilize STAR methodology (Situation, Task, Action, Result) implicitly within each bullet point.
  2.4. Action Verbs: Showcase soft skills with strong, active verbs.
  2.5. Honesty: Prioritize truthfulness and objective language.
  2.6. Structure: Each bullet point follows "Did X by doing Y, achieved Z" format.
  2.7. Specificity: Prioritize relevance to the specific job over general achievements.
3. Style:
  3.1. Clarity: Clear expression trumps impressiveness.
  3.2. Voice: Use active voice whenever possible.
  3.3. Proofreading: Ensure impeccable spelling and grammar.

<PROJECTS>
{section_data}
</PROJECTS>

<job_description>
{job_description}
</job_description>

<example>
"projects": [
    {{
   "name": "Actual Project Name from Resume",
      "type": "Actual Type from Resume",
      "link": "Actual Link if provided, else omit",
      "from_date": "Actual Start Date",
      "to_date": "Actual End Date or completion date explicitly stated" If no date mention dont write any thing like None/Nil,
      "description": [
        "Actual clearly stated achievement from provided resume",
        "Explicitly mentioned measurable impact from resume",
        "Clearly detailed activity or contribution from provided resume",
        [and So on ...]
      ]
    }}
    [and So on ...]
  ]
  </example>
  
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
Skills from the job description directly aligned with the candidate’s education and professional background. For example, if the candidate studied software engineering but did not explicitly mention "C#" in their resume, yet the job requires "C#", include "C#" in the skills list.
Think contextually, matching the candidate’s education and experience with the job requirements."]
    }},
    and so on ...
  ]
</example>
  
  {format_instructions}
  """


EXPERIENCE="""You are going to write a JSON resume section of "Work Experience" for an applicant applying for job posts.

Step to follow:
1. Analyze my Work details to match job requirements.
2. Create a JSON resume section that highlights strongest matches
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Strictly NO fabrication: Do NOT include roles, companies, or achievements not explicitly listed in the provided resume.
2. Content:
  2.1. Maintain exact accuracy regarding role titles, dates, and companies as given.
  2.2. Impact: Quantify each bullet point for measurable results.
  2.3. Storytelling: Utilize STAR methodology (Situation, Task, Action, Result) implicitly within each bullet point.
  2.4. Action Verbs: Showcase soft skills with strong, active verbs.
  2.5. Honesty: Prioritize truthfulness and objective language.
  2.6. Structure: Each bullet point follows "Did X by doing Y, achieved Z" format.
  2.7. Specificity: Prioritize relevance to the specific job over general achievements.
3. Style:
  3.1. Clarity: Clear expression trumps impressiveness.
  3.2. Voice: Use active voice whenever possible.
  3.3. Proofreading: Ensure impeccable spelling and grammar.

<work_experience>
{section_data}
</work_experience>

<job_description>
{job_description}
</job_description>

<example>
"work_experience": [
{{
      "role": "Actual Role Title from Resume",
      "company": "Actual Company from Resume",
      "location": "Actual Location from Resume",
      "from_date": "Actual Start Date",
      "to_date": "Actual End Date",
      "description": [
        "Explicitly mentioned responsibility or achievement from provided resume",
        "Quantified and clearly stated impact from provided resume"
      ]
    }}
]
</example>

{format_instructions}
"""