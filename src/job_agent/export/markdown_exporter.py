import structlog
from datetime import datetime
from pathlib import Path
from tabulate import tabulate
from job_agent.models.schemas import EvaluatedJob, ExecutionSummary
from job_agent.exceptions import ExportError

logger = structlog.get_logger()

class MarkdownExporter:
    """Exports qualified jobs to a formatted markdown file."""
    
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path
    
    def export_jobs(self, jobs: list[EvaluatedJob], summary: ExecutionSummary | None = None) -> None:
        """Generate jobs_output.md with qualified jobs table."""
        try:
            content = self._generate_markdown(jobs, summary)
            self._output_path.parent.mkdir(parents=True, exist_ok=True)
            self._output_path.write_text(content, encoding="utf-8")
            logger.info("exported_jobs", path=str(self._output_path), count=len(jobs))
        except Exception as e:
            raise ExportError(f"Failed to export jobs: {e}") from e
    
    def append_run(self, jobs: list[EvaluatedJob], summary: ExecutionSummary) -> None:
        """Append a new run section without overwriting previous runs."""
        try:
            new_content = self._generate_markdown(jobs, summary)
            existing_content = ""
            if self._output_path.exists():
                existing_content = self._output_path.read_text(encoding="utf-8")
            
            separator = "\n\n---\n\n" if existing_content else ""
            combined = f"{existing_content}{separator}{new_content}"
            self._output_path.write_text(combined, encoding="utf-8")
            logger.info("appended_run", path=str(self._output_path), new_jobs=len(jobs))
        except Exception as e:
            raise ExportError(f"Failed to append run: {e}") from e
    
    def regenerate_from_jobs(self, jobs: list[EvaluatedJob]) -> None:
        """Regenerate the entire output file from a list of jobs."""
        self.export_jobs(jobs)

    def _generate_markdown(self, jobs: list[EvaluatedJob], summary: ExecutionSummary | None) -> str:
        lines = []
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"# Job Discovery Report ({timestamp})\n")
        
        if summary:
            lines.append("## Run Summary")
            lines.append(f"- **Run ID:** {summary.run_id}")
            lines.append(f"- **Duration:** {summary.duration_seconds:.2f}s")
            lines.append(f"- **Targets processed:** {summary.total_targets}")
            lines.append(f"- **Jobs found:** {summary.jobs_found}")
            lines.append(f"- **Jobs qualified:** {summary.jobs_qualified}")
            lines.append(f"- **Jobs skipped (dedup):** {summary.jobs_skipped_dedup}")
            lines.append(f"- **Jobs skipped (low score):** {summary.jobs_skipped_low_score}")
            lines.append(f"- **Errors:** {summary.jobs_errored}")
            lines.append("")
        
        if not jobs:
            lines.append("No qualified jobs found in this run.")
            return "\n".join(lines)
            
        lines.append("## Qualified Jobs\n")
        
        # Sort jobs by fit score descending
        sorted_jobs = sorted(jobs, key=lambda j: j.fit_score, reverse=True)
        
        table_data = []
        for i, job in enumerate(sorted_jobs, 1):
            yoe = f"{job.extracted_min_yoe}-{job.extracted_max_yoe}" if job.extracted_min_yoe is not None else "N/A"
            skills = ", ".join(job.matched_skills[:3]) + ("..." if len(job.matched_skills) > 3 else "")
            apply_link = f"[Apply]({job.apply_url})"
            table_data.append([
                i, job.company, job.title, job.location, job.source_portal, yoe,
                f"{job.fit_score:.2f}", skills, job.status.value, apply_link
            ])
            
        headers = ["#", "Company", "Title", "Location", "Portal", "YoE", "Fit", "Matched Skills", "Status", "Link"]
        lines.append(tabulate(table_data, headers=headers, tablefmt="github"))
        lines.append("\n## Job Details\n")
        
        for i, job in enumerate(sorted_jobs, 1):
            lines.append(f"### {i}. {job.title} @ {job.company}")
            lines.append(f"- **Location:** {job.location}")
            lines.append(f"- **Fit Score:** {job.fit_score:.2f}")
            lines.append(f"- **Matched Skills:** {', '.join(job.matched_skills) if job.matched_skills else 'None'}")
            lines.append(f"- **Missing Skills:** {', '.join(job.missing_skills) if job.missing_skills else 'None'}")
            lines.append(f"- **Reason:** {job.summary_reason}")
            lines.append(f"- **Portal:** {job.source_portal}")
            lines.append(f"- **Apply:** [Link]({job.apply_url})\n")
            
        return "\n".join(lines)
