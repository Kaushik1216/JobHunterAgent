import structlog
import logging
from job_agent.config import Settings

def setup_logging(settings: Settings) -> None:
    """Configure structlog with JSON or console renderer based on settings."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    import sys
    logging.basicConfig(format="%(message)s", level=log_level, stream=sys.stdout, force=True)
