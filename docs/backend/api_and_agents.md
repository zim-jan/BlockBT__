# Backend - API Layer & MCP Integration

Warstwa API BlockBT stanowi pomost między silnikami obliczeniowymi a frontendem oraz zewnętrznymi agentami AI. Łączy ona klasyczny interfejs REST z nowoczesnym protokołem Model Context Protocol (MCP).

## Architektura API (FastAPI)

System API został zbudowany z wykorzystaniem frameworka **FastAPI**, co zapewnia natywną obsługę operacji asynchronicznych oraz automatyczną walidację danych poprzez Pydantic.

### Model Przetwarzania Asynchronicznego
Z uwagi na to, że backtesty i optymalizacje mogą trwać od kilku sekund do wielu minut, API stosuje wzorzec **Job Queue**:
1. Klient wysyła żądanie `POST` (np. `/api/backtest/`).
2. API tworzy rekord zadania w bazie danych ze statusem `PENDING`.
3. Zadanie jest przekazywane do `BackgroundTasks` (FastAPI thread pool).
4. API natychmiast zwraca `job_id`.
5. Klient odpytuje endpoint `GET` o status i wyniki.

### Standard Odpowiedzi (ApiResponse)
Wszystkie endpointy zwracają ujednoliconą strukturę JSON:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

---

## Katalog Endpointów

### Backtest (`/api/backtest/`)
- `POST /`: Uruchamia nowe zadanie backtestu. Przyjmuje konfigurację strategii i snapshot parametrów.
- `GET /{job_id}`: Zwraca status i metryki (Sharpe, MaxDD, Returns) dla konkretnego zadania.

### Optimizer (`/api/optimizer/`)
- `POST /`: Uruchamia optymalizację bayesowską (Optuna). Wymaga zdefiniowania zakresów (`bounds`) dla parametrów.
- `GET /{job_id}`: Zwraca najlepszą znalezioną kombinację parametrów oraz historię prób (`trials`).

### Results & AI Chat (`/api/results/`)
- `GET /{job_id}/analyze`: Wyzwala proces generowania raportu przez LLM dla zakończonego backtestu.
- `POST /{job_id}/chat`: Umożliwia interaktywną rozmowę z asystentem AI na temat konkretnego wyniku.

---

## Model Context Protocol (MCP)

BlockBT implementuje serwery MCP, które dostarczają kontekst strukturalny dla zewnętrznych modeli AI (np. Gemini, Claude).

### Architectural Router
Specjalizowany serwer MCP udostępniający narzędzia:
- **`read_safe_file`**: Bezpieczny odczyt plików projektu z rygorystyczną blokadą dostępu do folderów `vectorbtpro` (egzekwowanie polityki BYOL/Air-Gapped).
- **`get_domain_context`**: Zwraca wytyczne architektoniczne dla poszczególnych domen systemu (Backend, Frontend, DB).

### Code Knowledge Base (RAG)
Serwer MCP oparty na mechanizmie **Retrieval-Augmented Generation**:
- Wykorzystuje bazę **pgvector** do przechowywania embeddingów kodu źródłowego.
- Narzędzie **`search_my_code`** pozwala modelom AI wyszukiwać istniejące implementacje i logikę wewnątrz repozytorium.

---

## Workflow Analizy AI

Proces transformacji surowych wyników w inteligentny raport:

1. **MCP Payload**: Klasa `ReportBuilder` przekształca wyniki silnika na ustandaryzowany schemat `MCPPayload` (JSON v1.0).
2. **Downsampling**: Krzywa kapitału (equity curve) jest inteligentnie redukowana do stałej liczby punktów (np. 100), aby zminimalizować zużycie tokenów przy zachowaniu trendu.
3. **Prompting**: System generuje prompt zawierający kontekst strategii, kluczowe metryki oraz zredukowaną krzywą.
4. **OllamaClient**: Asynchroniczne wywołanie lokalnego serwera LLM (Ollama), który generuje profesjonalną ocenę ryzyka i stabilności strategii.
