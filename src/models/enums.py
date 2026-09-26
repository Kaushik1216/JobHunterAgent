from enum import StrEnum

class JobStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    NEW = "NEW"
    APPLIED = "APPLIED"
    SKIPPED = "SKIPPED"
    ARCHIVED = "ARCHIVED"


class RunMode(StrEnum):
    SEARCH = "search"
    SEARCH_AND_MATCH = "search_and_match"
    MATCH = "match"

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
