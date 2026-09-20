import time
import structlog
from job_agent.models.enums import PipelineStage, JobStatus
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
    
    def process_target(self, target: SearchTarget) -> list[EvaluatedJob]:
        """Run the full pipeline for a single search target."""
        logger.info("processing_target", target=target.model_dump())
        qualified_jobs = []
        
        # SEARCH
        raw_results = self._search(target)
        if not raw_results:
            return qualified_jobs
            
        # DEDUP
        new_results = self._dedup(raw_results)
        
        # EVALUATE
        for result in new_results:
            try:
                evaluated_job = self._evaluate(result, target)
                if evaluated_job:
                    # FILTER
                    if self._filter(evaluated_job):
                        # PERSIST
                        self._persist(evaluated_job)
                        qualified_jobs.append(evaluated_job)
                        self.metrics.increment_qualified()
                    else:
                        self.metrics.increment_skipped_low_score()
            except Exception as e:
                logger.error("evaluation_failed", result=result.title, error=str(e))
                self.metrics.increment_errored()
                
        return qualified_jobs
    
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

        # For broad searches (empty company), instruct SLM to extract company from snippet
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

    def _persist(self, job: EvaluatedJob) -> None:
        logger.debug("stage_transition", stage=PipelineStage.PERSIST.value)
        self.repository.save_job(job)
