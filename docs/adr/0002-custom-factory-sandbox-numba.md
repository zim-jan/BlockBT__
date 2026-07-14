# ADR-0002: Custom Factory — sandbox AST + Numba JIT (Faza 11)

- **Status:** Zaakceptowany
- **Data:** 2026-07-14
- **Faza:** 11 — Custom Factory i Numba JIT (Filary 2 i 3)

## Kontekst

Cel Fazy 11 (roadmap `AGENTS.md`): „Własna matematyka. Prędkość C." Użytkownik ma
móc zdefiniować **własny wskaźnik** kodem Pythona w UI (węzeł Indicators, tryb
Custom Code) oraz programowo (`IndicatorService.compile_custom_indicator`).

Rodzi to dwa napięte wymagania:

1. **Bezpieczeństwo eval/exec.** Wykonanie dowolnego kodu użytkownika to klasyczna
   powierzchnia ataku. Aplikacja jest Self-Hosted / Air-Gapped — krytyczne jest
   zablokowanie dostępu do systemu plików (zapis/eksfiltracja), procesów, sieci
   i introspekcji ucieczkowej (`__globals__`, ramki wykonania).
2. **Prędkość.** Rdzeń liczbowy custom wskaźnika (pętle po tablicy) w czystym
   Pythonie jest wolny; potrzebna jest kompilacja do kodu maszynowego.

Test TDD (red) buduje fabrykę wskaźnika z przykładu pandasowego i wymaga sandboxa
odrzucającego niebezpieczny kod frazą „Unsafe code detected".

## Rozważane opcje

### Sandbox

#### A. Własny walidator AST allowlist (deny-by-default) — wybrana
Statyczna analiza AST: dozwolone tylko węzły z allowlisty (`_ALLOWED_AST_NODES`),
plus denylista nazw (`_FORBIDDEN_NAMES`) i atrybutów (`_FORBIDDEN_ATTRIBUTES`),
zamknięte `__builtins__` przy `exec`.

- **Zysk:** zero zależności zewnętrznych (ważne dla Air-Gapped/BYOL),
  deterministyczny, pełna kontrola, blokada importów „u źródła" (brak węzła
  `Import` w allowliście). Czytelny, audytowalny, testowalny.
- **Koszt:** denylista atrybutów to enumeracja — trzeba świadomie utrzymywać;
  ryzyko przeoczenia wektora.

#### B. RestrictedPython
Biblioteka Zope transformująca AST i podmieniająca dostęp do atrybutów.

- **Zysk:** dojrzała, gotowe guardy.
- **Koszt:** dodatkowa zależność, złożona semantyka (guard*), historia CVE,
  trudniejsza do w pełni deterministycznego zaudytowania pod nasz wąski kontrakt.

#### C. asteval
Interpreter minimalnego podzbioru Pythona.

- **Zysk:** izolacja przez własny interpreter (brak realnego `exec`).
- **Koszt:** własny model wykonania — kolizja z Numba `@njit` i natywnym
  `vectorbt` (potrzebujemy prawdziwych obiektów np/pd/vbt, nie interpretera);
  dodatkowa zależność, wolniejszy.

### JIT (kontrakt rdzenia)

- **numpy 1D-per-kolumna (wybrana):** funkcja usera 1D `np.ndarray → np.ndarray`,
  `@njit` na rdzeniu, wrapper `apply_func` mapuje per kolumnę na 2D z vbt.
- **pandas:** rdzeń operuje na `Series`/`DataFrame` — czytelny, ale niekompatybilny
  z `@njit` (Numba nie zna pandas), traci „Prędkość C".
- **hybryda:** wykrywanie typu wejścia i dwie ścieżki — nadmiarowa złożoność bez
  realnej korzyści na tym etapie.

## Decyzja

- **Sandbox = własny walidator AST** (opcja A): allowlista węzłów + denylista nazw
  + **denylista atrybutów** (dunder algorytmicznie, reszta enumeracją: ramki,
  `ctypes`/`tobytes`, serializatory `to_csv`/`tofile`/..., `system`/`popen`).
  `exec` z jawnie zamkniętym `__builtins__` (`_safe_builtins`). Bez zależności
  zewnętrznych. Naruszenie → `ValueError("Unsafe code detected: ...")`.
- **JIT = numba 1D-per-kolumna** (opcja numpy): kontrakt funkcji
  `np.ndarray(1D) → np.ndarray(1D)`, kompilacja `@njit` **leniwa** (pierwszy
  `.run()`), wektoryzacja po symbolach w `apply_func`, opakowanie w
  `vbt.IndicatorFactory`.

Ta sama walidacja utwardza również ścieżkę DAG `generate_custom`
(`indicatorType == "custom"`): walidacja AST + zamknięte `__builtins__` przed
`exec`; użytkownik definiuje `entries`/`exits` (dostępne: `close`, `vbt`, `np`, `pd`).

## Konsekwencje

**Pozytywne**

- Zero zależności zewnętrznych na sandbox — spójne z Air-Gapped/BYOL.
- Deterministyczny, audytowalny, w pełni pokryty testami (48 testów sandboxa).
- „Prędkość C" dla rdzenia liczbowego; prosty kontrakt 1D dla użytkownika,
  wektoryzacja po symbolach transparentna.
- Wiedza utrwalona w MCP `get_domain_context` (`core_engine`).

**Negatywne / ryzyko rezydualne**

- **Denylista atrybutów to enumeracja** — nowy wektor ucieczki (np. nieznany
  atrybut zapisu/introspekcji) wymaga ręcznego dopisania. Mityguje to
  deny-by-default na węzłach i nazwach oraz zamknięte `__builtins__`, ale nie jest
  to dowód formalny.
- **`vectorbt` ma dużą powierzchnię** — udostępniamy realny `vbt`, więc metody
  biblioteki (poza naszą kontrolą AST) mogą teoretycznie eksponować niepożądane
  operacje. Air-Gap ogranicza skutki, lecz to świadomy kompromis użyteczność↔ryzyko.
- Kompilacja njit leniwa — pierwszy `.run()` ponosi koszt kompilacji (zimny start).

## Powiązania

- Poradnik użytkownika: [Pisanie własnych wskaźników](../frontend/custom_indicators.md).
- Kod: `backend/app/services/engine/indicators.py`
  (`_validate_code_safety`, `compile_custom_indicator`, `generate_custom`).
