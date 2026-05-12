# Architektura Systemu

BlockBT został zaprojektowany jako modularna platforma, która oddziela warstwę wizualnego projektowania strategii od ciężkich obliczeń numerycznych i analizy opartej na sztucznej inteligencji.

## Komponenty Systemu

System składa się z czterech głównych warstw:

1.  **Frontend (React SPA)**:
    *   Udostępnia **Visual Builder** oparty na React Flow.
    *   Zarządza stanem grafu (Zustand) oraz synchronizacją z API (TanStack Query).
    *   Odpowiada za wizualizację wyników i interaktywny czat z AI.

2.  **Backend (FastAPI)**:
    *   Serwuje REST API dla frontendu.
    *   Zarządza asynchronicznymi zadaniami (Background Tasks) backtestów i optymalizacji.
    *   Implementuje protokół **MCP (Model Context Protocol)** dla zewnętrznych agentów.

3.  **Warstwa Obliczeniowa (Dual-Engine)**:
    *   **OpenSourceEngine**: Wykorzystuje bibliotekę `vectorbt` do szybkich, wektoryzowanych obliczeń.
    *   **ProEngine (BYOL)**: Abstrakcja pozwalająca na wykorzystanie `vectorbtpro` przez użytkowników posiadających licencję.

4.  **Warstwa Danych i AI**:
    *   **Data Connectors**: Pobierają dane z Yahoo Finance lub Alpaca.
    *   **Parquet Cache**: Przechowuje dane historyczne w wysoce wydajnym formacie kolumnowym.
    *   **MCP Servers**: Dostarczają kontekst kodu (RAG) i narzędzia architektoniczne dla modeli LLM (np. Ollama).

---

## Przepływ Danych (Data Flow)

Typowy cykl życia operacji w systemie wygląda następująco:

1.  **Definicja**: Użytkownik buduje graf w Visual Builderze (np. `Data -> SMA Crossover -> Portfolio`).
2.  **Żądanie**: Frontend wysyła znormalizowany opis grafu do `/api/backtest/`.
3.  **Pozyskanie Danych**: Backend sprawdza cache Parquet; jeśli brak danych, konektor (np. Yahoo Finance) pobiera je z sieci.
4.  **Egzekucja**: `EngineLoader` wybiera odpowiedni silnik, który wykonuje wektoryzowany backtest na danych OHLCV.
5.  **Persystencja**: Wyniki (metryki i krzywa kapitału) trafiają do bazy SQLite oraz do cache'u wyników.
6.  **Prezentacja**: Frontend pobiera wyniki i aktualizuje węzły na grafie.
7.  **Analiza AI**: Na żądanie użytkownika, `ReportBuilder` przygotowuje prompt MCP, a `OllamaClient` generuje tekstową analizę wyników.

---

## Kluczowe Koncepcje Techniczne

### BYOL (Bring Your Own License)
System jest w pełni funkcjonalny w oparciu o narzędzia Open Source. Architektura pozwala jednak na "podpięcie" komercyjnych bibliotek (vectorbtpro) bez modyfikacji jądra aplikacji, co jest realizowane przez dynamiczne ładowanie (lazy loading) i wzorzec adaptera.

### Wektoryzacja Parametrów
BlockBT promuje podejście wektorowe. Zamiast uruchamiać wiele backtestów w pętli, system przesyła tablice parametrów bezpośrednio do silnika, co pozwala na wykorzystanie optymalizacji na poziomie procesora (NumPy/Numba).

### AI-First Documentation & Search
Dzięki integracji MCP i lokalnej bazie wektorowej (pgvector), dokumentacja i kod źródłowy są natywnie dostępne dla modeli AI, co wspiera proces tworzenia strategii i debugowania.
