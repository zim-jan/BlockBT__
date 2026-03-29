
filename = "src/blockbt/mcp/llm_client.py"
with open(filename) as f:
    content = f.read()

new_method = """
    def chat(self, messages: list[dict[str, str]]) -> str:
        \"\"\"Wysyła historię czatu do punktu końcowego /api/chat serwera Ollama.

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
        \"\"\"
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
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
                body = resp.read().decode("utf-8")
                return json.loads(body).get("message", {}).get("content", "")
        except urllib.error.URLError as exc:
            logger.error("OllamaClient: connection error — {}", exc)
            return f"[ERROR] Nie można połączyć się z Ollama ({self.base_url}): {exc}"
        except json.JSONDecodeError as exc:
            logger.error("OllamaClient: JSON decode error — {}", exc)
            return f"[ERROR] Nieprawidłowa odpowiedź z serwera Ollama: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.error("OllamaClient: unexpected error — {}", exc)
            return f"[ERROR] Nieoczekiwany błąd: {exc}"
"""

# Insert before health_check method
content = content.replace("    def health_check(self) -> bool:", new_method + "\n    def health_check(self) -> bool:")

with open(filename, "w") as f:
    f.write(content)

print("Patched llm_client.py")
