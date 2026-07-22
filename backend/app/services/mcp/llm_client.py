
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
        timeout: int = 120,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_report(
        self,
        prompt: str,
        system: str = _SYSTEM_PROMPT,
        stream: bool = False,
    ) -> str:
        """Send *prompt* to Ollama and return the generated text.

        Parameters
        ----------
        prompt:
            The full user-facing prompt (typically from ``MCPPayload.to_prompt()``).
        system:
            Optional system instruction prepended before the user prompt.
        stream:
            If True, consume the Ollama streaming NDJSON response line-by-line.
            Defaults to False (single JSON response).

        Returns
        -------
        str
            The model's text response, or an error message prefixed with ``[ERROR]``.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{system}\n\n{prompt}",
            "stream": stream,
        }
        logger.info("OllamaClient: POST {} model={}", url, self.model)

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
        """Wysyła historię czatu do punktu końcowego /api/chat serwera Ollama.

        Służy do wieloturowej rozmowy po wygenerowaniu wstępnego raportu.

        Parameters
        ----------
        messages:
            Lista słowników zawierających klucze 'role' i 'content'.
            Przykład: [{"role": "user", "content": "hello"}]

        Returns
        -------
        str
            Odpowiedź wygenerowana przez model jako tekst.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        logger.info("OllamaClient: POST {} model={}", url, self.model)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
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

    async def health_check(self) -> bool:
        """Return True if the Ollama server responds to GET /api/tags."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False

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
