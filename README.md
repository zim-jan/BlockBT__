# BlockBT

**Lokalne środowisko do backtestingu strategii algorytmicznych z wizualnym edytorem grafowym.**

Budujesz strategię, łącząc bloki na płótnie — źródło danych, wskaźniki, warunki wejścia
i wyjścia, portfel. Backend zamienia ten graf na wektorowy backtest na `vectorbt`
i zwraca wyniki. Wszystko działa na Twojej maszynie, na `127.0.0.1`.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

---

## Co potrafi

- **Wizualny edytor strategii** — graf oparty na React Flow 12. Węzły łączysz myszą,
  walidator pilnuje, żeby połączenie miało sens.
- **Wektorowy silnik backtestingu** — `vectorbt` z kompilacją Numba. Optymalizacja
  parametrów wchodzi jako dodatkowy wymiar macierzy, nie jako pętla po kombinacjach.
- **Optymalizacja parametrów** — Optuna, w tym walk-forward (WFO).
- **Własne wskaźniki w Pythonie** — pisane w przeglądarce, wykonywane za walidatorem AST.
- **Analityka portfela** — statystyki przez QuantStats, zarządzanie ryzykiem (SL/TP/sizing).
- **Dane** — Yahoo Finance z cache'em Parquet; opcjonalnie Alpaca (własny klucz).

Architektura, decyzje i szczegóły API: [dokumentacja](docs/index.md)
(`make docs-serve` uruchamia ją lokalnie).

---

## Ograniczenia — przeczytaj przed instalacją

Projekt powstał jako praca inżynierska i **nie jest produktem gotowym do obrotu
prawdziwymi pieniędzmi**. Rzeczy, o których lepiej wiedzieć od razu:

| Obszar | Stan faktyczny |
|:--|:--|
| **Rejestr wskaźników** | **Trzy pozycje**: SMA, MACD, RSI. Kuratorowany katalog w `backend/app/services/engine/introspection.py`. Resztę dopisujesz sam jako wskaźnik własny. |
| **ProEngine (vectorbtpro)** | Bez licencji vectorbtpro działa jako **zaślepka** zwracająca symulowane wyniki oznaczone `engine_name="pro_mock"`. To nie jest backtest. Model BYOL — biblioteki nie dostarczamy. |
| **Tearsheet** | Generowany jako tekst/Markdown ze statystykami. **Bez wykresów.** |
| **Uwierzytelnianie** | JWT, **domyślnie wyłączone**. Model zagrożeń zakłada, że granicą zaufania jest loopback ([ADR-0011](docs/adr/0011-loopback-jako-granica-zaufania.md)). |
| **Piaskownica wskaźników** | Walidator AST z listą dozwolonych węzłów. Chroni przed pomyłką, **nie przed atakiem** — nie uruchamiaj cudzego kodu. Patrz [SECURITY.md](SECURITY.md). |
| **„Air-gapped"** | Prawie. Arkusz stylów pobiera fonty z `fonts.googleapis.com` (`frontend/src/assets/index.css`). Bez internetu aplikacja działa, tylko z zapasowym krojem. |
| **Bundle frontendu** | ~5,4 MB (Plotly). Bez code-splittingu. |

---

## Instalacja

### Wymagania

- **Python 3.14+**
- **Node.js 20+**
- **TA-Lib** — biblioteka C, wymagana przez `vectorbt`
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

### 1. TA-Lib

Pakiet PyPI `ta-lib` to tylko wiązanie — bez biblioteki C instalacja zależności padnie
na etapie budowania. To najczęstsza przyczyna nieudanego `uv sync` w tym projekcie.

```bash
# macOS
brew install ta-lib

# Debian / Ubuntu — pakietu nie ma w repozytoriach, budujemy ze źródeł
wget https://github.com/TA-Lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz
tar -xzf ta-lib-0.6.4-src.tar.gz && cd ta-lib-0.6.4
./configure --prefix=/usr && make -j"$(nproc)" && sudo make install && sudo ldconfig

# Windows — użyj gotowego wheela ze strony projektu TA-Lib
```

### 2. Projekt

```bash
git clone <adres-repozytorium> && cd BlockBT

uv sync --extra dev                   # backend (uv sam pobierze Pythona 3.14)
cd frontend && npm ci && cd ..        # frontend

cp .env.example .env
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# wklej wynik jako SECRET_KEY w .env — bez tego aplikacja nie wstanie
```

### 3. Uruchomienie

```bash
make api                              # backend  → http://127.0.0.1:8000/docs
cd frontend && npm run dev            # frontend → http://127.0.0.1:3000
```

Albo jednym poleceniem: `./run_local.sh` (odpala oba procesy i sam generuje `.env`).

Baza SQLite i migracje Alembica wykonują się przy starcie backendu. Dane lądują
w `backend/data/`.

### Docker (alternatywa)

```bash
cp .env.example .env   # ustaw SECRET_KEY
docker compose up --build
```

Obraz backendu buduje TA-Lib ze źródeł — pierwsze uruchomienie trwa kilka minut.

---

## Polecenia

| Polecenie | Działanie |
|:--|:--|
| `make api` | backend FastAPI (port 8000) |
| `make frontend` | frontend Vite (port 3000) |
| `make lint` | `ruff` + `tsc --noEmit` |
| `make test` | testy backendu (pytest) |
| `make test-frontend` | testy frontendu (vitest) |
| `make docs-check` | `mkdocs build --strict` — to samo co CI |
| `make docs-serve` | dokumentacja na `127.0.0.1:8001` |
| `make migrate` | migracje Alembica |
| `make generate-api` | regeneracja typów TS z OpenAPI (wymaga działającego backendu) |
| `make clean` | czyszczenie cache'ów |

`make help` wypisuje pełną listę.

---

## Stos technologiczny

**Frontend** — React 19, TypeScript, Vite, Tailwind CSS v4, React Flow 12
(`@xyflow/react`), Zustand, TanStack Query, Plotly.

**Backend** — Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, `vectorbt`
z Numbą, Optuna, QuantStats, TA-Lib.

**Dokumentacja** — MkDocs Material, ADR-y w `docs/adr/`.

---

## Jak to działa

Frontend eksportuje strategię jako DAG (JSON) i wysyła na `POST /api/backtest/dag`.
Backend parsuje graf i uruchamia backtest wektorowo.

| Kategoria węzła | Rola | Dozwolone połączenia wychodzące |
|:--|:--|:--|
| **DataIngestion** | źródło danych | Indicators, Execution |
| **Indicators** | transformacje (SMA, MACD, RSI, własne) | LogicOperators, Execution |
| **LogicOperators** | maski logiczne (entries/exits) | Execution |
| **Execution** | portfel (`Portfolio.from_signals`) | — |
| **Meta** | optymalizatory parametrów | — (przez `target_nodes`) |

`GraphParser` sprawdza przed uruchomieniem: brak cykli (algorytm Kahna), zgodność typów
portów, dokładnie jeden węzeł Execution, brak osieroconych węzłów.

**Look-ahead bias:** sygnały wejścia i wyjścia są bezwarunkowo przesuwane o jeden okres
(`fshift`) w silniku, bez udziału użytkownika — [ADR-0007](docs/adr/0007-usuniecie-bloku-timeshift-auto-shift.md).

---

## Współtworzenie

Zasady, konwencje i lista rzeczy, których nie przyjmiemy: [CONTRIBUTING.md](CONTRIBUTING.md).
Podatności zgłaszaj zgodnie z [SECURITY.md](SECURITY.md), nie przez publiczne issue.

## Licencja

[Apache-2.0](LICENSE). Zależności zewnętrzne mają własne licencje — patrz [NOTICE](NOTICE).

`vectorbtpro` jest produktem komercyjnym i **nie jest** tu dołączony ani redystrybuowany.
