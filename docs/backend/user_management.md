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

Gdy włączona zostanie opcja `auth_enabled = true` i baza danych nie zawiera żadnych kont, przy starcie aplikacji automatycznie tworzony jest domyślny administrator:

- **Login:** `ADMIN_USERNAME` (domyślnie: `admin`)
- **Hasło:** `ADMIN_PASSWORD` (domyślnie: `blockbt`)
