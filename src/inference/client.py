import httpx
import structlog
import time
from typing import Any
from config import Settings
from exceptions import InferenceError, LLMConnectionError, OllamaConnectionError

logger = structlog.get_logger()

class LLMClient:
    """Universal client for local LLMs/SLMs supporting LM Studio, Ollama, and OpenAI-compatible endpoints."""
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._provider = getattr(settings, "llm_provider", "local").lower()
        self._api_key = (getattr(settings, "llm_api_key", "") or "").strip()
        
        # Determine base URL and model based on provider or fallback
        if self._provider in ("lm_studio", "openai", "local", "online"):
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
            
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        is_local = (
            self._provider in ("local", "lm_studio", "ollama")
            or "localhost" in self._base_url
            or "127.0.0.1" in self._base_url
            or "0.0.0.0" in self._base_url
            or ":1234" in self._base_url
            or ":11434" in self._base_url
        )
        if is_local:
            # For local models, cold-start model weight loading from disk into VRAM/RAM
            # can take significant time. Fast connect timeout (10s), but no read timeout.
            client_timeout = httpx.Timeout(timeout=None, connect=10.0)
        else:
            client_timeout = httpx.Timeout(timeout=self._timeout, connect=15.0)

        self._client = httpx.Client(timeout=client_timeout, headers=headers)
    
    @property
    def provider(self) -> str:
        return self._provider
    
    @property
    def model(self) -> str:
        return self._model
    
    def health_check(self) -> bool:
        """Check if local LLM server is reachable and ready."""
        # Check OpenAI / LM Studio / Local / Online endpoint
        if self._provider in ("lm_studio", "openai", "local", "online") or "/v1" in self._base_url or "1234" in self._base_url:
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
        """Send generation request to LLM (LM Studio Chat Completions, Ollama, or OpenAI-compatible online provider) and return response text."""
        # Use OpenAI Chat Completions for LM Studio / Local / Online / OpenAI
        if self._provider in ("lm_studio", "openai", "local", "online") or "/v1" in self._base_url or "1234" in self._base_url:
            clean_url = self._base_url.rstrip("/")
            if clean_url.endswith("/chat/completions"):
                chat_url = clean_url
            elif clean_url.endswith("/v1") or "/v1" in clean_url:
                chat_url = f"{clean_url}/chat/completions"
            else:
                chat_url = f"{clean_url}/v1/chat/completions"

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


def check_llm_connection(
    base_url: str,
    model: str,
    api_key: str = "",
    provider: str = "local",
    timeout: float | None = None,
) -> dict[str, Any]:
    """Test connection to an LLM provider and model.

    Verifies reachable URL, valid API key (if provided), and model generation capability.
    For local endpoints (localhost / 127.0.0.1), disables read timeout so that cold-start
    model weight loading into VRAM is given adequate time.
    Returns:
        {"success": bool, "message": str, "latency_ms"?: float, "model"?: str, "error"?: str}
    """
    clean_url = base_url.strip().rstrip("/")
    clean_model = model.strip()
    if not clean_url:
        return {"success": False, "error": "Base URL cannot be empty.", "message": "Missing Base URL"}
    if not clean_model:
        return {"success": False, "error": "Model name cannot be empty.", "message": "Missing Model Name"}

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    is_local = (
        provider.lower() in ("local", "lm_studio", "ollama")
        or "localhost" in clean_url
        or "127.0.0.1" in clean_url
        or "0.0.0.0" in clean_url
        or ":1234" in clean_url
        or ":11434" in clean_url
    )

    if timeout is not None:
        client_timeout = httpx.Timeout(timeout=timeout, connect=10.0)
    elif is_local:
        # Local model: connect to server quickly (10s), but allow unlimited read timeout
        # so cold-start model weight loading into VRAM/RAM never aborts prematurely.
        client_timeout = httpx.Timeout(timeout=None, connect=10.0)
    else:
        # Online APIs: use 60.0s total with 15.0s connect
        client_timeout = httpx.Timeout(timeout=60.0, connect=15.0)

    start_time = time.perf_counter()
    try:
        with httpx.Client(timeout=client_timeout, headers=headers) as client:
            # Check if native Ollama is explicitly selected
            if provider.lower() == "ollama" and "/v1" not in clean_url:
                target_url = f"{clean_url}/api/generate"
                payload = {
                    "model": clean_model,
                    "prompt": "Respond with 'Connected' only.",
                    "stream": False,
                    "options": {"num_predict": 5},
                }
                response = client.post(target_url, json=payload)
                response.raise_for_status()
                data = response.json()
                reply = data.get("response", "").strip()
            else:
                # Standard OpenAI Chat Completions (LM Studio, OpenAI, Groq, OpenRouter, etc.)
                if clean_url.endswith("/chat/completions"):
                    chat_url = clean_url
                elif clean_url.endswith("/v1") or "/v1" in clean_url:
                    chat_url = f"{clean_url}/chat/completions"
                else:
                    chat_url = f"{clean_url}/v1/chat/completions"

                payload = {
                    "model": clean_model,
                    "messages": [{"role": "user", "content": "Respond with 'Connected' only."}],
                    "max_tokens": 10,
                }
                response = client.post(chat_url, json=payload)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                reply = ""
                if choices:
                    msg = choices[0].get("message", {})
                    reply = (msg.get("content") or msg.get("reasoning_content") or "").strip()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
            msg_snippet = f' (response: "{reply[:40]}")' if reply else ""
            return {
                "success": True,
                "message": f"Successfully connected to '{clean_model}' in {latency_ms}ms!{msg_snippet}",
                "latency_ms": latency_ms,
                "model": clean_model,
            }

    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Connection refused to {clean_url}. Ensure your local server is running or URL is correct.",
            "message": "Connection refused",
        }
    except httpx.ConnectTimeout:
        return {
            "success": False,
            "error": f"Connection timed out trying to reach {clean_url} after 10s. Server is not responding on that port.",
            "message": "Connection timed out",
        }
    except httpx.ReadTimeout:
        return {
            "success": False,
            "error": "Model response timed out. The server is reachable, but model generation took too long.",
            "message": "Read timed out",
        }
    except httpx.TimeoutException as e:
        return {
            "success": False,
            "error": f"Request timed out: {e}",
            "message": "Connection timed out",
        }
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            err_json = e.response.json()
            detail = err_json.get("error", {}).get("message") or str(err_json)
        except Exception:
            detail = e.response.text[:200]
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {detail}",
            "message": f"HTTP Error {e.response.status_code}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Connection test failed",
        }

