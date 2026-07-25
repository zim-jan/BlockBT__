# ADR-0011: Loopback jako granica zaufania przy wyłączonej autentykacji

- **Status:** zaakceptowana
- **Data:** 2026-07-25
- **Powiązane:** [ADR-0010](0010-zarzadzanie-uzytkownikami-auth-jwt.md), `backend/tests/test_api/test_auth_p0.py`

## Kontekst i problem

ADR-0010 wprowadził **bezszwową opcjonalność** autentykacji: przy `auth_enabled = false` middleware przepuszcza cały ruch, ustawiając `request.state.user_id = None` i `user_role = None`. Helper `require_admin` interpretował brak roli jako „auth wyłączony, nie ma czego sprawdzać" i wychodził przez `return`.

Skutek: przy wyłączonej autentykacji **nikt niczego nie chronił**, a API nasłuchuje nie tylko na loopbacku (`docker-compose`, `--host 0.0.0.0`, reverse proxy). Dowolny klient z sieci lokalnej mógł wykonać:

1. `POST /api/auth/users` z rolą `admin` — założyć sobie konto,
2. `PUT /api/settings/ {auth_enabled: true}` — włączyć autentykację,

po czym właściciel instancji tracił dostęp do własnej maszyny, bo nie znał żadnych poświadczeń. Finding potwierdzony empirycznie na uruchomionej instancji (review pod PR #5).

Naiwna naprawa — odrzucanie żądań przy `user_role is None` — jest niewykonalna: przy wyłączonym auth nikt nie mógłby zmienić ustawień, **w tym włączyć autentykacji**. Klasyczne jajko i kura.

## Rozważane opcje

### (A) Autentykacja zawsze włączona
- **Zysk:** jedna ścieżka wykonania, brak trybu specjalnego.
- **Koszt:** największa zmiana produktowa, sprzeczna z filozofią Air-Gapped z ADR-0010; ~20 testów do przejścia; uruchomienie „od zera" wymaga konfiguracji konta.

### (B) Token bootstrap wypisywany do logu
- **Zysk:** działa niezależnie od topologii sieci.
- **Koszt:** nowe pojęcie w kontrakcie API, front musi go nosić przy każdym żądaniu uprzywilejowanym, token trzeba unieważniać i rotować.

### (C) Ograniczenie operacji uprzywilejowanych do loopbacku (wybrana)
- Przy `auth_enabled = false` `require_admin` przepuszcza wyłącznie żądania z `127.0.0.0/8` i `::1`; pozostałe dostają `403`.
- Przy `auth_enabled = true` bez zmian — decyduje rola `admin` z tokenu JWT.

## Decyzja

Wybieramy **(C)**. Granicą zaufania w trybie bez logowania jest adres klienta: właściciel maszyny robi na niej co chce, ale sieć lokalna nie ma dostępu do operacji administracyjnych. Tryb lokalny działa dalej bez żadnej konfiguracji, a ścieżka „włącz auth" pozostaje otwarta dla właściciela.

Uzupełniająco, żeby (C) było domknięte:

- **Anti-lockout:** włączenie `auth_enabled` przez `PUT /api/settings/` seeduje pierwszego admina (`ensure_admin_user`), a nie dopiero restart procesu. Bez tego decyzja (C) prowadziłaby do instancji z włączonym auth i zerem kont.
- **Zasoby bez właściciela:** `user_id IS NULL` widzi wyłącznie admin — inaczej scoping po Fazie 16 nie obejmuje wierszy powstałych wcześniej.

## Konsekwencje

### Pozytywne
- Eskalacja opisana w kontekście przestaje działać, bez zmiany modelu produktu.
- Zero konfiguracji dla dewelopera na localhoście — dokładnie jak dotąd.

### Negatywne / do pilnowania
- **Reverse proxy na tej samej maszynie** przedstawia się jako loopback, więc przywraca poprzednią dziurę dla całej sieci. W takiej topologii `auth_enabled` musi być włączony. Świadomie **nie** ufamy nagłówkom `X-Forwarded-For` — są trywialne do podrobienia, a zaufanie do nich wymaga konfiguracji listy proxy, której BlockBT nie ma.
- **Testy:** `TestClient` przedstawia się jako host `testclient`, który nie jest loopbackiem. Testy operacji uprzywilejowanych przy wyłączonym auth muszą jawnie podać adres: `TestClient(app, client=("127.0.0.1", 50000))`.
- **Zmiana kontraktu API** — klient zdalny, który dotąd dostawał `200` na `PUT /api/settings/`, dostanie `403`. Odnotowane w `CHANGELOG.md` i `docs/backend/user_management.md`.

## Implementacja

| Element | Lokalizacja |
|:--|:--|
| `is_loopback()`, `require_admin()`, `verify_resource_access()` | `backend/app/core/user_scope.py` |
| `ensure_admin_user()` — wspólny seed admina | `backend/app/services/auth.py` |
| Anti-lockout przy włączaniu auth | `backend/app/api/settings.py` |
| Testy regresyjne (jeden na finding) | `backend/tests/test_api/test_auth_p0.py` |
