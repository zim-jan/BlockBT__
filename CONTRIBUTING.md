# Współtworzenie BlockBT

Dzięki za zainteresowanie. Ten dokument opisuje, jak uruchomić środowisko i czego
oczekujemy od zmian.

## Środowisko deweloperskie

Wymagania: **Python 3.14+**, **Node.js 20+**, **TA-Lib** (biblioteka C — instrukcja
instalacji w [README](README.md#instalacja)) oraz [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev                 # backend + narzędzia deweloperskie
cd frontend && npm ci && cd ..      # frontend
cp .env.example .env                # SECRET_KEY wygenerujesz komendą z komentarza w pliku
```

Uruchomienie: `make api` (backend, port 8000) i `cd frontend && npm run dev`
(frontend, port 3000). Oba nasłuchują wyłącznie na `127.0.0.1` — to celowe,
patrz [ADR-0011](docs/adr/0011-loopback-jako-granica-zaufania.md).

## Zanim wyślesz PR

```bash
make lint        # ruff (Python) + tsc --noEmit (TypeScript)
make test        # pytest
make docs-check  # mkdocs build --strict
cd frontend && npm test && npm run build
```

Te same polecenia jedzie CI — jeśli przechodzą lokalnie, przejdą i tam.

## Zasady, na których nam zależy

**Jeden temat na PR.** Refaktor, poprawka i nowa funkcja w jednym diffie to trzy
osobne PR-y. Przegląd takiego zlepka trwa dłużej niż napisanie go od nowa.

**Komentarze tłumaczą „dlaczego", nie „co".** Kod już mówi, co robi. Komentarz ma
sens, gdy zapisuje powód nieoczywistej decyzji:

```python
# ŹLE — powtarza kod
# Ustawiamy cap na 10000
MAX_BODY = 10_000

# DOBRZE — zapisuje powód
# Cap na logowane body: pełne DAG-i potrafią mieć megabajty i zapychają logi.
MAX_BODY = 10_000
```

Odsyłacze do decyzji (`patrz ADR-0007`) są mile widziane — dają czytelnikowi ścieżkę
do uzasadnienia. Odsyłacze do wewnętrznego procesu („Faza 14", „audyt z 2026-07-17")
nic nie mówią osobie z zewnątrz — pomiń je.

**Decyzje architektoniczne trafiają do ADR.** Zmieniasz coś, co za pół roku ktoś
zapyta „czemu tak?" — dopisz `docs/adr/00XX-krotki-tytul.md` wzorowany na istniejących
i podlinkuj go z kodu. Dotyczy m.in. wyboru bibliotek, granic zaufania, formatu API.

**Testy razem ze zmianą.** Backend: `backend/tests/`, pytest. Frontend: `*.test.tsx`
obok komponentu, vitest + Testing Library. Poprawka błędu powinna przyjść z testem,
który bez niej nie przechodzi.

**Uwaga na CSS.** Testy frontendu jadą w jsdom, który **nie ładuje stylów** — zielony
`vitest` nie mówi nic o tym, czy Tailwind wygenerował klasy. Dlatego CI pilnuje
rozmiaru zbudowanego arkusza. Jeśli ta asercja padnie, sprawdź `content`
w `frontend/tailwind.config.js` i `@import "tailwindcss"` w `frontend/src/assets/index.css`.

## Język

- **Dokumentacja, komentarze i docstringi: po polsku.**
- **Kod, nazwy, klucze JSON i interfejs użytkownika: po angielsku.**
- Nie mieszaj obu w jednym zdaniu.

## Commity

Format [Conventional Commits](https://www.conventionalcommits.org/), opis po polsku:

```
feat(engine): dodaj wskaźnik ATR do rejestru introspekcji
fix(auth): odrzucaj tokeny bez pola `exp`
docs(adr): udokumentuj wybór Alembica zamiast ręcznych migracji
```

Typy w użyciu: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `build`.

## Czego nie przyjmiemy

- Kodu vectorbtpro w jakiejkolwiek postaci — to produkt komercyjny, integracja działa
  w modelu BYOL i tak zostanie.
- Zmian rozluźniających walidator AST w `backend/app/services/engine/indicators.py`
  bez wyraźnego uzasadnienia bezpieczeństwa.
- Nowych zależności runtime bez uzasadnienia w opisie PR-a.
- Wygenerowanych artefaktów (buildy, cache, zrzuty narzędzi) w drzewie repozytorium.

## Bezpieczeństwo

Podatności zgłaszaj zgodnie z [SECURITY.md](SECURITY.md), **nie** przez publiczne issue.
