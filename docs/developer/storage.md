# Storage Component Developer Documentation

## Overview
The `storage` module manages all persistent data for the Job Agent. It abstracts the database technology (SQLite) away from the rest of the application, providing clean CRUD (Create, Read, Update, Delete) interfaces.

## Responsibilities
- Manage database connections, sessions, and connection pooling.
- Define ORM models mapping to database tables.
- Handle database migrations and schema updates.
- Provide a Repository pattern for querying and updating job data.

## Key Files & Modules
- `database.py`: Contains the engine initialization, session factory setup, and connection management logic (often using SQLAlchemy). Configures SQLite specific settings like WAL mode.
- `repository.py`: Implements the data access layer. Exposes methods like `save_job`, `get_unprocessed_jobs`, `get_job_by_id`, encapsulating raw SQL or ORM queries.
- `migrations/`: Directory containing Alembic or similar database migration scripts to manage schema evolution.

## Architecture & Interactions
- Provides data to the `core` pipeline for deduplication (checking if a job exists).
- Saves evaluated jobs from the `core` pipeline.
- Supplies data to the `dashboard` and `export` modules for rendering and exporting.
- Uses types defined in `models` to accept and return data, keeping database specifics isolated.
