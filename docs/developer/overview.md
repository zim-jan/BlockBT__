# Developer Overview — BlockBT

Witaj w sercu systemu BlockBT! Ten dokument stanowi mapę wysokopoziomową dla każdego dewelopera, który chce zrozumieć jak "rozmawia" ze sobą Frontend, Silnik Backtestingowy oraz Baza Danych.

## 🗺️ Architektura Systemu

BlockBT opiera się na pięciu głównych warstwach, które są od siebie logicznie odseparowane:

1. **Frontend Layer (Streamlit)**: 
   - Lokalizacja: `/pages/` oraz `app.py`.
   - Rola: Interfejs użytkownika, kreatory (Wizards), wizualizacje Plotly i edytor grafowy React Flow (`6_Visual_Builder.py`).
2. **Business Logic / Engine Layer**:
   - Lokalizacja: `src/blockbt/engine/`.
   - Rola: Abstrakcja silników backtestingowych (`StrategyEngine`). Obsługuje zarówno silnik OpenSource (`vectorbt`), jak i dynamicznie ładowany ProEngine.
3. **Data Access Layer (Connectors)**:
   - Lokalizacja: `src/blockbt/connectors/`.
   - Rola: Łączenie się z API zewnętrznymi (Yahoo, Alpaca) i cache'owanie danych w formacie Parquet dla maksymalnej wydajności.
4. **Data Persistence Layer (Database)**:
   - Lokalizacja: `src/blockbt/db/`.
   - Rola: SQLAlchemy ORM. Przechowywanie użytkowników, szablonów strategii (`StrategyTemplate`) oraz wyników symulacji.
5. **API Layer (REST)**:
   - Lokalizacja: `src/blockbt/api/`.
   - Rola: Wystawianie funkcjonalności systemu na zewnątrz (FastAPI).

## 🛠️ Stack Techniczny

- **Core**: Python 3.10+
- **Backtesting**: [vectorbt](https://vectorbt.dev/) (Open Source / PRO)
- **UI**: [Streamlit](https://streamlit.io/) + [streamlit-flow-component](https://github.com/langchain-ai/langchain)
- **Database**: SQLite (SQLAlchemy)
- **Analytics**: pandas-ta, Optuna (Optymalizacja Bayesowska)
- **LLM**: Ollama (Interfejs MCP)

## 📂 Główne Lokalizacje Kodowe

- [auth.py](file:///home/przydan/my_project/src/blockbt/ui/auth.py) — Bramka logowania i persystencja ciasteczek.
- [opensource_engine.py](file:///home/przydan/my_project/src/blockbt/engine/opensource_engine.py) — Implementacja parsera AST i logiki pandas-ta.
- [models.py](file:///home/przydan/my_project/src/blockbt/db/models.py) — Definicje wszystkich tabel SQL.
- [config.py](file:///home/przydan/my_project/src/blockbt/config.py) — Centralna konfiguracja (Ścieżki, API Keys, Silniki).

---
### Następne Kroki:
- Przeczytaj [Class Reference](class_reference.md), aby poznać hierarchię obiektów.
- Zobacz [Extending Data Sources](extending_data.md), jeśli chcesz dodać własne API.
