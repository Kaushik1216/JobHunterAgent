# Contributing

We welcome contributions! Please follow these guidelines to set up your development environment and submit changes.

## Developer Setup

1. Fork and clone the repository.
2. Install the project with development dependencies using `uv` or `pip`:

```bash
uv pip install -e ".[dev]"
```

3. Set up pre-commit hooks:

```bash
pre-commit install
```

## Testing

We use `pytest` for testing. To run the test suite:

```bash
pytest tests/
```

To run tests with coverage:

```bash
pytest tests/ --cov=job_agent
```

## Code Style

This project uses [Ruff](https://astral.sh/ruff) for fast linting and formatting, and `mypy` for static type checking.

Run the linters:

```bash
ruff check .
ruff format .
mypy src/
```

These tools are also configured to run automatically via `pre-commit`.

## Pull Request Process

1. Create a new branch for your feature or bugfix (`git checkout -b feature/your-feature-name`).
2. Make your changes and ensure all tests and linters pass.
3. Commit your changes with clear, descriptive commit messages.
4. Push your branch and open a Pull Request against the `main` branch.
5. A maintainer will review your PR and may request changes before merging.
