import time
import structlog
from job_agent.models.enums import JobStatus, PipelineStage, RunMode
from job_agent.models.schemas import SearchTarget, RawJobResult, EvaluatedJob
from job_agent.observability.metrics import MetricsCollector
from job_agent.inference.prompts import build_extraction_prompt, EXTRACTION_SYSTEM_PROMPT, get_extraction_schema
from job_agent.portals.base import JobSearcher

logger = structlog.get_logger()

class Pipeline:
    """Coordinates the job discovery pipeline stages."""
    
    def __init__(self, searcher: JobSearcher, repository, ollama_client, output_guard, exporter, metrics: MetricsCollector, settings):
        self.searcher = searcher
        self.repository = repository
        self.ollama_client = ollama_client
        self.output_guard = output_guard
        self.exporter = exporter
        self.metrics = metrics
        self.settings = settings
    
    def process_target(self, target: SearchTarget, mode: RunMode = RunMode.SEARCH_AND_MATCH) -> list[EvaluatedJob]:
        """Search and optionally evaluate a single target."""
        logger.info("processing_target", target=target.model_dump(), mode=mode.value)
        if mode == RunMode.MATCH:
            return self.match_unevaluated()

        discovered = self.discover_target(target)
        if mode == RunMode.SEARCH:
            return []
        return self._match_jobs(discovered)
    
    def discover_target(self, target: SearchTarget) -> list[EvaluatedJob]:
        raw_results = self._search(target)
        if not raw_results:
            return []
        new_results = self._dedup(raw_results)
        discovered: list[EvaluatedJob] = []
        for result in new_results:
            job = EvaluatedJob.from_discovery(result, target)
            self.repository.save_job(job)
            discovered.append(job)
        return discovered

    def match_unevaluated(self) -> list[EvaluatedJob]:
        pending = self.repository.get_unevaluated_jobs()
        logger.info("matching_unevaluated", count=len(pending))
        return self._match_jobs(pending)

    def _match_jobs(self, jobs: list[EvaluatedJob]) -> list[EvaluatedJob]:
        qualified_jobs: list[EvaluatedJob] = []
        for job in jobs:
            try:
                evaluated = self._match_one(job)
                if evaluated is None:
                    self.metrics.increment_errored()
                    continue
                if evaluated.status == JobStatus.NEW:
                    qualified_jobs.append(evaluated)
                    self.metrics.increment_qualified()
                else:
                    self.metrics.increment_skipped_low_score()
            except Exception as e:
                logger.error("evaluation_failed", result=job.title, error=str(e))
                self.metrics.increment_errored()
        return qualified_jobs

    def _match_one(self, job: EvaluatedJob) -> EvaluatedJob | None:
        target = SearchTarget(
            company=job.company,
            title=job.search_title or job.title,
            location=job.location,
            target_yoe=job.target_yoe,
            core_skills=job.core_skills or None,
        )
        raw = RawJobResult(
            title=job.title,
            url=job.apply_url,
            snippet=job.raw_snippet,
            source_query=job.source_query,
            source_portal=job.source_portal,
        )
        evaluated = self._evaluate(raw, target)
        if evaluated is None:
            return None
        passed = self._filter(evaluated)
        merged = evaluated.model_copy(update={
            "evaluated": True,
            "search_title": job.search_title,
            "target_yoe": job.target_yoe,
            "core_skills": job.core_skills,
            "status": JobStatus.NEW if passed else JobStatus.SKIPPED,
            "apply_url": job.apply_url,
            "source_query": job.source_query or evaluated.source_query,
            "source_portal": job.source_portal or evaluated.source_portal,
            "raw_snippet": job.raw_snippet or evaluated.raw_snippet,
        })
        self.repository.update_job(merged)
        return merged
    
    def _search(self, target: SearchTarget) -> list[RawJobResult]:
        logger.debug("stage_transition", stage=PipelineStage.SEARCH.value)
        start_time = time.time()
        try:
            results = self.searcher.search(
                company=target.company,
                title=target.title,
                location=target.location,
                max_results=self.settings.search_max_results,
            )
            self.metrics.record_search_latency((time.time() - start_time) * 1000)
            self.metrics.increment_found(len(results))
            return results
        except Exception as e:
            logger.error("search_failed", error=str(e))
            self.metrics.increment_errored()
            return []

    def _dedup(self, results: list[RawJobResult]) -> list[RawJobResult]:
        logger.debug("stage_transition", stage=PipelineStage.DEDUP.value)
        import hashlib
        new_results = []
        for result in results:
            url_hash = hashlib.sha256(str(result.url).encode("utf-8")).hexdigest()
            if not self.repository.job_exists(url_hash):
                new_results.append(result)
            else:
                self.metrics.increment_skipped_dedup()
        return new_results

    def _evaluate(self, result: RawJobResult, target: SearchTarget) -> EvaluatedJob | None:
        logger.debug("stage_transition", stage=PipelineStage.EVALUATE.value)
        start_time = time.time()
        
        schema = get_extraction_schema()
        system_prompt = EXTRACTION_SYSTEM_PROMPT.format(schema=schema)

        company_for_prompt = target.company if target.company else "Extract from snippet"

        prompt = build_extraction_prompt(
            snippet=result.snippet,
            company=company_for_prompt,
            title=target.title,
            location=target.location,
            target_yoe=target.target_yoe or 0,
            core_skills=target.core_skills or [],
        )
        response_text = self.ollama_client.generate(prompt=prompt, system_prompt=system_prompt)
        
        self.metrics.record_inference_latency((time.time() - start_time) * 1000)
        
        job = self.output_guard.validate_and_parse(
            raw_output=response_text,
            apply_url=str(result.url),
            source_query=result.source_query,
            raw_snippet=result.snippet,
            source_portal=result.source_portal,
        )
        return job

    def _filter(self, job: EvaluatedJob) -> bool:
        logger.debug("stage_transition", stage=PipelineStage.FILTER.value)
        if job.fit_score < self.settings.fit_score_threshold:
            return False
        return True
