class JobAgentError(Exception):
    """Base exception for all job agent errors."""

class ConfigurationError(JobAgentError):
    """Raised when configuration is invalid or missing."""

class CriteriaParseError(ConfigurationError):
    """Raised when criteria.yaml cannot be parsed."""

class SearchError(JobAgentError):
    """Raised when job search fails."""

class RateLimitError(SearchError):
    """Raised when search engine rate-limits requests."""

class CircuitBreakerOpenError(SearchError):
    """Raised when circuit breaker is open."""

class InferenceError(JobAgentError):
    """Raised when SLM/LLM inference fails."""

class LLMConnectionError(InferenceError):
    """Raised when local LLM server (LM Studio / Ollama) is unreachable."""

class OllamaConnectionError(LLMConnectionError):
    """Raised when Ollama server is unreachable (kept for backward compatibility)."""

class OutputValidationError(InferenceError):
    """Raised when SLM output fails schema validation."""

class StorageError(JobAgentError):
    """Raised when database operations fail."""

class MigrationError(StorageError):
    """Raised when database migration fails."""

class ExportError(JobAgentError):
    """Raised when export/reporting fails."""
