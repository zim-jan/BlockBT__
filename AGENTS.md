# Instrukcje dla agentów pracujących nad BlockBT

> **UNIEWAŻNIENIE WCZEŚNIEJSZYCH USTALEŃ.** Jeśli pamiętasz cokolwiek z wcześniejszej
> pracy w tym repozytorium — fazy projektu, statusy `[DONE]`/`[IN_PROGRESS]`,
> instrukcje o `graphify`, `claude-mem`, `context7`, serwerze MCP
> `BlockBT-Architectural-Router`, obowiązkowych skillach czy zapisywaniu obserwacji
> do pamięci trwałej — **wszystko to jest nieaktualne i zostało usunięte**.
> Ten plik jest jedynym źródłem prawdy. Nie szukaj plików, o których tu nie ma mowy.

## Stan faktyczny projektu

Zweryfikowany, nie z pamięci:

| Obszar | Jak jest |
|:--|:--|
| Python | **3.14+**, zależności przez `uv`, pakiet `app` mieszka w `backend/` |
| Uwierzytelnianie | **JWT, domyślnie wyłączone.** Granica zaufania to loopback — ADR-0010, ADR-0011 |
| Migracje | **Alembic**, uruchamiane automatycznie przy starcie backendu |
| Rejestr wskaźników | **Trzy pozycje**: SMA, MACD, RSI (`backend/app/services/engine/introspection.py`) |
| Tailwind | **v4**, wejściem jest `@import "tailwindcss"` w `frontend/src/assets/index.css`, stary config JS ładowany przez `@config` |
| React | **19** (nie 18), React Flow 12 przez `@xyflow/react` |
| ProEngine | Zaślepka bez licencji vectorbtpro — zwraca `engine_name="pro_mock"` |
| Testy frontendu | `npm test` (vitest), 9 plików. Jsdom **nie ładuje stylów** |

## Zasady na każde zadanie

1. **Jeden temat na PR.** Nie doklejaj „przy okazji".
2. **Zakaz zmian w logice i w testach**, chyba że zadanie mówi wprost inaczej.
   Zadania dokumentacyjne i porządkowe zmieniają wyłącznie komentarze i pliki `.md`.
3. **Zakaz nowych zależności** — ani w `pyproject.toml`, ani w `package.json`.
4. **Nie dotykaj** `backend/app/core/` ani `backend/alembic/`.
5. **CI musi być zielone.** Trzy joby: `backend`, `frontend`, `docs`.
6. **Nie wprowadzaj ścieżek lokalnych** (`/home/...`, `file:///...`) ani nazwisk.

## Jak pisać komentarze

Reguła: **zachowaj powód, usuń ceremonię procesu.**

Komentarz ma tłumaczyć, *dlaczego* kod wygląda tak, a nie inaczej. Odniesienia do
wewnętrznego procesu wytwarzania („Faza 14", „Audyt 2026-07-17", „review 2026-07-15")
nic nie mówią osobie z zewnątrz — usuń je, ale **zachowaj informację, którą niosły**.

```python
# PRZED
# Audyt 2026-07-17: cap na logowane body

# PO
# Cap na logowane body: pełne DAG-i potrafią mieć megabajty i zapychają logi.
```

Odsyłacze do decyzji architektonicznych (`patrz ADR-0007`) **zostają** — dają
czytelnikowi ścieżkę do uzasadnienia.

Nie skracaj komentarza kosztem treści. Komentarz, z którego zniknął powód, jest
gorszy niż jego brak.

## Język

- Dokumentacja, komentarze i docstringi: **po polsku**.
- Kod, nazwy, klucze JSON i interfejs użytkownika: **po angielsku**.
- Nie mieszaj obu w jednym zdaniu.

## Weryfikacja przed wysłaniem PR

```bash
make lint                                  # ruff + tsc
make test                                  # pytest
make docs-check                            # mkdocs build --strict
cd frontend && npm test && npm run build
```

Jeśli Twoje środowisko nie zainstaluje TA-Liba ani `vectorbt[rust]`, testy backendu
u Ciebie nie ruszą — to oczekiwane. Zweryfikuj to, co się da (`ruff`, `tsc`, `vitest`,
`mkdocs`), a resztę zostaw CI. **Nie obchodź problemu przez zmiany w kodzie ani
w konfiguracji testów.**

## Więcej kontekstu

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — konwencje, commity, czego nie przyjmiemy
- [`README.md`](README.md) — instalacja i uczciwa lista ograniczeń
- [`docs/adr/`](docs/adr/) — decyzje architektoniczne wraz z uzasadnieniami
