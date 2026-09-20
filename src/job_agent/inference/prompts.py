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
6. Respond with ONLY valid JSON matching the schema below. No markdown, no explanation.
7. DO NOT output any thinking process, reasoning steps, or conversational text. Return only the raw JSON.

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
        "fit_score",
        "summary_reason"
      ]
    }
    return json.dumps(schema, indent=2)
