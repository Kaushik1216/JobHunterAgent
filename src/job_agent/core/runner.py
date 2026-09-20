import uuid
import time
import structlog
from datetime import datetime
from job_agent.config import get_settings, Settings
from job_agent.core.criteria_parser import parse_criteria
from job_agent.core.jd_parser import parse_jd, jd_to_search_targets
from job_agent.core.pipeline import Pipeline
from job_agent.storage.database import DatabaseManager
from job_agent.storage.repository import JobRepository
from job_agent.portals.composite import MultiPortalSearcher
from job_agent.inference.client import LLMClient, OllamaClient
from job_agent.inference.output_guard import OutputGuard
from job_agent.export.markdown_exporter import MarkdownExporter
from job_agent.observability.logging import setup_logging
from job_agent.observability.metrics import MetricsCollector
from job_agent.models.enums import RunMode
from job_agent.models.schemas import ExecutionSummary, EvaluatedJob, SearchTarget
from job_agent.exceptions import JobAgentError

logger = structlog.get_logger()

class AgentRunner:
    """Main orchestration engine for the job discovery agent."""
    
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._run_id = str(uuid.uuid4())[:8]
    
    def _resolve_targets(self, targets: list[SearchTarget] | None) -> tuple[list[SearchTarget], str]:
        if targets is not None:
            return targets, f"dashboard ({len(targets)} targets)"
        if self._settings.jd_path.exists():
            jd = parse_jd(self._settings.jd_path)
            resolved = jd_to_search_targets(jd)
            source = f"job_description.txt ({jd.role} @ {jd.location})"
            logger.info("using_jd_file", path=str(self._settings.jd_path), role=jd.role, location=jd.location)
            return resolved, source
        criteria = parse_criteria(self._settings.criteria_path)
        resolved = criteria.resolve_targets()
        source = f"criteria.yaml ({len(resolved)} targets)"
        logger.info("using_criteria_yaml", path=str(self._settings.criteria_path), target_count=len(resolved))
        return resolved, source

    def run(
        self,
        mode: RunMode = RunMode.SEARCH_AND_MATCH,
        targets: list[SearchTarget] | None = None,
    ) -> ExecutionSummary:
        """Execute search, match, or the full discovery pipeline."""
        setup_logging(self._settings)
        logger.info("starting_run", run_id=self._run_id, mode=mode.value)
        
        db = DatabaseManager(self._settings.db_path)
        db.connect()
        db.run_migrations()
        repo = JobRepository(db)
        
        searcher = MultiPortalSearcher.from_settings(self._settings)
        llm_client = LLMClient(self._settings)
        guard = OutputGuard(llm_client)
        exporter = MarkdownExporter(self._settings.output_path)
        metrics = MetricsCollector()

        resolved_targets: list[SearchTarget] = []
        if mode != RunMode.MATCH:
            resolved_targets, _input_source = self._resolve_targets(targets)
        
        pipeline = Pipeline(
            searcher=searcher,
            repository=repo,
            ollama_client=llm_client,
            output_guard=guard,
            exporter=exporter,
            metrics=metrics,
            settings=self._settings
        )
        
        start_time = datetime.now()
        
        all_qualified: list[EvaluatedJob] = []
        jobs_discovered = 0
        if mode == RunMode.MATCH:
            all_qualified = pipeline.match_unevaluated()
        else:
            for target in resolved_targets:
                if mode == RunMode.SEARCH:
                    discovered = pipeline.discover_target(target)
                    jobs_discovered += len(discovered)
                else:
                    qualified = pipeline.process_target(target, mode=mode)
                    all_qualified.extend(qualified)
            
        summary = ExecutionSummary(
            run_id=self._run_id,
            started_at=start_time,
            completed_at=datetime.now(),
            total_targets=len(resolved_targets),
            jobs_found=metrics.jobs_found,
            jobs_qualified=metrics.jobs_qualified,
            jobs_skipped_dedup=metrics.jobs_skipped_dedup,
            jobs_skipped_low_score=metrics.jobs_skipped_low_score,
            jobs_errored=metrics.jobs_errored,
            avg_inference_latency_ms=metrics.to_dict()["avg_inference_latency_ms"],
            avg_search_latency_ms=metrics.to_dict()["avg_search_latency_ms"],
            mode=mode.value,
            jobs_discovered=jobs_discovered if mode == RunMode.SEARCH else metrics.jobs_found,
        )
        
        if all_qualified:
            exporter.export_jobs(all_qualified, summary)
            
        metrics.log_summary()
        logger.info("run_complete", summary=summary.model_dump())
        db.close()
        return summary
    
    def validate(self) -> bool:
        """Validate configuration and criteria without running."""
        setup_logging(self._settings)
        logger.info("validating_configuration")
        try:
            criteria = parse_criteria(self._settings.criteria_path)
            targets = criteria.resolve_targets()
            logger.info("criteria_valid", target_count=len(targets))

            llm_client = LLMClient(self._settings)
            try:
                llm_ok = llm_client.health_check()
                logger.info("llm_health", reachable=llm_ok, provider=llm_client.provider, model=llm_client.model)
            except Exception as e:
                logger.warning("llm_unreachable", error=str(e), provider=llm_client.provider)
                llm_ok = False
            finally:
                llm_client.close()

            return len(targets) > 0 and llm_ok
        except JobAgentError as e:
            logger.error("validation_failed", error=str(e))
            return False
    
    def export_only(self) -> None:
        """Re-export from database without searching."""
        db = DatabaseManager(self._settings.db_path)
        db.connect()
        db.run_migrations()
        repo = JobRepository(db)
        exporter = MarkdownExporter(self._settings.output_path)
        
        jobs = repo.get_all_jobs()
        exporter.regenerate_from_jobs(jobs)
        db.close()
    
    def show_stats(self) -> dict:
        """Show database statistics."""
        db = DatabaseManager(self._settings.db_path)
        db.connect()
        db.run_migrations()
        repo = JobRepository(db)
        stats = repo.get_run_stats()
        db.close()
        return stats
