"""Job Description TXT file parser.

Reads a plain-text job description file and converts it into SearchTarget
objects that the existing pipeline can process.
"""

from __future__ import annotations

import re
import structlog
from dataclasses import dataclass, field
from pathlib import Path

from job_agent.exceptions import CriteriaParseError
from job_agent.models.schemas import SearchTarget, GlobalFilters, CriteriaConfig

logger = structlog.get_logger(__name__)


@dataclass
class JobDescription:
    """Structured representation of a job description text file."""
    role: str = ""
    company: str = ""
    location: str = ""
    yoe: int = 0
    skills: list[str] = field(default_factory=list)
    description: str = ""


def parse_jd(jd_path: Path) -> JobDescription:
    """Parse a job description text file into a JobDescription dataclass.

    Expected format (case-insensitive keys):
        Role: Software Engineer
        Location: Noida, India
        Experience: 1+ years
        Skills: Python, JavaScript, React
        Description: Looking for ...
    """
    if not jd_path.exists():
        raise CriteriaParseError(f"Job description file not found: {jd_path}")

    try:
        text = jd_path.read_text(encoding="utf-8")
    except OSError as e:
        raise CriteriaParseError(f"Failed to read JD file {jd_path}: {e}") from e

    if not text.strip():
        raise CriteriaParseError(f"Job description file is empty: {jd_path}")

    jd = JobDescription()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Match "Key: Value" pattern
        match = re.match(r"^(role|location|experience|skills|description|company)\s*:\s*(.+)$", line, re.IGNORECASE)
        if not match:
            continue

        key = match.group(1).lower()
        value = match.group(2).strip()

        if key == "role":
            jd.role = value
        elif key == "company":
            jd.company = value
        elif key == "location":
            jd.location = value
        elif key == "experience":
            # Extract first integer from strings like "1+ years", "2-4 years", "3 years"
            yoe_match = re.search(r"(\d+)", value)
            jd.yoe = int(yoe_match.group(1)) if yoe_match else 0
        elif key == "skills":
            jd.skills = [s.strip() for s in value.split(",") if s.strip()]
        elif key == "description":
            jd.description = value

    if not jd.role:
        raise CriteriaParseError("Job description must contain a 'Role:' field")
    if not jd.location:
        raise CriteriaParseError("Job description must contain a 'Location:' field")

    logger.info(
        "parsed_job_description",
        role=jd.role,
        location=jd.location,
        yoe=jd.yoe,
        skills=jd.skills,
    )
    return jd


def jd_to_search_targets(jd: JobDescription) -> list[SearchTarget]:
    """Convert a JobDescription into a list of SearchTarget objects.

    Generates:
    1. A broad search (company="") — catches results from any source
    2. Optionally, targeted searches for well-known job portals
    """
    targets = []

    # Broad search — no company restriction
    # Broad search
    targets.append(
        SearchTarget(
            company=jd.company,
            title=jd.role,
            location=jd.location,
            target_yoe=jd.yoe,
            core_skills=jd.skills,
        )
    )

    # Additional keyword-variant searches for better coverage
    location_city = jd.location.split(",")[0].strip()  # e.g., "Noida" from "Noida, India"

    if location_city.lower() != jd.location.lower():
        targets.append(
            SearchTarget(
                company=jd.company,
                title=jd.role,
                location=location_city,
                target_yoe=jd.yoe,
                core_skills=jd.skills,
            )
        )

    logger.info("generated_search_targets", count=len(targets))
    return targets


def jd_to_criteria_config(jd: JobDescription) -> CriteriaConfig:
    """Convert a JobDescription into a CriteriaConfig for backward compatibility."""
    global_filters = GlobalFilters(
        target_yoe=jd.yoe,
        preferred_locations=[jd.location],
        core_skills=jd.skills,
    )
    targets = [
        SearchTarget(
            company="",
            title=jd.role,
            location=jd.location,
        )
    ]
    return CriteriaConfig(global_filters=global_filters, targets=targets)
