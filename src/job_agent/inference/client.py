import httpx
import structlog
import time
from typing import Any
from job_agent.config import Settings
from job_agent.exceptions import InferenceError, LLMConnectionError, OllamaConnectionError

logger = structlog.get_logger()

class LLMClient:
    """Universal client for local LLMs/SLMs supporting LM Studio, Ollama, and OpenAI-compatible endpoints."""
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._provider = getattr(settings, "llm_provider", "lm_studio").lower()
        
        # Determine base URL and model based on provider or fallback
        if self._provider in ("lm_studio", "openai"):
            self._base_url = settings.llm_base_url.rstrip("/")
            self._model = settings.llm_model
            self._temperature = settings.llm_temperature
            self._timeout = settings.llm_timeout
            self._max_retries = settings.llm_max_retries
        else:
            # Ollama
            self._base_url = settings.ollama_base_url.rstrip("/")
            self._model = settings.ollama_model
            self._temperature = settings.ollama_temperature
            self._timeout = settings.ollama_timeout
            self._max_retries = settings.ollama_max_retries
            
        self._client = httpx.Client(timeout=self._timeout)
    
    @property
    def provider(self) -> str:
        return self._provider
    
    @property
    def model(self) -> str:
        return self._model
    
    def health_check(self) -> bool:
        """Check if local LLM server is reachable and ready."""
        # Check OpenAI / LM Studio endpoint
        if self._provider in ("lm_studio", "openai") or "/v1" in self._base_url or "1234" in self._base_url:
            models_url = f"{self._base_url}/models" if not self._base_url.endswith("/models") else self._base_url
            try:
                response = self._client.get(models_url)
                response.raise_for_status()
                data = response.json()
                models = [m.get("id") for m in data.get("data", [])]
                
                # If exact model is loaded or if any models exist
                if self._model in models:
                    logger.info("LM Studio health check passed", model=self._model, provider=self._provider)
                elif models:
                    logger.info("LM Studio reachable with loaded models", active_model=models[0], requested_model=self._model)
                    self._model = models[0]
                else:
                    logger.warning("LM Studio reachable but no model returned", provider=self._provider)
                return True
            except httpx.RequestError as e:
                logger.error("LM Studio connection failed", error=str(e), url=models_url)
                raise LLMConnectionError(f"Failed to connect to LM Studio at {self._base_url}: {e}") from e
            except Exception as e:
                logger.error("LM Studio health check error", error=str(e))
                return False

        # Fallback to Ollama native check
        try:
            url = f"{self._base_url}/api/tags"
            response = self._client.get(url)
            response.raise_for_status()
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            
            if self._model not in models:
                logger.warning("Ollama model not found", model=self._model, available=models)
                return False
                
            logger.info("Ollama health check passed", model=self._model)
            return True
        except httpx.RequestError as e:
            logger.error("Ollama connection failed", error=str(e))
            raise OllamaConnectionError(f"Failed to connect to Ollama at {self._base_url}: {e}") from e
        except Exception as e:
            logger.error("Ollama health check error", error=str(e))
            return False

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Send generation request to LLM (LM Studio Chat Completions or Ollama) and return response text."""
        # Use OpenAI Chat Completions for LM Studio
        if self._provider in ("lm_studio", "openai") or "/v1" in self._base_url or "1234" in self._base_url:
            chat_url = f"{self._base_url}/chat/completions"
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self._model,
                "messages": messages,
                "temperature": self._temperature,
                "max_tokens": 1500,
            }
            
            for attempt in range(self._max_retries):
                start_time = time.perf_counter()
                try:
                    response = self._client.post(chat_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    latency = time.perf_counter() - start_time
                    logger.debug("LM Studio generation successful", latency=latency, attempt=attempt+1)
                    
                    choices = data.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        content = msg.get("content") or ""
                        if not content and msg.get("reasoning_content"):
                            content = msg.get("reasoning_content", "")
                        return content
                    return ""
                except httpx.ConnectError as e:
                    logger.error("LM Studio connection error", error=str(e))
                    raise LLMConnectionError(f"Connection error: {e}") from e
                except httpx.TimeoutException as e:
                    latency = time.perf_counter() - start_time
                    logger.warning("LM Studio generation timeout", attempt=attempt+1, latency=latency)
                    if attempt == self._max_retries - 1:
                        raise InferenceError(f"LM Studio generation timed out after {self._max_retries} attempts") from e
                except httpx.HTTPStatusError as e:
                    latency = time.perf_counter() - start_time
                    logger.error("LM Studio HTTP error", status_code=e.response.status_code, response=e.response.text, attempt=attempt+1, latency=latency)
                    if attempt == self._max_retries - 1:
                        raise InferenceError(f"LM Studio HTTP error {e.response.status_code}: {e.response.text}") from e
                except Exception as e:
                    latency = time.perf_counter() - start_time
                    logger.error("LM Studio generation unknown error", error=str(e), attempt=attempt+1, latency=latency)
                    if attempt == self._max_retries - 1:
                        raise InferenceError(f"LM Studio generation failed: {e}") from e
                
                time.sleep(2 ** attempt)
            
            raise InferenceError("Exhausted retries without success")
            
        # Native Ollama generate endpoint
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self._temperature
            }
        }
        
        for attempt in range(self._max_retries):
            start_time = time.perf_counter()
            try:
                response = self._client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                latency = time.perf_counter() - start_time
                logger.debug("Ollama generation successful", latency=latency, attempt=attempt+1)
                return data.get("response", "")
            except httpx.ConnectError as e:
                logger.error("Ollama connection error", error=str(e))
                raise OllamaConnectionError(f"Connection error: {e}") from e
            except httpx.TimeoutException as e:
                latency = time.perf_counter() - start_time
                logger.warning("Ollama generation timeout", attempt=attempt+1, latency=latency)
                if attempt == self._max_retries - 1:
                    raise InferenceError(f"Ollama generation timed out after {self._max_retries} attempts") from e
            except httpx.HTTPStatusError as e:
                latency = time.perf_counter() - start_time
                logger.error("Ollama generation HTTP error", status_code=e.response.status_code, response=e.response.text, attempt=attempt+1, latency=latency)
                if attempt == self._max_retries - 1:
                    raise InferenceError(f"Ollama HTTP error {e.response.status_code}: {e.response.text}") from e
            except Exception as e:
                latency = time.perf_counter() - start_time
                logger.error("Ollama generation unknown error", error=str(e), attempt=attempt+1, latency=latency)
                if attempt == self._max_retries - 1:
                    raise InferenceError(f"Ollama generation failed: {e}") from e
            
            time.sleep(2 ** attempt)
            
        raise InferenceError("Exhausted retries without success")

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self) -> "LLMClient":
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()

# Backward compatibility alias
OllamaClient = LLMClient
