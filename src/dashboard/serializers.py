from models.schemas import EvaluatedJob, ResumeRecord
from portals.registry import apply_label_for_portal


def serialize_job(job: EvaluatedJob) -> dict:
    payload = job.model_dump(mode="json")
    payload["id"] = job.url_hash()
    payload["apply_label"] = apply_label_for_portal(job.source_portal)
    return payload


def serialize_resume(resume: ResumeRecord) -> dict:
    return resume.model_dump(mode="json")

