# Zarządzanie Użytkownikami, Autentykacja i Scoping Sesji (Faza 16)

Moduł zarządzania użytkownikami w BlockBT umożliwia obsługę wielu kont, uwierzytelnianie bezstanowe oparte o tokeny JWT (JSON Web Token), automatyczny scoping zapytań SQL oraz izolację zasobów w interfejsie użytkownika.

---

## Architektura i Opcjonalność

System został zaprojektowany w modelu **bezszwowej opcjonalności** (Seamless Optionality):

```
                     +---------------------------------------+
                     | Zapytanie HTTP z Frontendu / API Client |
                     +---------------------------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |           AuthMiddleware              |
                     +---------------------------------------+
                                   /           \
               auth_enabled == false           auth_enabled == true
                                 /               \
                                v                 v
               +-------------------+   +---------------------------+
               | Passthrough       |   | Sprawdzenie Bearer JWT    |
               | user_id = None    |   | -> Decoded user_id, role  |
               +-------------------+   +---------------------------+
                                \                 /
                                 v               v
                     +---------------------------------------+
                     |    Wykonanie Logiki / SQL Query       |
                     |  (scoped_query filtruje po user_id)   |
                     +---------------------------------------+
```

1. **Tryb Jednoosobowy (Domyślny, `auth_enabled = false`):**
   - Wszystkie zapytania HTTP są przepuszczane bez konieczności podawania tokenów.
   - Endpoint `/api/auth/me` zwraca profil domyślnego użytkownika lokalnego (`id=0, username="local", role="admin"`).
   - Baza danych nie wymusza filtrowania po użytkowniku (`user_id = None`).
   - `LoginPage.tsx` automatycznie przekierowuje na stronę główną `/`.
   - **Operacje uprzywilejowane wymagają loopbacku** (zmiana kontraktu, 2026-07-25) — patrz niżej.

### Granica zaufania w trybie bez logowania

Przy `auth_enabled = false` nie istnieją role, więc `require_admin` nie miał czego sprawdzać i przepuszczał wszystko. Otwierało to eskalację: dowolny klient z sieci lokalnej wykonywał `POST /api/auth/users` (rola `admin`), następnie `PUT /api/settings/ {auth_enabled: true}` — i właściciel instancji tracił dostęp do własnej maszyny.

Od 2026-07-25 granicą zaufania jest **adres klienta**:

| Endpointy | `auth_enabled = false` | `auth_enabled = true` |
|:--|:--|:--|
| `POST/PUT/DELETE /api/auth/users`, `GET /api/auth/users` | tylko `127.0.0.0/8` i `::1` | rola `admin` |
| `PUT /api/settings/` | tylko loopback | rola `admin` |
| `POST/PUT/DELETE /api/settings/prompts*` | tylko loopback | rola `admin` |

Wywołanie spoza loopbacku zwraca `403`. Odczyty (`GET /api/settings/`, `GET /api/settings/prompts`) pozostają otwarte jak dotąd.

**Skutek dla klientów:** przy wystawieniu API przez reverse proxy adresem klienta staje się proxy. Jeśli proxy działa na tej samej maszynie, operacje uprzywilejowane pozostaną dostępne dla całej sieci — w takiej konfiguracji należy włączyć `auth_enabled`.

**Skutek dla testów:** `TestClient` przedstawia się jako host `testclient`, który **nie** jest loopbackiem. Testy wywołujące operacje uprzywilejowane przy wyłączonym auth muszą tworzyć klienta jawnie: `TestClient(app, client=("127.0.0.1", 50000))`.

### Zasoby bez właściciela (`user_id IS NULL`)

Wiersze powstałe przed Fazą 16 nie mają `user_id`. Wcześniej `verify_resource_access` przepuszczał je bezwarunkowo, co udostępniało całą starą bazę każdemu zalogowanemu użytkownikowi. Obecnie przy włączonym auth widzi je **wyłącznie administrator**; migracja `0001_user_scoping` dodatkowo przypisuje je pierwszemu kontu o roli `admin`.

2. **Tryb Wieloużytkownikowy (`auth_enabled = true`):**
   - Flaga `auth_enabled` włączana jest w zakładce `User Management` w ustawieniach aplikacji (tabela `app_settings`).
   - Middleware wymaga poprawnego nagłówka `Authorization: Bearer <JWT_TOKEN>`.
   - Tworzenie strategii, backtestów i optymalizacji przypisuje `user_id` zalogowanego konta.
   - Odczyt zasobów w zapykaniach SQL jest filtrowany po `user_id`.

---

## Moduły Backendowe i Routery API

- **Model ORM (`app/models/user.py`):** Encja `User` (`id`, `username`, `password_hash`, `role`, `is_active`, `created_at`).
- **Serwis Auth (`app/services/auth.py`):** Szyfrowanie haseł `bcrypt`, generowanie tokenu JWT (`sub: str(user_id)`, ważność 24h).
- **Middleware (`app/core/auth_middleware.py`):** Przechwytywanie requestów, obsługa ścieżek publicznych.
- **Scoping zapytań (`app/core/user_scope.py`):**
  - `get_user_id(request: Request) -> int | None`: Wyciąga `user_id` z sesji.
  - `scoped_query(query, model, request: Request)`: Dokleja klauzulę `WHERE user_id = X`.
- **Routery Zmodyfikowane pod Scoping (`app/api/`):**
  - `strategies.py`: Zapis i odczyt strategii w oparciu o `user_id`.
  - `backtest.py`: Tworzenie `BacktestJob` z przypisanym `user_id` i filtrowanie listy jobów.
  - `optimizer.py`: Tworzenie `OptimizationJob` z przypisanym `user_id` i filtrowanie zapytań.
  - `auth.py`: Logowanie, rejestracja, zarządzanie użytkownikami, endpoint `/api/auth/auth-status`.

---

## Izolacja Stanu Interfejsu (Frontend)

- **Auth Store (`frontend/src/store/authStore.ts`):** Metody `login` oraz `logout` wywołują `useWorkflowStore.getState().clearCanvas()`.
- **Zapobieganie Wyciekom:** Przełączenie użytkownika natychmiastowo czyści paletę i węzły na kanwie Visual Buildera, uniemożliwiając wgląd w strategie poprzedniej sesji.
- **Dostępność Strategii:** Popup `StrategyListModal.tsx` po pobraniu listy z backendu prezentuje wyłącznie zapytania przypisane do zalogowanego konta.

---

## Endpointy API `/api/auth`

| Metoda | Ścieżka | Wymagana rola | Opis |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Publiczny | Logowanie użytkownika i zwrot tokena JWT |
| `GET` | `/api/auth/me` | Publiczny / Token | Pobiera dane zalogowanego użytkownika (lub domyślne `local` gdy auth wyłączony) |
| `GET` | `/api/auth/auth-status` | Publiczny | Sprawdza czy autentykacja jest włączona (`auth_enabled`) |
| `GET` | `/api/auth/users` | `admin` | Pobiera listę wszystkich użytkowników |
| `POST` | `/api/auth/users` | `admin` | Tworzy nowego użytkownika |
| `PUT` | `/api/auth/users/{id}` | `admin` | Edytuje dane, rolę lub status użytkownika |
| `DELETE` | `/api/auth/users/{id}` | `admin` | Usuwa konto użytkownika |

---

## Pierwsze Uruchomienie (Seeding Admina)

Gdy `auth_enabled = true`, a baza danych nie zawiera żadnych kont, automatycznie tworzony jest administrator:

- **Login:** `ADMIN_USERNAME` (domyślnie: `admin`)
- **Hasło:** `ADMIN_PASSWORD` — **bez wartości domyślnej**. Gdy zmienna nie jest ustawiona, hasło jest losowane (`secrets.token_urlsafe(16)`) i **jednorazowo** wypisywane do logu na poziomie `WARNING`. Nie da się go odczytać później — trzeba je zapisać przy pierwszym starcie albo zresetować konto. W `.env.example` wpis jest celowo zakomentowany; nigdy nie umieszczaj tam wartości przykładowej, bo trafi na wszystkie instalacje.

---

## Schemat Bazy i Migracje

`Base.metadata.create_all()` tworzy brakujące tabele, ale **nie wykonuje `ALTER TABLE`** — instalacja z bazą sprzed Fazy 16 kończyła się błędem `no such column: strategies.user_id`. Od 2026-07-25 start aplikacji (`lifespan` → `app.db.migrations.init_or_migrate_db()`) stosuje wzorzec **„stamp albo upgrade"**:

| Stan bazy | Działanie |
|:--|:--|
| pusta | `create_all()` + `alembic stamp head` |
| istniejąca | `alembic upgrade head`, potem `create_all()` dla tabel spoza migracji |

Stempel na świeżej bazie jest istotny: bez niego kolejna migracja próbowałaby odtworzyć całą historię na schemacie, który już wszystko ma, i **każda** przyszła migracja musiałaby być idempotentna.

Błąd migracji celowo przerywa start aplikacji — lepiej nie wstać niż działać na rozjechanym schemacie. Ręczne uruchomienie pozostaje dostępne przez `make migrate` (i `make migrate-down` dla cofnięcia jednej rewizji).

Seed uruchamia się w **dwóch** miejscach, co jest istotne dla poprawności:

1. `lifespan` przy starcie API,
2. `PUT /api/settings/` w momencie przestawienia `auth_enabled` na `true`.

Bez punktu (2) włączenie autentykacji na bazie bez użytkowników zamykało właściciela na zewnątrz aż do restartu procesu — każde żądanie kończyło się `401`, a konta nie było jak założyć. Wspólną implementacją jest `app.services.auth.ensure_admin_user()`.
