import yaml
from pathlib import Path
from pydantic import ValidationError

from job_agent.models.schemas import CriteriaConfig
from job_agent.exceptions import CriteriaParseError

def parse_criteria(criteria_path: Path) -> CriteriaConfig:
    """Parse criteria.yaml and return validated CriteriaConfig."""
    if not criteria_path.exists():
        raise CriteriaParseError(f"Criteria file not found at {criteria_path}")
    
    if not criteria_path.is_file():
        raise CriteriaParseError(f"Criteria path is not a file: {criteria_path}")

    try:
        with open(criteria_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if data is None:
            raise CriteriaParseError(f"Criteria file is empty: {criteria_path}")
            
    except yaml.YAMLError as e:
        raise CriteriaParseError(f"Failed to parse YAML file {criteria_path}: {e}")
    except OSError as e:
        raise CriteriaParseError(f"Failed to read file {criteria_path}: {e}")

    try:
        config = CriteriaConfig.model_validate(data)
        return config
    except ValidationError as e:
        raise CriteriaParseError(f"Criteria validation failed: {e}")
