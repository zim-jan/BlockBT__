
import json

import httpx
from loguru import logger

from app.core.config import settings

"""
BlockBT MCP — OllamaClient.

Asynchronous HTTP client for a local Ollama server.
Handles prompt assembly, request, and streaming response accumulation.
Uses ``httpx.AsyncClient`` for non-blocking I/O so that FastAPI ``async def``
route handlers do not block the event loop.
"""



# ── Defaults ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "Jesteś głównym analitykiem finansowym (Quant). "
    "Twoim zadaniem jest ocena wyników strategii algorytmicznej. "
    "Zignoruj techniczną strukturę pliku JSON i skup się wyłącznie na liczbach. "
    "Zinterpretuj wskaźnik Sharpe'a, "
    "Max Drawdown oraz Win Rate. Napisz zwięzły, profesjonalny wniosek "
    "na temat ryzyka i stabilności tej strategii. "
    "Kategorycznie zabrania się opisywania czym są poszczególne pola JSON."
)


class OllamaClient:
    """Async client for the Ollama /api/generate and /api/chat endpoints.

    Parameters
    ----------
    base_url:
        Base URL of the Ollama server, e.g. ``"http://localhost:11434"``.
        Falls back to the ``OLLAMA_BASE_URL`` setting when not provided.
    model:
        Ollama model tag, e.g. ``"llama3"``.
        Falls back to the ``OLLAMA_MODEL`` setting when not provided.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        resolved_url, resolved_model, resolved_timeout = self._resolve_config(base_url, model, timeout)
        self.base_url = resolved_url.rstrip("/")
        self.model = resolved_model
        self.timeout = resolved_timeout

    @staticmethod
    def _resolve_config(
        base_url: str | None, model: str | None, timeout: int | None
    ) -> tuple[str, str, int]:
        url = base_url
        mdl = model
        tout = timeout
        if not url or not mdl or tout is None:
            try:
                from app.db.session import get_session
                from app.models.orm import AppSetting

                with get_session() as db:
                    if not url:
                        setting_url = db.get(AppSetting, "ollama_base_url")
                        if setting_url and setting_url.value:
                            url = setting_url.value
                    if not mdl:
                        setting_mdl = db.get(AppSetting, "ollama_model")
                        if setting_mdl and setting_mdl.value:
                            mdl = setting_mdl.value
                    if tout is None:
                        setting_tout = db.get(AppSetting, "ollama_timeout_seconds")
                        if setting_tout and setting_tout.value:
                            try:
                                tout = int(setting_tout.value)
                            except ValueError:
                                pass
            except Exception:
                pass
        return (
            (url or settings.OLLAMA_BASE_URL),
            (mdl or settings.OLLAMA_MODEL),
            (tout or 300),
        )

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_report(
        self,
        prompt: str,
        system: str = _SYSTEM_PROMPT,
        stream: bool = False,
    ) -> str:
        """Send *prompt* to Ollama and return the generated text."""
        url = f"{self.base_url}/api/generate"
        full_prompt = f"{system}\n\n{prompt}"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": stream,
        }
        logger.info(
            "OllamaClient: POST {} model={} timeout={}s prompt_len={}",
            url,
            self.model,
            self.timeout,
            len(full_prompt),
        )
        logger.debug("OllamaClient prompt preview: {}...", full_prompt[:200].replace("\n", " "))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                if stream:
                    return self._consume_stream_sync(response.text)

                return response.json().get("response", "")
        except httpx.TimeoutException as exc:
            logger.error("OllamaClient: request timed out after {}s — {}", self.timeout, exc)
            return f"[ERROR] Przekroczono limit czasu odpowiedzi Ollama ({self.timeout}s)."
        except httpx.ConnectError as exc:
            logger.error("OllamaClient: connection error — {}", exc)
            return f"[ERROR] Nie można połączyć się z Ollama ({self.base_url}): {exc}"
        except json.JSONDecodeError as exc:
            logger.error("OllamaClient: JSON decode error — {}", exc)
            return f"[ERROR] Nieprawidłowa odpowiedź z serwera Ollama: {exc}"
        except httpx.HTTPStatusError as exc:
            logger.error("OllamaClient: HTTP error — {}", exc)
            return f"[ERROR] Błąd HTTP z serwera Ollama: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.error("OllamaClient: unexpected error — {}", exc)
            return f"[ERROR] Nieoczekiwany błąd: {exc}"

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """Wysyła historię czatu do punktu końcowego /api/chat serwera Ollama."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        last_msg = messages[-1]["content"] if messages else ""
        logger.info(
            "OllamaClient: POST {} model={} timeout={}s num_messages={} last_msg_len={}",
            url,
            self.model,
            self.timeout,
            len(messages),
            len(last_msg),
        )
        logger.debug("OllamaClient chat last message preview: {}...", last_msg[:150].replace("\n", " "))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
        except httpx.TimeoutException as exc:
            logger.error("OllamaClient: chat request timed out after {}s — {}", self.timeout, exc)
            return f"[ERROR] Przekroczono limit czasu odpowiedzi czatu Ollama ({self.timeout}s)."
        except httpx.ConnectError as exc:
            logger.error("OllamaClient: connection error — {}", exc)
            return f"[ERROR] Nie można połączyć się z Ollama ({self.base_url}): {exc}"
        except json.JSONDecodeError as exc:
            logger.error("OllamaClient: JSON decode error — {}", exc)
            return f"[ERROR] Nieprawidłowa odpowiedź z serwera Ollama: {exc}"
        except httpx.HTTPStatusError as exc:
            logger.error("OllamaClient: HTTP error — {}", exc)
            return f"[ERROR] Błąd HTTP z serwera Ollama: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.error("OllamaClient: unexpected error — {}", exc)
            return f"[ERROR] Nieoczekiwany błąd: {exc}"

    async def get_status(self) -> dict[str, Any]:
        """Return detailed status dict for Ollama server connection and configured model."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    raw_models = data.get("models", [])
                    installed_models = [m.get("name", "") for m in raw_models if isinstance(m, dict)]
                    # Model match check (e.g. 'llama3' vs 'llama3:latest')
                    model_installed = any(
                        m == self.model or m.startswith(f"{self.model}:") for m in installed_models
                    )
                    return {
                        "available": True,
                        "base_url": self.base_url,
                        "model": self.model,
                        "installed_models": installed_models,
                        "model_installed": model_installed,
                        "error": None,
                    }
                return {
                    "available": False,
                    "base_url": self.base_url,
                    "model": self.model,
                    "installed_models": [],
                    "model_installed": False,
                    "error": f"HTTP {res.status_code}",
                }
        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "base_url": self.base_url,
                "model": self.model,
                "installed_models": [],
                "model_installed": False,
                "error": str(exc),
            }

    async def health_check(self) -> bool:
        """Return True if the Ollama server responds to GET /api/tags."""
        status = await self.get_status()
        return status["available"]

    # ── Internals ─────────────────────────────────────────────────────────────

    def _consume_stream_sync(self, text: str) -> str:
        """Parse NDJSON stream text into a single string."""
        parts: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
                parts.append(chunk.get("response", ""))
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue
        return "".join(parts)
