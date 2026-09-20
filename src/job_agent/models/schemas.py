import hashlib
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from job_agent.models.enums import JobStatus

class GlobalFilters(BaseModel):
    model_config = ConfigDict(strict=True)
    target_yoe: int
    preferred_locations: list[str]
    core_skills: list[str]

class SearchTarget(BaseModel):
    model_config = ConfigDict(strict=True)
    company: str
    title: str
    location: str
    target_yoe: int | None = None
    posted_days_ago: int | None = None
    core_skills: list[str] | None = None

    def merge_with_globals(self, globals_filter: GlobalFilters) -> "SearchTarget":
        return SearchTarget(
            company=self.company,
            title=self.title,
            location=self.location,
            target_yoe=self.target_yoe if self.target_yoe is not None else globals_filter.target_yoe,
            core_skills=self.core_skills if self.core_skills is not None else globals_filter.core_skills
        )

class CriteriaConfig(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    global_filters: GlobalFilters = Field(alias="global")
    targets: list[SearchTarget]

    def resolve_targets(self) -> list[SearchTarget]:
        return [target.merge_with_globals(self.global_filters) for target in self.targets]

class RawJobResult(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str
    url: HttpUrl
    snippet: str
    source_query: str = ""
    source_portal: str = "unknown"

class EvaluatedJob(BaseModel):
    model_config = ConfigDict(
        strict=True,
        json_schema_extra={
            "example": {
                "title": "Software Engineer",
                "company": "Stripe",
                "location": "Remote",
                "extracted_min_yoe": 2,
                "extracted_max_yoe": 5,
                "yoe_match": True,
                "matched_skills": ["Python", "Docker"],
                "missing_skills": ["FastAPI"],
                "fit_score": 0.85,
                "summary_reason": "Good match on core skills, meets YoE requirements.",
                "apply_url": "https://linkedin.com/jobs/view/12345",
                "source_query": "stripe software engineer remote",
                "source_portal": "linkedin",
                "raw_snippet": "We are looking for...",
                "status": "NEW"
            }
        }
    )
    title: str
    company: str
    location: str
    extracted_min_yoe: int | None
    extracted_max_yoe: int | None
    yoe_match: bool
    matched_skills: list[str]
    missing_skills: list[str]
    fit_score: float = Field(ge=0.0, le=1.0)
    summary_reason: str
    apply_url: str
    source_query: str = ""
    source_portal: str = "unknown"
    raw_snippet: str = ""
    status: JobStatus = JobStatus.NEW
    evaluated: bool = True
    search_title: str = ""
    target_yoe: int | None = None
    posted_days_ago: int | None = None
    core_skills: list[str] = Field(default_factory=list)

    def url_hash(self) -> str:
        return hashlib.sha256(self.apply_url.encode("utf-8")).hexdigest()

    @classmethod
    def from_discovery(cls, result: RawJobResult, target: SearchTarget) -> "EvaluatedJob":
        """Placeholder row for a listing that has been searched but not matched yet."""
        return cls(
            title=result.title,
            company=target.company or "Unknown",
            location=target.location or "Unknown",
            extracted_min_yoe=None,
            extracted_max_yoe=None,
            yoe_match=False,
            matched_skills=[],
            missing_skills=[],
            fit_score=0.0,
            summary_reason="Not evaluated yet",
            apply_url=str(result.url),
            source_query=result.source_query,
            source_portal=result.source_portal,
            raw_snippet=result.snippet,
            status=JobStatus.DISCOVERED,
            evaluated=False,
            search_title=target.title,
            target_yoe=target.target_yoe,
            core_skills=list(target.core_skills or []),
            posted_days_ago=None,
        )

class ExecutionSummary(BaseModel):
    model_config = ConfigDict(strict=True)
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    total_targets: int = 0
    jobs_found: int = 0
    jobs_qualified: int = 0
    jobs_skipped_dedup: int = 0
    jobs_skipped_low_score: int = 0
    jobs_errored: int = 0
    avg_inference_latency_ms: float = 0.0
    avg_search_latency_ms: float = 0.0
    mode: str = "search_and_match"
    jobs_discovered: int = 0

    @property
    def duration_seconds(self) -> float:
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def qualification_rate(self) -> float:
        if self.jobs_found == 0:
            return 0.0
        return self.jobs_qualified / self.jobs_found
