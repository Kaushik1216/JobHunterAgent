# Dashboard Component Developer Documentation

## Overview
The `dashboard` module provides the user interface and API layer for the Job Agent. It allows users to visualize matched jobs, manage pipeline runs, and interact with the system without using the CLI.

## Responsibilities
- Serve the Streamlit-based web dashboard.
- Expose REST APIs for interacting with the core pipeline and storage layer (if applicable).
- Manage pipeline execution states and background runs.
- Serialize and deserialize data between the backend storage and frontend components.

## Key Files & Modules
- `api.py`: Contains API endpoints and routing logic for the backend if acting as a server, exposing job data and pipeline triggers.
- `run_manager.py`: Manages asynchronous or background execution of the core pipeline, tracking status (running, completed, failed).
- `serializers.py`: Provides data transformation functions to convert internal models (e.g., from `models/schemas.py`) into API responses or UI-friendly formats.
- `web/`: Directory containing the Streamlit frontend application code, UI components, and pages.

## Architecture & Interactions
- Reads data directly from the SQLite database via the `storage` module.
- Uses `run_manager.py` to trigger the `core` pipeline.
- Integrates with Streamlit to render data in the browser.
