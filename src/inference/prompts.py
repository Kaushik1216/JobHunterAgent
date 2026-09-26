"""Versioned prompt templates for SLM extraction and evaluation."""

import json

# Version tag for tracking prompt drift
PROMPT_VERSION = "v1.0"

EXTRACTION_SYSTEM_PROMPT = """
You are a precise job posting analyzer. Your task is to extract structured information from a job posting snippet and evaluate candidate-job fit.

RULES:
1. Extract ONLY information explicitly stated in the snippet. DO NOT infer or hallucinate.
2. If years of experience (YOE) is not mentioned, set extracted_min_yoe and extracted_max_yoe to null.
3. If YOE is ambiguous (e.g., "experience preferred"), set yoe_match to false (conservative default).
4. Match skills case-insensitively. Only count a skill as matched if it appears in the snippet.
5. fit_score should be between 0.0 and 1.0, calculated as: (matched_skills_count / total_required_skills) * yoe_weight
   - yoe_weight = 1.0 if YOE matches or is unspecified, 0.5 if YOE doesn't match
6. Extract `posted_days_ago` if the snippet mentions when it was posted (e.g. "3 days ago" -> 3, "1 week ago" -> 7, "Posted 10:38 AM" -> 0). If not mentioned, set to null.
7. Respond with ONLY valid JSON matching the schema below. No markdown, no explanation.
8. DO NOT output any thinking process, reasoning steps, or conversational text. Return only the raw JSON.

OUTPUT JSON SCHEMA:
{schema}
"""

def build_extraction_prompt(snippet: str, company: str, title: str, location: str, target_yoe: int, core_skills: list[str]) -> str:
    """Build the user prompt for extraction."""
    
    prompt = f"""TARGET CANDIDATE PROFILE:
- Target YOE: {target_yoe}
- Core Skills: {', '.join(core_skills)}

JOB DETAILS:
- Company: {company}
- Title: {title}
- Location: {location}
- Snippet: {snippet}

Analyze this job posting based on the target profile and output JSON with these exact keys:
- title (string)
- company (string)
- location (string)
- extracted_min_yoe (integer or null)
- extracted_max_yoe (integer or null)
- yoe_match (boolean)
- matched_skills (array of string)
- missing_skills (array of string)
- posted_days_ago (integer or null)
- fit_score (number between 0.0 and 1.0)
- summary_reason (short string explanation)

EXAMPLE OUTPUT FORMAT:
{{
  "title": "{title}",
  "company": "{company}",
  "location": "{location}",
  "extracted_min_yoe": 2,
  "extracted_max_yoe": 4,
  "yoe_match": true,
  "matched_skills": ["Python"],
  "missing_skills": ["Docker"],
  "posted_days_ago": 3,
  "fit_score": 0.8,
  "summary_reason": "Matches candidate profile and target skills."
}}

Output ONLY the JSON object. Do not include extra text.
"""
    return prompt

def get_correction_prompt(error_message: str) -> str:
    """Build a corrective prompt when SLM output fails validation."""
    return f"""
Your previous output failed validation with the following error:
{error_message}

Please correct the JSON and return ONLY the valid JSON matching the schema. No markdown, no explanations.
"""

def get_extraction_schema() -> str:
    """Return the JSON schema string for EvaluatedJob extraction output."""
    schema = {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "company": {"type": "string"},
        "location": {"type": "string"},
        "extracted_min_yoe": {"type": ["integer", "null"]},
        "extracted_max_yoe": {"type": ["integer", "null"]},
        "yoe_match": {"type": "boolean"},
        "matched_skills": {
          "type": "array",
          "items": {"type": "string"}
        },
        "missing_skills": {
          "type": "array",
          "items": {"type": "string"}
        },
        "posted_days_ago": {"type": ["integer", "null"]},
        "fit_score": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0
        },
        "summary_reason": {"type": "string"},
        "apply_url": {"type": "string"},
        "source_query": {"type": "string"},
        "raw_snippet": {"type": "string"},
        "status": {"type": "string"}
      },
      "required": [
        "title",
        "company",
        "location",
        "extracted_min_yoe",
        "extracted_max_yoe",
        "yoe_match",
        "matched_skills",
        "missing_skills",
        "posted_days_ago",
        "fit_score",
        "summary_reason"
      ]
    }
    return json.dumps(schema, indent=2)


RESUME_EXTRACTION_SYSTEM_PROMPT = """
You are an expert technical talent analyst and resume parser.
Your task is to analyze candidate resumes and extract exhaustive, high-fidelity structured profile data.

RULES:
1. Extract all technical skills and tools explicitly mentioned or clearly evident in the candidate's work and projects.
2. Group skills into languages, frameworks_and_libraries, databases, cloud_and_devops, tools_and_platforms, and core_competencies.
3. For each work experience entry: extract company name, role/title, employment dates, current status, technologies used, achievements (bullet points with impact/metrics), and description.
4. For each project: extract project title, role, technologies used, description, highlights, and any github/demo link.
5. Accurately calculate or estimate total_experience_years based on work history date ranges. If fresh graduate / student, set to 0.0 or < 1.0.
6. Infer target_roles (e.g. "Senior Software Engineer", "Backend Developer", "Full Stack Engineer") and domains_and_industries (e.g. "FinTech", "SaaS", "Distributed Systems").
7. Extract education (degrees, colleges, years) and certifications.
8. Respond with ONLY valid JSON matching the schema. No markdown backticks, no explanatory conversational text, and no thinking tokens.
"""

def build_resume_extraction_prompt(resume_text: str) -> str:
    """Build the extraction prompt containing the raw resume content."""
    prompt = f"""RESUME CONTENT TO ANALYZE:
---
{resume_text}
---

Extract all candidate details into valid JSON with this exact schema:
{{
  "name": "Candidate Full Name or null",
  "email": "candidate email or null",
  "phone": "candidate phone or null",
  "location": "City, Country or null",
  "linkedin_url": "url or null",
  "github_url": "url or null",
  "portfolio_url": "url or null",
  "headline": "e.g. Senior Backend Engineer | Python & Distributed Systems",
  "summary": "comprehensive professional summary highlighting strengths and years of experience",
  "total_experience_years": 4.5,
  "skills": {{
    "languages": ["Python", "Go", "TypeScript", "SQL"],
    "frameworks_and_libraries": ["FastAPI", "React", "Docker", "PyTorch"],
    "databases": ["PostgreSQL", "Redis", "MongoDB"],
    "cloud_and_devops": ["AWS", "Docker", "Kubernetes", "CI/CD"],
    "tools_and_platforms": ["Git", "Linux", "Kafka"],
    "core_competencies": ["System Design", "Microservices", "REST APIs"],
    "all_skills": ["Python", "Go", "FastAPI", "PostgreSQL", ...]
  }},
  "work_experience": [
    {{
      "company": "Company Name",
      "role": "Software Engineer",
      "location": "Bengaluru, India or null",
      "start_date": "Jan 2022",
      "end_date": "Present",
      "is_current": true,
      "technologies": ["Python", "FastAPI", "AWS", "PostgreSQL"],
      "achievements": [
        "Scaled backend APIs to 50k requests per minute with 99.9% uptime",
        "Refactored legacy monolith into event-driven microservices"
      ],
      "description": "Led development of core matching algorithms and customer search platform."
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "role": "Creator / Lead Developer or null",
      "technologies": ["React", "FastAPI", "SQLite"],
      "description": "Autonomous multi-portal job agent with local SLM scoring.",
      "highlights": ["Zero-token discovery mode", "Real-time WAL concurrency"],
      "link": "https://github.com/..."
    }}
  ],
  "education": [
    {{
      "institution": "University / College Name",
      "degree": "B.Tech in Computer Science",
      "field_of_study": "Computer Science & Engineering",
      "graduation_year": "2022",
      "grade": "8.8 CGPA or null"
    }}
  ],
  "certifications": ["AWS Certified Solutions Architect", "CKA"],
  "target_roles": ["Software Engineer", "Backend Developer", "Full Stack Engineer"],
  "domains_and_industries": ["FinTech", "Cloud Infrastructure", "Enterprise SaaS"],
  "key_strengths": ["Fast API Development", "High Concurrency", "System Architecture"]
}}

Output ONLY the JSON object. Do not include markdown fences or any extra text.
"""
    return prompt

