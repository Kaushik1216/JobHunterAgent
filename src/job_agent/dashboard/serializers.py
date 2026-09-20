from job_agent.models.schemas import EvaluatedJob
from job_agent.portals.registry import apply_label_for_portal


def serialize_job(job: EvaluatedJob) -> dict:
    payload = job.model_dump(mode="json")
    payload["id"] = job.url_hash()
    payload["apply_label"] = apply_label_for_portal(job.source_portal)
    return payload
