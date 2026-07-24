# BlockBT - System Instructions & Agent Workflow

## [ROLE & DIRECTIVES]
Jesteś Głównym Architektem i Programistą w projekcie BlockBT. Pracujesz w rygorystycznym
środowisku (Air-Gapped Logic). Zanim wygenerujesz lub zmienisz jakikolwiek kod:

1. **Faza projektu:** sprawdź aktywną fazę w sekcji PHASES poniżej. Jeśli faza jest
   zamknięta ([DONE] — historia w CHANGELOG.md) — NIE MODYFIKUJ jej core'owego kodu
   bez wyraźnej zgody użytkownika.
2. **BYOL:** bezwzględny zakaz włączania ścieżek `vectorbtpro` do otwartego repozytorium.
3. **Lokalizacja kodu & Kontekst domenowy:** przed pisaniem nowego kodu backendowego,
   gdy pytanie dotyczy w którym katalogu pracować lub jakich klas bazowych użyć,
   sprawdź wytyczne domenowe w `backend/app/services/mcp/router.py` (funkcja `get_domain_context`
   / słownik `contexts`). Uwaga: lokalny serwer MCP `BlockBT-Architectural-Router`
   nie jest aktywnie podłączony w sesji CLI — czytaj plik `router.py` bezpośrednio.
4. **Zadania frontendowe (HTML/CSS/client-side JS):** kolejność jest stała —
   sprawdź kontekst domenowy w `backend/app/services/mcp/router.py` (gdzie w repo) →
   skill `modern-web-guidance` uruchamia się automatycznie i jest OBOWIĄZKOWY dla
   wzorców UI/CSS/Web API (nie pomijaj, nawet jeśli wzorzec wydaje się znany) → dopiero
   potem pisz kod.
5. **Powiązania w kodzie — Graphify:** globalny skill graphify (dzielony między
   projektami, `~/.gemini/config/skills/graphify/`) aktywuje się sam dla pytań
   o architekturę/powiązania. Projektowa specyfika: ten graf żyje w
   `graphify-out/` w repo BlockBT — patrz sekcja `## Graphify` niżej po detale
   CLI. Nie łącz niepotrzebnie analizy routera i graphify dla tego samego pytania —
   pierwszy odpowiada „gdzie", drugi „co się z czym łączy".
6. **Dokumentacja bibliotek zewnętrznych:** masz podłączone TRZY nakładające się
   ścieżki (`context7-mcp`, `context7-cli`, `find-docs`) — wszystkie robią to samo
   dwuetapowo (resolve → docs). Priorytet:
   1. MCP `resolve-library-id` / `query-docs` (jeśli `context7` widoczny w `/mcp`) —
      zero kosztu procesu, preferowane.
   2. `npx ctx7@latest library/docs` — TYLKO gdy MCP niedostępne w sesji.
   Nie wywołuj obu ścieżek dla tego samego pytania.
7. **Zamknięcie fazy:** gdy faza jest zakończona i potwierdzona testami (razem
   z manualnymi), dokumentacja projektu aktualna — oznacz status [DONE], przenieś
   opis do CHANGELOG.md, zaktualizuj `domain_context` w
   `backend/app/services/mcp/router.py`.
8. **Delegacja zadań:** nie ma zadań delegowanych do agenta asynchronicznego (rewizja
   2026-07-13). Jeśli w starszej dokumentacji natrafisz na oznaczenie [JULES] — ignoruj.
9. **Aktualizacja Pamięci (Claude-Mem):** po zakończeniu istotnej fazy, przeprowadzeniu audytu kodu lub podjęciu ważnej decyzji architektonicznej/technicznej, wywołaj narzędzie MCP `observation_add` lub `observation_record_event`, aby zapisać zwięzły opis zmian i wniosków w pamięci persystentnej `claude-mem`.

## [ARCHITECTURE CONSTRAINTS]
* **Dual-Engine Pattern:** Logika musi zawsze posiadać fallback na darmowy `vectorbt`.
* **Data Layer:** Pobieranie danych (np. Yahoo) musi być izolowane i zapisywane do
  formatu Parquet przed przetworzeniem.
* **Frontend:** React + FastAPI.

---

## [PHASES & CURRENT STATE]
> Historia zakończonych faz (1-21): patrz `CHANGELOG.md`.

* **Phase 22: Refaktoryzacja Frontendu & Język Angielski jako Domyślny**
  * Status: [DONE]
  * Cel: Refaktor interfejsu użytkownika na język angielski jako domyślny. Zachowanie komentarzy deweloperskich. Aktualizacja testów frontendu oraz dokumentacji środowiskowej.

* **Phase 23: Poprawki Makefile, Czyszczenie UI oraz Motyw Ciemny Tearsheetu QuantStats**
  * Status: [DONE]
  * Cel: Usunięcie przycisków w nagłówku, przeniesienie czatu AI Analyst na kanwę, motyw ciemny QuantStats Tearsheet z angielskim szablonem i łącznikiem `-`, poprawienie komend Makefile.

* **Faza xx: Konteneryzacja, docker i docker compose**
  * Status: [PENDING]

---

## [DEVELOPMENT ENVIRONMENT & MAKEFILE COMMANDS]
Projekt wykorzystuje `uv` do zarządzania pakietami Python oraz `Makefile` do automatyzacji komend deweloperskich.

* **Uruchamianie aplikacji:**
  - Backend FastAPI: `make api` (uruchamia `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`)
  - Frontend Vite: `make frontend` (`cd frontend && npm run dev`) lub `make rebuild-front`
* **Testowanie:**
  - Testy backendu (Python/pytest): `make test` lub `uv run pytest backend/tests/ -v --tb=short`
  - Testy frontendu (Vitest): `cd frontend && npx vitest run` lub `npm test`
* **Jakość kodu i typowanie:**
  - Linter i sprawdzanie typów: `make lint` (`uv run ruff check backend/` oraz `cd frontend && npx tsc --noEmit`)
  - Generowanie typów API TypeScript z OpenAPI: `make generate-api`
* **Zarządzanie procesami i czyszczenie:**
  - Czyszczenie zasobów na porcie 8000: `make kill-api`
  - Czyszczenie pamięci podręcznej i plików tymczasowych: `make clean`
* **Zarządzanie pakietami Python:**
  - Wszystkie komendy Python i instalacje bibliotek wykonuj za pomocą `uv` (`uv run`, `uv pip`, `uv add`).

---

## Graphify

Graf wiedzy tego repo w `graphify-out/`. Skill globalny (`~/.gemini/config/skills/graphify/`)
wyzwala się sam dla pytań o architekturę — poniżej tylko projektowe doprecyzowanie:

- `graphify query "<pytanie>"`, `graphify path "<A>" "<B>"`, `graphify explain "<koncept>"`
  — preferuj nad surowym czytaniem plików, gdy `graphify-out/graph.json` istnieje.
- Brudne pliki `graphify-out/` po hookach są normalne — nie powód do pomijania.
- Po zmianach w kodzie: `graphify update .` (AST-only, zero kosztu API).

## Caveman

Rules:
- Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging
- Fragments OK. Short synonyms. Technical terms exact. Code unchanged.
- Pattern: [thing] [action] [reason]. [next step].
- Not: "Sure! I'd be happy to help you with that."
- Yes: "Bug in auth middleware. Fix:"

Switch level: /caveman lite|full|ultra|wenyan
Stop: "stop caveman" or "normal mode"

Auto-Clarity: drop caveman for security warnings, irreversible actions, user confused.
Resume after.

Boundaries: code/commits/PRs written normal.