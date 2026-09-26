# Core Component Developer Documentation

## Overview
The `core` module is the heart of the Job Agent system. It orchestrates the entire job processing pipeline, bringing together the search, evaluation, and persistence logic into a cohesive workflow.

## Responsibilities
- Define and execute the end-to-end job processing pipeline.
- Coordinate interactions between different sub-components (portals, inference, storage).
- Parse job descriptions and user criteria to ensure they are properly formatted before evaluation.
- Act as the entry point for CLI runners and scheduled tasks.

## Key Files & Modules
- `pipeline.py`: Defines the main `Pipeline` class which orchestrates the Search -> Deduplicate -> Evaluate -> Filter -> Persist workflow.
- `runner.py`: Provides execution context and manages the lifecycle of pipeline runs, handling exceptions and retries.
- `jd_parser.py`: Contains logic to clean, normalize, and extract relevant sections from raw job descriptions.
- `criteria_parser.py`: Responsible for loading and validating user job-seeking criteria (e.g., from `criteria.yaml`).

## Architecture & Interactions
- **Inputs**: Reads raw jobs via the `portals` module and criteria from user configurations.
- **Processing**: Passes data to the `inference` module for SLM evaluation.
- **Outputs**: Writes matched and evaluated jobs to the `storage` module.
- **Integration**: The pipeline is triggered by `dashboard/run_manager.py` or the CLI.
