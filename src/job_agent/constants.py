DEFAULT_JITTER_MIN = 2.0
DEFAULT_JITTER_MAX = 4.0
DEFAULT_MAX_RESULTS = 5
DEFAULT_FIT_THRESHOLD = 0.70
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b-instruct"
DEFAULT_DB_PATH = "jobs_vault.db"
DEFAULT_CRITERIA_PATH = "criteria.yaml"
DEFAULT_OUTPUT_PATH = "jobs_output.md"
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_COOLDOWN = 60
MAX_INFERENCE_RETRIES = 3
INFERENCE_TIMEOUT = 30
LINKEDIN_DORK_TEMPLATE = 'site:linkedin.com/jobs/view "{company}" "{title}" "{location}"'
SEARCH_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]
SUPPORTED_LOG_FORMATS = ("json", "console")
APP_NAME = "linkedin-job-agent"
APP_VERSION = "1.0.0"
