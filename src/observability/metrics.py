import structlog
import statistics
from dataclasses import dataclass, field
from typing import Any

logger = structlog.get_logger()

@dataclass
class MetricsCollector:
    """Collects and reports pipeline execution metrics."""
    jobs_found: int = 0
    jobs_qualified: int = 0
    jobs_skipped_dedup: int = 0
    jobs_skipped_low_score: int = 0
    jobs_errored: int = 0
    search_latencies: list[float] = field(default_factory=list)
    inference_latencies: list[float] = field(default_factory=list)
    
    def record_search_latency(self, latency: float) -> None:
        self.search_latencies.append(latency)
        
    def record_inference_latency(self, latency: float) -> None:
        self.inference_latencies.append(latency)
        
    def increment_found(self, count: int = 1) -> None:
        self.jobs_found += count
        
    def increment_qualified(self, count: int = 1) -> None:
        self.jobs_qualified += count
        
    def increment_skipped_dedup(self, count: int = 1) -> None:
        self.jobs_skipped_dedup += count
        
    def increment_skipped_low_score(self, count: int = 1) -> None:
        self.jobs_skipped_low_score += count
        
    def increment_errored(self, count: int = 1) -> None:
        self.jobs_errored += count
        
    def _calc_percentile(self, data: list[float], q: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (q / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def _calc_mean(self, data: list[float]) -> float:
        if not data:
            return 0.0
        return statistics.mean(data)
        
    def to_dict(self) -> dict[str, Any]:
        return {
            "jobs_found": self.jobs_found,
            "jobs_qualified": self.jobs_qualified,
            "jobs_skipped_dedup": self.jobs_skipped_dedup,
            "jobs_skipped_low_score": self.jobs_skipped_low_score,
            "jobs_errored": self.jobs_errored,
            "avg_inference_latency_ms": self._calc_mean(self.inference_latencies),
            "avg_search_latency_ms": self._calc_mean(self.search_latencies),
            "p50_search_latency": self._calc_percentile(self.search_latencies, 50),
            "p95_search_latency": self._calc_percentile(self.search_latencies, 95),
            "p50_inference_latency": self._calc_percentile(self.inference_latencies, 50),
            "p95_inference_latency": self._calc_percentile(self.inference_latencies, 95)
        }
        
    def log_summary(self) -> None:
        metrics = self.to_dict()
        logger.info("pipeline_metrics", **metrics)
