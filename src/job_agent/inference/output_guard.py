import json
import structlog
import re
from job_agent.models.schemas import EvaluatedJob
from job_agent.exceptions import OutputValidationError
from job_agent.inference.client import OllamaClient
from job_agent.inference.prompts import get_correction_prompt

logger = structlog.get_logger()

class OutputGuard:
    """Validates SLM output against Pydantic schema with retry on failure."""
    
    def __init__(self, client: OllamaClient, max_retries: int = 2) -> None:
        self._client = client
        self._max_retries = max_retries
        self._validation_success_count = 0
        self._validation_failure_count = 0
    
    def validate_and_parse(self, raw_output: str, apply_url: str, source_query: str = "", raw_snippet: str = "") -> EvaluatedJob:
        """Parse raw SLM output into EvaluatedJob, retrying with correction prompt on failure."""
        current_output = raw_output
        
        for attempt in range(self._max_retries + 1):
            try:
                # 1. Extract JSON from raw_output
                parsed_json = self._extract_json(current_output)
                
                # 2. Validate against EvaluatedJob schema
                # We add the missing required fields before validation
                parsed_json["apply_url"] = apply_url
                parsed_json["source_query"] = source_query
                parsed_json["raw_snippet"] = raw_snippet
                if "status" not in parsed_json or not parsed_json["status"]:
                    parsed_json["status"] = "NEW"
                # Convert status string to enum for strict mode
                from job_agent.models.enums import JobStatus
                if isinstance(parsed_json.get("status"), str):
                    try:
                        parsed_json["status"] = JobStatus(parsed_json["status"])
                    except ValueError:
                        parsed_json["status"] = JobStatus.NEW
                
                # Clamp fit_score
                if "fit_score" in parsed_json and isinstance(parsed_json["fit_score"], (int, float)):
                    parsed_json["fit_score"] = max(0.0, min(1.0, float(parsed_json["fit_score"])))
                
                job = EvaluatedJob.model_validate(parsed_json)
                
                # Track success
                if attempt == 0:
                    self._validation_success_count += 1
                    
                logger.debug("Output validation successful")
                return job
                
            except Exception as e:
                # On failure
                if attempt == self._max_retries:
                    self._validation_failure_count += 1
                    logger.error("Output validation failed permanently", error=str(e), raw_output=current_output)
                    raise OutputValidationError(f"Failed to validate SLM output after {self._max_retries} retries: {e}") from e
                
                logger.warning("Output validation failed, retrying with correction prompt", error=str(e), attempt=attempt+1)
                
                # 3. Send correction prompt to SLM
                correction_prompt = get_correction_prompt(str(e))
                # For a correction, we just pass the previous output and the error
                full_prompt = f"Previous Output:\n{current_output}\n\n{correction_prompt}"
                try:
                    current_output = self._client.generate(prompt=full_prompt, system_prompt="You are a JSON fixing assistant.")
                except Exception as gen_e:
                    logger.error("Failed to generate correction", error=str(gen_e))
                    raise OutputValidationError(f"Failed to generate correction: {gen_e}") from gen_e

        raise OutputValidationError("Unreachable code reached in validation loop")
        
    @property
    def schema_adherence_rate(self) -> float:
        """Return the percentage of successful validations."""
        total = self._validation_success_count + self._validation_failure_count
        if total == 0:
            return 1.0
        return self._validation_success_count / total
    
    def _extract_json(self, text: str) -> dict:
        """Extract JSON from potentially messy SLM output."""
        if not text:
            raise OutputValidationError("Empty output provided")
            
        # Strip thinking tags from reasoning models if present
        cleaned_text = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()
        if not cleaned_text:
            cleaned_text = text
            
        # Try direct parse first
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
            
        # Try to find JSON block in markdown code fences
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Try to find first { ... } block
        match = re.search(r'(\{[\s\S]*\})', cleaned_text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        raise OutputValidationError("Could not extract valid JSON from output")
