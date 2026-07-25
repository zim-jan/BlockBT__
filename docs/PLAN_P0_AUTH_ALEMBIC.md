# Plan: naprawa P0 warstwy auth + migracje Alembic

**Status:** zaplanowane, **kod nie zaczęty** · **Data:** 2026-07-25 · **Gałąź docelowa:** `fix/auth-p0-and-alembic` (utworzona, pusta)

Blokery merge'a `przydan-dev` → `main`. Findingi pochodzą z review Jana pod PR #5 (potwierdzone empirycznie na uruchomionej instancji) i zostały ponownie zweryfikowane w kodzie 2026-07-25.

---

## Decyzja projektowa (podjęta, nie zmieniać bez powodu)

**P0-1 rozwiązujemy przez ograniczenie do loopbacku.** Naiwna naprawa (odrzucanie żądań bez roli) zabiłaby tryb bez logowania — przy `auth_enabled=false` nikt nie mógłby zmienić ustawień, w tym włączyć auth. Jajko i kura.

Odrzucone alternatywy: token bootstrap w logu (nowe pojęcie w API, front musi go nosić), auth zawsze włączony (największa zmiana produktowa, ~20 testów do przejścia).

---

## Findingi z lokalizacją w kodzie

| ID | Plik | Problem |
|:--|:--|:--|
| **P0-1** | `backend/app/core/user_scope.py:24` | `require_admin` wychodzi przez `return`, gdy `user_role is None` — przy wyłączonym auth nie chroni niczego. Atak: `POST /api/auth/users` z rolą `admin` → `PUT /api/settings/ {auth_enabled: true}` → właściciel zablokowany |
| **P0-1b** | `backend/app/main.py:58` | seed admina dzieje się **tylko** w `lifespan` — włączenie auth na bazie bez użytkowników daje 401 na wszystkim do restartu procesu |
| **P0-2** | `backend/app/api/backtest.py:222` | `db.get(Strategy, ...)` bez sprawdzenia właściciela, a `:231` bezwarunkowo nadpisuje `strategy.parameters`. Ten sam wzorzec w `backend/app/api/optimizer.py:52` i `:112` |
| **P0-3** | `backend/app/core/user_scope.py:41` | `if resource_user_id is not None and resource_user_id != user_id` — przepuszcza wszystko z `user_id IS NULL`, czyli całą bazę powstałą przed Fazą 16 |
| **P1-1** | `backend/app/core/auth_middleware.py:21` | `except Exception: return False` — dowolny błąd SQLite (np. `database is locked`) wyłącza autoryzację. Ma być fail-closed |
| **P1-2** | `backend/app/api/settings.py:64,84,100,120` | CRUD `SystemPrompt` bez `require_admin` — każdy zalogowany podmienia globalny prompt AI (wektor prompt injection) |
| **P1-3** | `backend/app/core/config.py:45` | `ADMIN_PASSWORD: str = "blockbt"` jako domyślne, bez wymuszenia zmiany |
| **P1-4** | `backend/app/main.py:128` | `log_requests` czyta i loguje **body każdego żądania** — hasła z `/api/auth/login` lądują plaintextem w `backend/data/logs` |
| **P1-5** | `backend/app/api/auth.py:22` | `/api/auth/login` bez rate limitingu |
| **P1-6** | `alembic.ini:4` | `script_location = src/blockbt/db/migrations` — katalog nie istnieje (relikt starej struktury). Brak jakichkolwiek migracji, `create_all()` nie robi `ALTER TABLE`, więc każdy z istniejącym `blockbt.db` sprzed Fazy 16 dostaje `no such column: strategies.user_id` |

---

## Zakres wdrożenia

### 1. Alembic (nowy moduł)

- `alembic.ini`: `script_location = backend/alembic`, usunąć zaszyte `sqlalchemy.url`
- `backend/alembic/env.py` — URL bazy rozwiązywać **tak samo jak `backend/app/db/session.py`**: priorytet `BLOCKBT_DB_PATH`, potem `BLOCKBT_DB_URL`/`DATABASE_URL`, na końcu `backend/data/db/blockbt.db`
- `backend/alembic/versions/0001_user_scoping.py` — **idempotentna**: przez `sa.inspect()` dodaje `users` (jeśli brak) oraz kolumny `user_id` w `strategies`, `backtest_jobs`, `optimization_jobs`, `notes` (te cztery modele mają `user_id`; `chat_messages`, `system_prompts`, `app_settings` nie mają). Na końcu **backfill**: wiersze z `user_id IS NULL` przypisać pierwszemu użytkownikowi o roli `admin`, jeśli taki istnieje
- `create_all()` w `lifespan` zostaje dla świeżych instalacji — migracja musi być bezpieczna do uruchomienia na bazie już utworzonej przez `create_all`
- `Makefile`: cel `migrate` (`uv run alembic upgrade head`)

### 2. Hardening auth

- `user_scope.py`: helper `_is_loopback(request)` (`127.0.0.1`, `::1`); `require_admin` → gdy `role is None` wymaga loopbacku, inaczej 403; `verify_resource_access` → przy włączonym auth `resource_user_id is None` dostępne **tylko dla admina**
- `auth_middleware.py`: `is_auth_enabled` fail-closed — logować wyjątek i zwracać `True`
- `backtest.py`, `optimizer.py` (2 miejsca): `verify_resource_access(strategy, request)` bezpośrednio po `db.get`
- `settings.py`: `require_admin(request)` w czterech endpointach promptów (dodać parametr `request: Request`); w `update_settings` anti-lockout — przy włączaniu auth na bazie bez użytkowników zaseedować admina (wydzielić funkcję współdzieloną z `main.py`)
- `config.py`: `ADMIN_PASSWORD: str | None = None`; przy seedowaniu, gdy brak wartości, wygenerować `secrets.token_urlsafe(16)` i **jednorazowo** wypisać do logu
- `main.py`: `log_requests` przestaje czytać i logować body (zostają metoda, ścieżka, status, czas, query params)
- `auth.py`: prosty rate limiting w pamięci na `/api/auth/login` (np. 5 prób / 60 s na parę IP+username → 429), bez nowych zależności

### 3. Testy regresyjne (`backend/tests/test_api/`)

Po jednym na każdy finding — wszystkie są odtwarzalne:

- `require_admin`: auth off + klient **nie**-loopback → 403 na `POST /api/auth/users` i `PUT /api/settings/`; auth off + loopback → 200 (zachowanie trybu lokalnego); auth on + rola `user` → 403
- `verify_resource_access`: zasób z `user_id IS NULL` → 403 dla zwykłego użytkownika, 200 dla admina
- `POST /api/backtest/dag` na cudzą strategię → 403 **oraz** `strategy.parameters` bez zmian
- `POST /api/optimizer/*` na cudzą strategię → 403 (dwa endpointy)
- CRUD promptów wymaga admina
- `is_auth_enabled` fail-closed: podmienić `get_session` na rzucający → `True`
- rate limiting: N+1 próba logowania → 429
- migracja idempotentna: dwa przebiegi na tymczasowej bazie bez błędu

**Pułapka:** `TestClient` ustawia host klienta na `testclient`, więc `_is_loopback` będzie fałszywe i **istniejące testy uderzające w endpointy uprzywilejowane przy auth off zaczną dostawać 403**. Host podaje się przez `TestClient(app, client=("127.0.0.1", 50000))` — trzeba przejść istniejące testy (`test_auth_api.py`, `test_settings*`) i jawnie zdecydować, które symulują loopback, a które LAN.

---

## Kryteria ukończenia

- `uv run pytest backend/tests/` zielone (baza: **258 passed**, 2 deselected)
- `uv run ruff check backend/ --ignore E501` czysto
- każdy finding P0/P1 ma test, który **czerwieni się** na kodzie przed naprawą
- `alembic upgrade head` przechodzi na: świeżej bazie, bazie z `create_all` po Fazie 16, bazie sprzed Fazy 16 (bez `user_id`)
- `docs/` i `CHANGELOG.md` odnotowują zmianę kontraktu (loopback dla operacji uprzywilejowanych przy wyłączonym auth)
