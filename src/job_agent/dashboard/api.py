from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yaml


from job_agent.config import Settings, get_settings
from job_agent.core.criteria_parser import parse_criteria
from job_agent.dashboard.run_manager import RunInProgressError, RunManager
from job_agent.dashboard.serializers import serialize_job
from job_agent.models.enums import JobStatus, RunMode
from job_agent.models.schemas import SearchTarget
from job_agent.portals.registry import list_portal_ids, portal_display_name
from job_agent.storage.database import DatabaseManager
from job_agent.storage.repository import JobRepository

WEB_DIR = Path(__file__).parent / "web"



class SettingsUpdate(BaseModel):
    search_portals: list[str]
    companies: list[str]
    ttl_days: int | None = None
    search_max_days: int = 7

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


    @app.get("/api/settings")
    def get_user_settings(ctx: AppState = Depends(get_state)) -> dict:
        companies = []
        if ctx.settings.criteria_path.exists():
            try:
                criteria = parse_criteria(ctx.settings.criteria_path)
                companies = list(set(t.company for t in criteria.targets if t.company))
            except Exception:
                pass
        return {
            "search_portals": ctx.settings.enabled_portal_ids(),
            "companies": companies,
            "ttl_days": 30,
            "search_max_days": getattr(ctx.settings, 'search_max_days', 7)
        }

    @app.post("/api/settings")
    def update_user_settings(body: SettingsUpdate, ctx: AppState = Depends(get_state)) -> dict:
        # 1. Update config fields
        ctx.settings.search_portals = ",".join(body.search_portals)
        ctx.settings.search_max_days = body.search_max_days
        
        env_file = Path(ctx.settings.model_config.get("env_file", ".env"))
        if env_file.exists():
            env_content = env_file.read_text(encoding='utf-8')
            
            # Update portals
            if "JOB_AGENT_SEARCH_PORTALS" in env_content:
                env_content = re.sub(r'JOB_AGENT_SEARCH_PORTALS=.*', f'JOB_AGENT_SEARCH_PORTALS="{ctx.settings.search_portals}"', env_content)
            else:
                env_content += f'\nJOB_AGENT_SEARCH_PORTALS="{ctx.settings.search_portals}"'
                
            # Update max days
            if "JOB_AGENT_SEARCH_MAX_DAYS" in env_content:
                env_content = re.sub(r'JOB_AGENT_SEARCH_MAX_DAYS=.*', f'JOB_AGENT_SEARCH_MAX_DAYS={ctx.settings.search_max_days}', env_content)
            else:
                env_content += f'\nJOB_AGENT_SEARCH_MAX_DAYS={ctx.settings.search_max_days}'
                
            env_file.write_text(env_content, encoding='utf-8')
        else:
            env_file.write_text(f'JOB_AGENT_SEARCH_PORTALS="{ctx.settings.search_portals}"\nJOB_AGENT_SEARCH_MAX_DAYS={ctx.settings.search_max_days}', encoding='utf-8')
        
        # 2. Companies
        if ctx.settings.criteria_path.exists():
            data = yaml.safe_load(ctx.settings.criteria_path.read_text(encoding='utf-8')) or {}
            new_targets = []
            for c in body.companies:
                c = c.strip()
                if not c: continue
                t = next((x for x in data.get("targets", []) if x.get("company") == c), None)
                if t:
                    new_targets.append(t)
                else:
                    new_targets.append({"company": c, "title": "Software Engineer", "location": "Remote"})
            data["targets"] = new_targets
            ctx.settings.criteria_path.write_text(yaml.dump(data, sort_keys=False), encoding='utf-8')

        # 3. TTL
        deleted = 0
        if body.ttl_days is not None and body.ttl_days > 0:
            deleted = ctx.repository.purge_jobs(body.ttl_days)
            
        return {"status": "ok", "deleted_jobs": deleted}

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


