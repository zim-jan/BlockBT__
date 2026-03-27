"""
BlockBT MCP — OllamaClient.

Synchronous HTTP client for a local Ollama server.
Handles prompt assembly, request, and streaming response accumulation.
Uses only the standard-library ``urllib`` so no additional dependency is
needed beyond what blockbt already ships.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from loguru import logger

from blockbt.config import settings

# ── Defaults ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "Jesteś głównym analitykiem finansowym (Quant). Twoim zadaniem jest ocena wyników strategii algorytmicznej. "
    "Zignoruj techniczną strukturę pliku JSON i skup się wyłącznie na liczbach. Zinterpretuj wskaźnik Sharpe'a, "
    "Max Drawdown oraz Win Rate. Napisz zwięzły, profesjonalny wniosek na temat ryzyka i stabilności tej strategii. "
    "Kategorycznie zabrania się opisywania czym są poszczególne pola JSON."
)


class OllamaClient:
    """Synchronous client for the Ollama /api/generate endpoint.

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

    def generate_report(
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
            Defaults to False (single JSON response) for simplicity under Streamlit.

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
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        logger.info("OllamaClient: POST {} model={}", url, self.model)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if stream:
                    return self._consume_stream(resp)
                body = resp.read().decode("utf-8")
                return json.loads(body).get("response", "")
        except urllib.error.URLError as exc:
            logger.error("OllamaClient: connection error — {}", exc)
            return f"[ERROR] Nie można połączyć się z Ollama ({self.base_url}): {exc}"
        except json.JSONDecodeError as exc:
            logger.error("OllamaClient: JSON decode error — {}", exc)
            return f"[ERROR] Nieprawidłowa odpowiedź z serwera Ollama: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.error("OllamaClient: unexpected error — {}", exc)
            return f"[ERROR] Nieoczekiwany błąd: {exc}"

    def health_check(self) -> bool:
        """Return True if the Ollama server responds to GET /api/tags."""
        try:
            url = f"{self.base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=5):
                return True
        except Exception:  # noqa: BLE001
            return False

    # ── Internals ─────────────────────────────────────────────────────────────

    def _consume_stream(self, resp) -> str:  # type: ignore[type-arg]
        """Accumulate NDJSON stream lines into a single string."""
        parts: list[str] = []
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
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
