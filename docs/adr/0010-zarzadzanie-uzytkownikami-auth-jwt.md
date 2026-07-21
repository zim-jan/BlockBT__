# ADR-0010: Zarządzanie użytkownikami, uwierzytelnianie JWT i izolacja sesji

- **Status:** zaakceptowana
- **Data:** 2026-07-21

## Kontekst i problem

Dotychczas BlockBT działał w trybie jednoosobowym (Air-Gapped Single-User) — brak autentykacji, wszystkie zasoby (strategie, joby backtestowe, optymalizacje) w bazie były globalne i dostępne dla każdego wywołania REST API.

Dla zastosowań wieloużytkownikowych (Multi-Tenant / Self-Hosted) wymagany był mechanizm pozwalający na:
1. Rejestrację/logowanie użytkowników z bezpiecznym przechowywaniem haseł.
2. Wydawanie bezstanowych tokenów sesyjnych.
3. Przypisywanie utworzonych zasobów (`strategies`, `backtest_jobs`, `optimization_jobs`) do konkretnego `user_id`.
4. Izolację danych pomiędzy użytkownikami na poziomie zapytania SQL (`WHERE user_id = X`).
5. Zachowanie **100% kompatybilności wstecznej** z lokalnym trybem jednoosobowym, gdy autentykacja jest wyłączona (`auth_enabled = false`).
6. Izolację stanu interfejsu (płótna Visual Builder) przy przełączaniu / wylogowywaniu użytkowników.

## Rozważane opcje

### (A) Obowiązkowy system Auth (brak opcji wyłączenia)
- **Zysk:** Jedna ścieżka wykonania w kodzie.
- **Koszt:** Naruszenie filozofii Air-Gapped i prostoty uruchomienia bez konfiguracji kont w środowisku lokalnym deweloperskim.

### (B) Warunkowy Middleware JWT z opcjonalnością, scopingiem SQL i czyszczeniem płótna (wybrana)
- Uwierzytelnianie włączane flagą `auth_enabled` w encji `AppSetting` (baza danych / UI Settings).
- Bezstanowe tokeny JWT (`PyJWT`, `HS256`, ważność 24h) z rolami `admin` i `user`.
- Haszowanie haseł algorytmem `bcrypt`.
- W trybie `auth_enabled = false` middleware przepuszcza cały ruch bez weryfikacji tokenów (`request.state.user_id = None`), endpoint `/api/auth/me` zwraca profil domyślnego usera lokalnego (`id=0, username="local", role="admin"`), a zapytania zwracają wszystkie rekordy (zero barier dla lokalnego dev-a).
- W trybie `auth_enabled = true` middleware weryfikuje nagłówek `Authorization: Bearer <token>`, a routery API (`strategies.py`, `backtest.py`, `optimizer.py`) zapisują `user_id = get_user_id(request)` oraz filtrują dane przy użyciu helpera `scoped_query`.
- Zapewnienie izolacji frontendowej w `authStore.ts` poprzez wywołanie `clearCanvas()` przy logowaniu/wylogowaniu.

## Decyzja

Wybrano **Opcję (B)**.

### Szczęśliwy przebieg i detale implementacji:
1. **Model `User` (`app/models/user.py`):**
   Tabela `users` (`id`, `username` UNIQUE, `password_hash`, `role`, `is_active`, `created_at`).
2. **Klucze obce (`app/models/orm.py`):**
   Dodano `user_id` FK (nullable) do tabel `strategies`, `backtest_jobs`, `optimization_jobs`.
3. **Pobieranie i filtrowanie w routerach API (`app/api/`):**
   - `strategies.py`, `backtest.py`, `optimizer.py`: endpointy `POST` zapisują `user_id=get_user_id(request)`.
   - Endpointy `GET` (listy i pojedyncze rekordy) stosują `scoped_query(select(...), Model, request)` oraz sprawdzają uprawnienia dostępu.
4. **Middleware (`app/core/auth_middleware.py`):**
   Przechwytuje requesty HTTP. Pomija ścieżki publiczne (`/api/health`, `/api/auth/login`, `/api/auth/auth-status`, `/docs`).
5. **Seeding pierwszego Admina (`app/main.py`):**
   Gdy auth jest włączony i baza nie zawiera użytkowników, system generuje domyślne konto administratora z konfiguracji (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
6. **Frontend Guard & Routing (`App.tsx`, `ProtectedRoute.tsx`, `LoginPage.tsx`):**
   - Komponent `ProtectedRoute` sprawdza publiczny endpoint `/api/auth/auth-status`. Jeśli auth jest włączony i brak tokena — automatyczne przekierowanie do `LoginPage.tsx`.
   - `LoginPage.tsx` weryfikuje status — jeśli auth jest wyłączony, przekierowuje bezszwowo na stronę główną `/`.
7. **Panel Zarządzania w UI (`SettingsPage.tsx`):**
   Przebudowano układ na spójny design system MD3 oparty na kartach i zakładkach (`Database`, `Bot`, `Users`).
8. **Izolacja Płótna (`authStore.ts`):**
   Metody `login` oraz `logout` wywołują `useWorkflowStore.getState().clearCanvas()`, uniemożliwiając wyciek węzłów i wyników strategii między różnymi kontami.

## Konsekwencje

- **Zero regresji:** Suita 248 testów przechodzi pomyślnie.
- **Bezpieczeństwo:** Hasła szyfrowane bcrypt-em z solą, tokeny JWT podpisywane kluczem `SECRET_KEY`.
- **Izolacja danych:** Każdy zalogowany użytkownik posiada odseparowany widok własnych strategii i wyników backtestów.

## Powiązania

- Kod backend: `backend/app/models/user.py`, `backend/app/services/auth.py`, `backend/app/core/auth_middleware.py`, `backend/app/core/user_scope.py`, `backend/app/api/auth.py`, `backend/app/api/strategies.py`, `backend/app/api/backtest.py`, `backend/app/api/optimizer.py`.
- Kod frontend: `frontend/src/store/authStore.ts`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/pages/SettingsPage.tsx`.
- Testy: `backend/tests/test_api/test_auth_api.py`.
