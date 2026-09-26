# Models Component Developer Documentation

## Overview
The `models` module contains the central data definitions, schemas, and enumerations used across the entire Job Agent application. It ensures type safety and consistent data structures.

## Responsibilities
- Define Pydantic models for data validation and serialization.
- Define enumerations for standardizing fields like job status, portal types, etc.
- Provide a single source of truth for the shape of the data moving between components.

## Key Files & Modules
- `schemas.py`: Contains Pydantic models such as `Job`, `JobEvaluation`, `SearchCriteria`, etc., which are used for data validation, API requests/responses, and internal message passing.
- `enums.py`: Contains Python `Enum` classes representing discrete states or types (e.g., `JobStatus`, `EvaluationResult`).

## Architecture & Interactions
- Used universally across `core`, `dashboard`, `inference`, `portals`, and `storage`.
- Does *not* contain database logic (which is isolated in `storage`). Pydantic models here are often converted to/from SQLAlchemy models in the repository layer.
