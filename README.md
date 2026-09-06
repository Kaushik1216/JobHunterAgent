# LinkedIn Job Agent

An Autonomous LinkedIn Job Discovery Agent that searches, deduplicates, and evaluates job postings using an Ollama SLM (Small Language Model).

## Features

- **Automated Searching:** Fetches jobs from LinkedIn.
- **SLM Evaluation:** Uses local Ollama models to evaluate job descriptions against a user profile.
- **Streamlit Dashboard:** Interactive UI for viewing, filtering, and managing jobs.
- **SQLite Storage:** Persistent storage using SQLite with WAL mode for performance.
- **MCP Server:** Exposes Model Context Protocol capabilities.

## Quickstart

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Ollama](https://ollama.ai/) installed and running locally

### Installation

Clone the repository and install the package in development mode:

```bash
git clone <your-repo>
cd linkedin-job-agent
uv pip install -e ".[dev]"
# or using pip: pip install -e ".[dev]"
```

### Configuration

Create a `.env` file in the root directory based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` to configure your database path, Ollama model, and other settings.

## Usage

### CLI

Run the main job discovery pipeline:

```bash
job-agent run
```

Launch the Streamlit dashboard:

```bash
job-agent dashboard
```

### MCP Server

Start the Model Context Protocol server:

```bash
job-agent mcp
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](docs/CONTRIBUTING.md)
