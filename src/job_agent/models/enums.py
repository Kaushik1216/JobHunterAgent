from enum import StrEnum

class JobStatus(StrEnum):
    NEW = "NEW"
    APPLIED = "APPLIED"
    SKIPPED = "SKIPPED"
    ARCHIVED = "ARCHIVED"

class PipelineStage(StrEnum):
    SEARCH = "SEARCH"
    DEDUP = "DEDUP"
    EVALUATE = "EVALUATE"
    FILTER = "FILTER"
    PERSIST = "PERSIST"
    EXPORT = "EXPORT"

class LogFormat(StrEnum):
    JSON = "json"
    CONSOLE = "console"
