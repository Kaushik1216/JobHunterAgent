# Export Component Developer Documentation

## Overview
The `export` module is responsible for extracting evaluated job data from the system and formatting it into user-friendly, portable formats (such as Markdown).

## Responsibilities
- Query matched jobs from the storage layer.
- Format job details, evaluations, and scores into structured output files.
- Provide customizable templates or structures for the exported data.

## Key Files & Modules
- `markdown_exporter.py`: Handles the generation of markdown files (e.g., `jobs_output.md`) summarizing the best job matches, their scores, and the AI's reasoning.

## Architecture & Interactions
- Plugs into the end of the `core` pipeline as an optional final step.
- Reads from the `storage` module.
- Generates file artifacts in the project root or a designated export directory.
