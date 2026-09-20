# Job Agent

An autonomous job discovery agent that searches multiple job boards and company career sites, deduplicates listings, and evaluates fit with a local SLM (LM Studio or Ollama).

LinkedIn remains a first-class source. Indeed, Naukri, Glassdoor, Wellfound, and ATS sites (Greenhouse, Lever, Ashby) are enabled through the same `JobPortal` interface so additional portals can be added without changing the pipeline.

## Features

- **Multi-portal search:** LinkedIn plus other boards and company ATS sites, selected via config.
- **Expandable portals:** Each source is a class that inherits `JobPortal` (or `BoardJobPortal` / `AtsJobPortal`).
- **SLM evaluation:** Uses a local model to score postings against your profile.
- **Streamlit dashboard:** Filter and manage qualified jobs, with apply links labeled by portal.
- **SQLite storage:** Persistent vault with WAL mode.
- **MCP server:** Tools for listing portals and searching jobs.

## Quickstart

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Ollama](https://ollama.ai/) or LM Studio running locally

### Installation

```bash
git clone <your-repo>
cd jobagent
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` for the LLM, database path, and which portals to query:

```bash
JOB_AGENT_SEARCH_PORTALS=linkedin,indeed,naukri,greenhouse,lever
```

Available portal ids: `linkedin`, `indeed`, `naukri`, `glassdoor`, `wellfound`, `greenhouse`, `lever`, `ashby`.

## Usage

```bash
job-agent run
job-agent dashboard
job-agent mcp
```

## Job portal architecture

Search is no longer hard-coded to LinkedIn. The pipeline talks only to a `JobSearcher` (`search(...)` → `list[RawJobResult]`). `MultiPortalSearcher` fans that call out to every enabled portal.

```
JobPortal (ABC)
├── WebSearchJobPortal     # DuckDuckGo + jitter + circuit breaker
│   ├── BoardJobPortal     # public job boards
│   │   ├── LinkedInPortal
│   │   ├── IndeedPortal
│   │   ├── NaukriPortal
│   │   ├── GlassdoorPortal
│   │   └── WellfoundPortal
│   └── AtsJobPortal       # company career / ATS sites
│       ├── GreenhousePortal
│       ├── LeverPortal
│       └── AshbyPortal
└── (your API-backed portal)  # implement search() yourself
```

Registration lives in `src/job_agent/portals/registry.py`. The runner builds `MultiPortalSearcher.from_settings(settings)` so the rest of the app does not import portal classes.

## Adding a new job portal

1. **Pick a base class**
   - Public board with a `site:` dork → subclass `BoardJobPortal` in `src/job_agent/portals/boards.py` (or a new module).
   - Company ATS / careers page → subclass `AtsJobPortal` in `src/job_agent/portals/ats.py`.
   - Official HTTP API → subclass `JobPortal` and implement `search()` (skip DuckDuckGo).

2. **Set class attributes and, if needed, override `build_query`**

```python
from typing import ClassVar
from job_agent.portals.base import BoardJobPortal

class ExamplePortal(BoardJobPortal):
    portal_id: ClassVar[str] = "example"
    display_name: ClassVar[str] = "Example Jobs"
    site_filter: ClassVar[str] = "site:jobs.example.com"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ("example.com",)
```

`url_host_suffixes` drops off-site DuckDuckGo noise. Results are tagged with `source_portal=portal_id`.

3. **Register it** in `PORTAL_REGISTRY` inside `src/job_agent/portals/registry.py`.

4. **Enable it** with `JOB_AGENT_SEARCH_PORTALS=...,example`.

5. **Add a unit test** for `build_query` / `accepts_url` in `tests/unit/test_search.py`.

You should not need to change `Pipeline`, the CLI, or storage for a standard DuckDuckGo-backed portal.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](docs/CONTRIBUTING.md)
