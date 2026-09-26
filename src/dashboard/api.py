from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yaml


from config import Settings, get_settings
from agent.criteria_parser import parse_criteria
from agent.pipeline import Pipeline
from agent.resume_parser import (
    extract_text_from_file,
    parse_resume_with_ai,
    process_resume_upload,
)
from dashboard.run_manager import RunInProgressError, RunManager
from dashboard.serializers import serialize_job, serialize_resume
from inference.client import LLMClient, check_llm_connection
from inference.output_guard import OutputGuard
from export.markdown_exporter import MarkdownExporter
from observability.metrics import MetricsCollector
from models.enums import JobStatus, RunMode
from models.schemas import SearchTarget
from portals.composite import MultiPortalSearcher
from portals.registry import list_portal_ids, portal_display_name
from database.database import DatabaseManager
from database.repository import JobRepository

WEB_DIR = Path(__file__).parent / "web"


class SettingsUpdate(BaseModel):
    search_portals: list[str]
    companies: list[str]
    ttl_days: int | None = None
    search_max_days: int = 7
    llm_provider: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None


class TestModelRequest(BaseModel):
    base_url: str
    model: str
    api_key: str = ""
    provider: str = "local"


class StatusUpdate(BaseModel):
    status: JobStatus


class RunRequest(BaseModel):
    mode: RunMode
    company: str | None = None
    title: str | None = None
    location: str | None = None


class AppState:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = DatabaseManager(settings.db_path)
        self.db.connect()
        self.db.run_migrations()
        self.repository = JobRepository(self.db)
        self.runs = RunManager(settings)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    state = AppState(resolved)
    app = FastAPI(title="Job Agent Dashboard", version="1.0.0")
    app.state.dashboard = state

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            f"http://127.0.0.1:{resolved.dashboard_port}",
            f"http://localhost:{resolved.dashboard_port}",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_state() -> AppState:
        return app.state.dashboard

    StateDep = Annotated[AppState, Depends(get_state)]


    @app.get("/api/companies")
    def list_companies(ctx: AppState = Depends(get_state)) -> list[dict]:
        return ctx.repository.get_target_companies()

    # --- Resume Profile Management ---

    @app.post("/api/resume/upload")
    async def upload_resume(
        file: UploadFile = File(...),
        ctx: AppState = Depends(get_state),
    ) -> dict:
        """Upload candidate resume, extract text, and run AI structured extraction (one-time job)."""
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

        llm_client = LLMClient(ctx.settings)
        record = process_resume_upload(
            file_bytes=content,
            original_filename=file.filename or "resume",
            resumes_dir=ctx.settings.resumes_dir,
            client=llm_client,
        )
        saved = ctx.repository.save_resume(record)
        return serialize_resume(saved)

    @app.get("/api/resume")
    def list_resumes(ctx: AppState = Depends(get_state)) -> list[dict]:
        """List all resumes uploaded with active indicator."""
        resumes = ctx.repository.list_resumes()
        return [serialize_resume(r) for r in resumes]

    @app.get("/api/resume/active")
    def get_active_resume(ctx: AppState = Depends(get_state)) -> dict:
        """Get the currently active resume profile."""
        resume = ctx.repository.get_active_resume()
        if not resume:
            return {"active": False, "resume": None}
        return {"active": True, "resume": serialize_resume(resume)}

    @app.get("/api/resume/{resume_id}")
    def get_single_resume(resume_id: str, ctx: AppState = Depends(get_state)) -> dict:
        """Get detailed resume profile by ID."""
        resume = ctx.repository.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found.")
        return serialize_resume(resume)

    @app.post("/api/resume/{resume_id}/set-active")
    def set_active_resume(resume_id: str, ctx: AppState = Depends(get_state)) -> dict:
        """Set specified resume as the active profile for candidate matching."""
        success = ctx.repository.set_active_resume(resume_id)
        if not success:
            raise HTTPException(status_code=404, detail="Resume not found.")
        return {"status": "ok", "active_id": resume_id}

    @app.post("/api/resume/{resume_id}/reparse")
    def reparse_resume(resume_id: str, ctx: AppState = Depends(get_state)) -> dict:
        """Re-run AI extraction on existing resume file (e.g. after model switch)."""
        resume = ctx.repository.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found.")

        raw_text = resume.raw_text
        if not raw_text and resume.file_path:
            raw_text = extract_text_from_file(Path(resume.file_path))

        llm_client = LLMClient(ctx.settings)
        parsed_profile = parse_resume_with_ai(raw_text, llm_client)

        updated_record = resume.model_copy(update={
            "raw_text": raw_text,
            "parsed_profile": parsed_profile,
            "candidate_name": parsed_profile.name or resume.candidate_name,
            "headline": parsed_profile.headline or resume.headline,
            "email": parsed_profile.email or resume.email,
            "total_yoe": parsed_profile.total_experience_years if parsed_profile.total_experience_years is not None else resume.total_yoe,
        })
        saved = ctx.repository.save_resume(updated_record)
        return serialize_resume(saved)

    @app.delete("/api/resume/{resume_id}")
    def delete_resume(resume_id: str, ctx: AppState = Depends(get_state)) -> dict:
        """Delete resume record and clean up stored file."""
        file_path = ctx.repository.delete_resume(resume_id)
        if file_path:
            try:
                p = Path(file_path)
                if p.exists() and p.is_file():
                    p.unlink()
            except Exception:
                pass
        return {"status": "deleted", "id": resume_id}


    @app.get("/api/settings")
    def get_user_settings(ctx: AppState = Depends(get_state)) -> dict:
        target_comps = ctx.repository.get_target_companies()
        enabled_companies = [tc["name"] for tc in target_comps if tc["enabled"]]
        if not enabled_companies and ctx.settings.criteria_path.exists():
            try:
                criteria = parse_criteria(ctx.settings.criteria_path)
                enabled_companies = list(set(t.company for t in criteria.targets if t.company))
            except Exception:
                pass
        return {
            "search_portals": ctx.settings.enabled_portal_ids(),
            "companies": enabled_companies,
            "available_companies": target_comps,
            "ttl_days": 30,
            "search_max_days": getattr(ctx.settings, 'search_max_days', 7),
            "llm_provider": getattr(ctx.settings, 'llm_provider', 'local'),
            "llm_base_url": getattr(ctx.settings, 'llm_base_url', 'http://localhost:1234/v1'),
            "llm_model": getattr(ctx.settings, 'llm_model', 'qwen2.5-7b-instruct'),
            "llm_api_key": getattr(ctx.settings, 'llm_api_key', ''),
        }

    @app.post("/api/settings")
    def update_user_settings(body: SettingsUpdate, ctx: AppState = Depends(get_state)) -> dict:
        # 1. Update config fields
        ctx.settings.search_portals = ",".join(body.search_portals)
        ctx.settings.search_max_days = body.search_max_days
        if body.llm_provider is not None:
            ctx.settings.llm_provider = body.llm_provider
        if body.llm_base_url is not None:
            ctx.settings.llm_base_url = body.llm_base_url
        if body.llm_model is not None:
            ctx.settings.llm_model = body.llm_model
        if body.llm_api_key is not None:
            ctx.settings.llm_api_key = body.llm_api_key
        
        env_file = Path(ctx.settings.model_config.get("env_file", ".env"))
        env_content = env_file.read_text(encoding='utf-8') if env_file.exists() else ""

        def set_env_var(text: str, key: str, value: str) -> str:
            pattern = rf'^{key}=.*$'
            replacement = f'{key}="{value}"'
            if re.search(pattern, text, flags=re.MULTILINE):
                return re.sub(pattern, replacement, text, flags=re.MULTILINE)
            return f'{text.rstrip()}\n{replacement}\n'

        env_content = set_env_var(env_content, "JOB_AGENT_SEARCH_PORTALS", ctx.settings.search_portals)
        env_content = set_env_var(env_content, "JOB_AGENT_SEARCH_MAX_DAYS", str(ctx.settings.search_max_days))
        env_content = set_env_var(env_content, "JOB_AGENT_LLM_PROVIDER", ctx.settings.llm_provider)
        env_content = set_env_var(env_content, "JOB_AGENT_LLM_BASE_URL", ctx.settings.llm_base_url)
        env_content = set_env_var(env_content, "JOB_AGENT_LLM_MODEL", ctx.settings.llm_model)
        env_content = set_env_var(env_content, "JOB_AGENT_LLM_API_KEY", ctx.settings.llm_api_key)

        env_file.write_text(env_content.strip() + "\n", encoding='utf-8')
        
        # 2. Update DB target companies
        ctx.repository.set_enabled_companies(body.companies)

        # 3. Update Companies in criteria.yaml
        if ctx.settings.criteria_path.exists():
            data = yaml.safe_load(ctx.settings.criteria_path.read_text(encoding='utf-8')) or {}
            new_targets = []
            for c in body.companies:
                c = c.strip()
                if not c: continue
                t = next((x for x in data.get("targets", []) if x.get("company", "").lower() == c.lower()), None)
                if t:
                    new_targets.append(t)
                else:
                    new_targets.append({"company": c, "title": "Software Engineer", "location": "Bengaluru"})
            data["targets"] = new_targets
            ctx.settings.criteria_path.write_text(yaml.dump(data, sort_keys=False), encoding='utf-8')

        # 4. TTL
        deleted = 0
        if body.ttl_days is not None and body.ttl_days > 0:
            deleted = ctx.repository.purge_jobs(body.ttl_days)
            
        import config as cfg
        cfg._settings = cfg.Settings()
        ctx.settings = cfg._settings
            
        return {"status": "ok", "deleted_jobs": deleted}

    @app.post("/api/settings/test-model")
    def test_model_endpoint(body: TestModelRequest) -> dict:
        return check_llm_connection(
            base_url=body.base_url,
            model=body.model,
            api_key=body.api_key,
            provider=body.provider,
        )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/meta")
    def meta(ctx: AppState = Depends(get_state)) -> dict:
        settings = ctx.settings
        return {
            "fit_score_threshold": settings.fit_score_threshold,
            "search_max_results": settings.search_max_results,
            "enabled_portals": settings.enabled_portal_ids(),
            "all_portals": [
                {"id": portal_id, "name": portal_display_name(portal_id)}
                for portal_id in list_portal_ids()
            ],
        }

    @app.get("/api/stats")
    def stats(ctx: AppState = Depends(get_state)) -> dict[str, int]:
        return ctx.repository.get_run_stats()

    @app.get("/api/filters")
    def filters(ctx: AppState = Depends(get_state)) -> dict[str, list[str]]:
        return ctx.repository.get_filter_options()

    @app.get("/api/jobs")
    def list_jobs(
        ctx: AppState = Depends(get_state),
        company: list[str] | None = Query(None),
        portal: list[str] | None = Query(None),
        status: list[str] | None = Query(None),
        max_days: int | None = Query(None),
        location: list[str] | None = Query(None),
        min_fit: float | None = Query(None, ge=0.0, le=1.0),
        evaluated: bool | None = Query(None),
        yoe_match: bool | None = Query(None),
        q: str | None = Query(None),
        sort: str = Query("fit_score"),
    ) -> list[dict]:
        jobs = ctx.repository.list_jobs(
            companies=company,
            portals=portal,
            statuses=status,
            max_days=max_days,
            locations=location,
            min_fit=min_fit,
            evaluated=evaluated,
            yoe_match=yoe_match,
            query=q,
            sort=sort,
        )
        return [serialize_job(job) for job in jobs]

    @app.get("/api/jobs/export.csv")
    def export_csv(ctx: AppState = Depends(get_state)) -> StreamingResponse:
        jobs = ctx.repository.get_all_jobs()
        buffer = io.StringIO()
        fieldnames = [
            "id",
            "company",
            "title",
            "location",
            "fit_score",
            "status",
            "source_portal",
            "apply_url",
            "yoe_match",
            "matched_skills",
            "missing_skills",
            "summary_reason",
            "evaluated",
        ]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            payload = serialize_job(job)
            writer.writerow({
                "id": payload["id"],
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "fit_score": job.fit_score,
                "status": job.status.value,
                "source_portal": job.source_portal,
                "apply_url": job.apply_url,
                "yoe_match": job.yoe_match,
                "matched_skills": "; ".join(job.matched_skills),
                "missing_skills": "; ".join(job.missing_skills),
                "summary_reason": job.summary_reason,
                "evaluated": job.evaluated,
            })
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=jobs_export.csv"},
        )

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str, ctx: AppState = Depends(get_state)) -> dict:
        job = ctx.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return serialize_job(job)

    @app.delete("/api/jobs")
    def delete_all_jobs(ctx: AppState = Depends(get_state)) -> dict:
        try:
            with ctx.repository.db.get_connection():
                cursor = ctx.repository.db.execute("DELETE FROM jobs")
                deleted = cursor.rowcount
            return {"deleted": deleted}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.patch("/api/jobs/{job_id}/status")
    def patch_status(job_id: str, body: StatusUpdate, ctx: AppState = Depends(get_state)) -> dict:
        job = ctx.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        ctx.repository.update_status(job_id, body.status)
        updated = ctx.repository.get_job(job_id)
        assert updated is not None
        return serialize_job(updated)

    @app.post("/api/jobs/{job_id}/evaluate")
    def evaluate_single_job(job_id: str, ctx: AppState = Depends(get_state)) -> dict:
        job = ctx.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        llm_client = LLMClient(ctx.settings)
        output_guard = OutputGuard(llm_client)
        exporter = MarkdownExporter(ctx.settings.output_path)
        metrics = MetricsCollector()
        searcher = MultiPortalSearcher.from_settings(ctx.settings)

        pipeline = Pipeline(
            searcher=searcher,
            repository=ctx.repository,
            ollama_client=llm_client,
            output_guard=output_guard,
            exporter=exporter,
            metrics=metrics,
            settings=ctx.settings,
        )

        try:
            evaluated = pipeline._match_one(job)
            if evaluated is None:
                raise HTTPException(status_code=500, detail="LLM evaluation returned empty or invalid output.")
            return serialize_job(evaluated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI evaluation failed: {e}")

    @app.get("/api/runs/current")
    def current_run(ctx: AppState = Depends(get_state)) -> dict:
        return ctx.runs.snapshot()

    @app.post("/api/runs")
    def start_run(body: RunRequest, ctx: AppState = Depends(get_state)) -> dict:
        if body.mode == RunMode.MATCH:
            pending = ctx.repository.get_unevaluated_jobs()
            if not pending:
                raise HTTPException(
                    status_code=400,
                    detail="No unmatched jobs. Run Search first.",
                )
        try:
            return ctx.runs.start(body.mode, _adhoc_targets(body, ctx.settings))
        except RunInProgressError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    assets_dir = WEB_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    docs_dir = Path(__file__).resolve().parent.parent.parent / "docs"
    if docs_dir.is_dir():
        app.mount("/docs", StaticFiles(directory=docs_dir, html=True), name="docs")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = WEB_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = WEB_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(
            status_code=503,
            detail="Dashboard UI is not built. Run: cd frontend && npm install && npm run build",
        )

    return app


def _adhoc_targets(body: RunRequest, settings: Settings) -> list[SearchTarget] | None:
    if body.mode == RunMode.MATCH:
        return None
    if not (body.company or body.title or body.location):
        return None

    target_yoe: int | None = None
    core_skills: list[str] | None = None
    location = body.location or ""
    if settings.criteria_path.exists():
        try:
            criteria = parse_criteria(settings.criteria_path)
            target_yoe = criteria.global_filters.target_yoe
            core_skills = criteria.global_filters.core_skills
            if not location and criteria.global_filters.preferred_locations:
                location = criteria.global_filters.preferred_locations[0]
        except Exception:
            pass

    return [
        SearchTarget(
            company=body.company or "",
            title=body.title or "",
            location=location,
            target_yoe=target_yoe,
            core_skills=core_skills,
        )
    ]


