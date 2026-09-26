# Portals Component Developer Documentation

## Overview
The `portals` module is responsible for integrating with external job boards and Applicant Tracking Systems (ATS). It standardizes the extraction of job listings across various platforms.

## Responsibilities
- Scrape or API-fetch job listings from sources like LinkedIn, Indeed, etc.
- Normalize raw job data from different platforms into a unified `models.Job` schema.
- Manage rate limits, pagination, and platform-specific authentication or headers.

## Key Files & Modules
- `base.py`: Defines the abstract base classes and interfaces (e.g., `BasePortal`) that all concrete portal implementations must inherit from.
- `registry.py`: Implements a factory or registry pattern to dynamically load and instantiate specific portal adapters based on configuration.
- `boards.py`: Contains implementations for major job boards (e.g., LinkedIn, Glassdoor).
- `ats.py`: Contains implementations for common ATS platforms (e.g., Greenhouse, Lever) if specific scraping logic is required.
- `composite.py`: Allows aggregating searches across multiple portals simultaneously.

## Architecture & Interactions
- Called by the `core` pipeline during the "Search" phase.
- Returns normalized data using structures defined in the `models` module.
- Handles external network requests independently of the evaluation logic.
