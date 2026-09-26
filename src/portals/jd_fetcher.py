from __future__ import annotations

import concurrent.futures
import html
import json
import re
from typing import Any
import httpx
import structlog

from models.schemas import RawJobResult

logger = structlog.get_logger(__name__)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

EXPIRED_INDICATORS = [
    "expired_jd_redirect",
    "trk=expired",
    "no longer accepting applications",
    "this job is no longer available",
    "this job has expired",
    "the job you're looking for is no longer available",
    "job posting has closed",
]


def clean_html_to_text(raw_html: str) -> str:
    """Converts HTML markup into clean, formatted readable text."""
    if not raw_html:
        return ""

    # First unescape HTML entities (&lt; -> <, &gt; -> >)
    text = html.unescape(raw_html)

    # Remove script and style elements entirely
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)

    # Convert block elements to newlines
    text = re.sub(
        r"<(?:br|br\s*/|/p|/li|/div|/h\d|/tr)[^>]*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # Convert bullet points
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Final unescape pass for any double-escaped text
    text = html.unescape(text)

    # Clean whitespace per line and join
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned


def fetch_job_description(url: str, fallback_snippet: str = "") -> tuple[str, bool]:
    """
    Fetch the web page for a job posting and extract the full description.

    Returns:
        (description: str, is_expired: bool)
    """
    if not url or not url.startswith("http"):
        return fallback_snippet, False

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=8.0,
            headers=BROWSER_HEADERS,
        ) as client:
            resp = client.get(url)
            final_url = str(resp.url).lower()

            # Check URL redirect patterns indicating expiration
            if "expired_jd_redirect" in final_url or "trk=expired" in final_url:
                logger.debug("job expired via redirect", url=url, final_url=final_url)
                return fallback_snippet, True

            # Detect portal redirects away from the single job view page (LinkedIn/Indeed redirect to search when closed)
            if "/jobs/view/" in url and "/jobs/view/" not in final_url:
                logger.info("job expired via redirect away from view", original_url=url, final_url=final_url)
                return fallback_snippet, True

            if "/viewjob" in url and "/viewjob" not in final_url and "jk=" not in final_url:
                logger.info("indeed job expired via redirect", original_url=url, final_url=final_url)
                return fallback_snippet, True

            if resp.status_code in (404, 410):
                logger.debug("job page not found", url=url, status=resp.status_code)
                return fallback_snippet, True

            if resp.status_code != 200:
                logger.debug("job page non-200", url=url, status=resp.status_code)
                return fallback_snippet, False

            page_html = resp.text
            page_lower = page_html.lower()

            # Check textual expiration indicators in page
            for indicator in EXPIRED_INDICATORS:
                if indicator in page_lower:
                    logger.debug("job expired via page content", url=url, indicator=indicator)
                    return fallback_snippet, True

            # 1. Check for JSON-LD schema (JobPosting)
            json_ld_matches = re.findall(
                r'<script type="application/ld\+json"[^>]*>([\s\S]*?)</script>',
                page_html,
                flags=re.IGNORECASE,
            )
            for jld_str in json_ld_matches:
                try:
                    data = json.loads(jld_str)
                    candidates: list[dict[str, Any]] = []
                    if isinstance(data, dict):
                        candidates.append(data)
                    elif isinstance(data, list):
                        candidates.extend([d for d in data if isinstance(d, dict)])

                    for cand in candidates:
                        if cand.get("@type") == "JobPosting":
                            desc = cand.get("description", "")
                            if desc and len(desc) > 150:
                                return clean_html_to_text(desc), False
                except Exception:
                    pass

            # 2. LinkedIn specific container
            li_match = re.search(
                r'<div class="show-more-less-html__markup[^>]*>([\s\S]*?)</div>',
                page_html,
            )
            if li_match:
                extracted = clean_html_to_text(li_match.group(1))
                if len(extracted) > 50:
                    return extracted, False

            # 3. Indeed container
            indeed_match = re.search(
                r'<div id="jobDescriptionText"[^>]*>([\s\S]*?)</div>',
                page_html,
            )
            if indeed_match:
                extracted = clean_html_to_text(indeed_match.group(1))
                if len(extracted) > 50:
                    return extracted, False

            # 4. Generic containers
            generic_patterns = [
                r'<div class="[^"]*(?:job-description|description__text|job_description)[^"]*">([\s\S]*?)</div>',
                r'<section class="[^"]*description[^"]*">([\s\S]*?)</section>',
            ]
            for pattern in generic_patterns:
                match = re.search(pattern, page_html, re.IGNORECASE)
                if match:
                    extracted = clean_html_to_text(match.group(1))
                    if len(extracted) > 50:
                        return extracted, False

            # 5. Meta description fallback if longer than search snippet
            meta_match = re.search(
                r'<meta\s+(?:property="og:description"|name="description")\s+content="([^"]+)"',
                page_html,
                re.IGNORECASE,
            )
            if meta_match:
                meta_text = html.unescape(meta_match.group(1)).strip()
                if len(meta_text) > len(fallback_snippet):
                    return meta_text, False

            return fallback_snippet, False

    except Exception as exc:
        logger.debug("job fetch failed, falling back to snippet", url=url, error=str(exc))
        return fallback_snippet, False


def enrich_jobs_concurrently(
    jobs: list[RawJobResult],
    max_workers: int = 5,
) -> list[RawJobResult]:
    """
    Concurrently fetch full job descriptions and filter out expired jobs.

    Returns:
        List of active RawJobResults with enriched snippets.
    """
    if not jobs:
        return []

    active_jobs: list[RawJobResult] = []
    expired_count = 0
    enriched_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {
            executor.submit(fetch_job_description, str(job.url), job.snippet): job
            for job in jobs
        }

        for future in concurrent.futures.as_completed(future_to_job):
            job = future_to_job[future]
            try:
                full_desc, is_expired = future.result()
                if is_expired:
                    expired_count += 1
                    logger.info("filtered out expired job", title=job.title, url=str(job.url))
                    continue

                if full_desc and len(full_desc) > len(job.snippet):
                    job.snippet = full_desc
                    enriched_count += 1

                active_jobs.append(job)
            except Exception as exc:
                logger.warning("enrichment error for job", url=str(job.url), error=str(exc))
                active_jobs.append(job)

    logger.info(
        "job enrichment completed",
        total_candidates=len(jobs),
        active_retained=len(active_jobs),
        enriched_count=enriched_count,
        expired_dropped=expired_count,
    )
    return active_jobs
