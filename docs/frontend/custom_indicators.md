# Pisanie własnych wskaźników

Poradnik trybu **Custom Code** w węźle Indicators oraz kompilacji wskaźnika
własnego przez `compile_custom_indicator` (Faza 11: Custom Factory + Numba JIT).

## Po co własne wskaźniki

Wbudowane węzły (SMA crossover, MACD, RSI) pokrywają typowe strategie. Custom
wskaźniki pozwalają:

- zdefiniować **własną matematykę** sygnału (oscylatory, filtry, autorskie reguły),
- prototypować logikę, dla której nie ma gotowego węzła,
- policzyć rdzeń liczbowy z **prędkością C** (kompilacja Numba `@njit`).

Kod użytkownika przechodzi **statyczną walidację AST** (deny-by-default) blokującą
importy, `eval`/`exec` i dostęp do dunderów.

!!! warning "To NIE jest twarda granica bezpieczeństwa"
    Walidator to warstwa higieny kodu (defense-in-depth), a nie pełny sandbox.
    Udostępniamy realne moduły `np`/`pd`/`vbt`, więc zdeterminowany kod może obejść
    denylistę (np. odczyt/zapis pliku przez mniej znane funkcje numpy/pandas,
    `pd.read_pickle` = potencjalne RCE). Aplikacja jest **lokalna i jednoosobowa** —
    piszesz własny kod na własnej maszynie, więc w normalnym użyciu to bezpieczne.
    **Nie uruchamiaj jednak wskaźników/strategii importowanych z niezaufanych
    źródeł.** Szczegóły i model zagrożeń: [ADR-0002](../adr/0002-custom-factory-sandbox-numba.md).

## Tryb Custom Code w węźle Indicators

W węźle Indicators wybierz tryb **Custom Code**. Pojawi się textarea na kod.

**Kontrakt:** kod ma zdefiniować dwie zmienne — `entries` i `exits` (wektory/serie
booli: wejście i wyjście z pozycji). Brak którejkolwiek → błąd walidacji.

Dostępne nazwy w przestrzeni wykonania:

| Nazwa   | Znaczenie                                   |
|---------|---------------------------------------------|
| `close` | seria/macierz cen zamknięcia (single lub multi-symbol) |
| `vbt`   | `vectorbt` (metody `.vbt.*`, `vbt.MA.run`, ...) |
| `np`    | NumPy                                       |
| `pd`    | pandas                                      |

Przykład (kod w textarea węzła):

```python
fast = vbt.MA.run(close, window=10).ma
slow = vbt.MA.run(close, window=30).ma
entries = fast.vbt.crossed_above(slow)
exits = fast.vbt.crossed_below(slow)
```

Błąd walidacji (np. „Unsafe code detected: ...") jest pokazywany w węźle
(`data.error`).

## Sandbox — co wolno, a czego nie

Walidator statycznie analizuje AST kodu **przed** wykonaniem. Model: dozwolone są
tylko jawnie dopuszczone konstrukcje; wszystko inne jest odrzucane.

### Wolno

- arytmetyka i porównania (`+ - * / // % **`, `< <= > >= == !=`, `and or not`),
- przypisania, `if`/`for`/`while`, `break`/`continue`, wyrażenia listowe,
- funkcje pomocnicze: `abs min max len range enumerate zip sum round sorted ...`,
- NumPy: `np.mean`, `np.where`, indeksowanie tablic, pętle po `range(...)`,
- pandas / vectorbt: `.rolling(...).mean()`, `.vbt.crossed_above(...)` itd.

### Nie wolno (→ `ValueError: "Unsafe code detected: ..."`)

- **importy** (`import ...`, `from ... import ...`) — całkowicie zablokowane,
- nazwy systemowe / ucieczkowe: `os`, `sys`, `subprocess`, `socket`, `ctypes`,
  `eval`, `exec`, `compile`, `open`, `__import__`, `getattr`, `setattr`,
  `globals`, `locals`, `input`, ...,
- dostęp do atrybutów **dunder** (`__class__`, `__globals__`, `__dict__`, ...),
- introspekcja ramek: `gi_frame`, `f_globals`, `f_back`, ...,
- surowa pamięć / interfejs C: `ctypes`, `tobytes`, `getbuffer`, `setflags`,
- **zapis na dysk**: `tofile`, `save`, `to_csv`, `to_parquet`, `to_pickle`,
  `to_json`, ... (krytyczne w trybie Air-Gapped),
- wykonanie procesów / serializacja: `system`, `popen`, `spawn`, `dump`, `dumps`.

Złamanie którejkolwiek reguły przerywa kompilację komunikatem
`Unsafe code detected: ...` z nazwą naruszenia.

## `compile_custom_indicator` + Numba JIT

Ścieżka programowa (`IndicatorService.compile_custom_indicator(code)`) buduje
z kodu użytkownika pełną klasę wskaźnika `vbt.IndicatorFactory` z metodą `.run()`.

**Kontrakt funkcji rdzenia:** kod definiuje funkcję, która przyjmuje
**1-wymiarową** tablicę NumPy (`close`) i zwraca **1-wymiarową** tablicę.
Jeśli zdefiniujesz kilka funkcji, rdzeniem wskaźnika jest **pierwsza** funkcja
najwyższego poziomu (kolejne traktowane są jako pomocnicze). Wrapper
(`apply_func`) mapuje ją per kolumnę na realny 2D z vectorbt — dzięki temu piszesz
prostą funkcję jednowymiarową, a **wektoryzacja po symbolach** dzieje się
automatycznie.

- **Prędkość C:** rdzeń jest kompilowany `@njit` (Numba).
- **Leniwa kompilacja:** njit odpala się przy **pierwszym** `.run()`, nie przy
  budowie fabryki (samo zbudowanie nie wymaga pełnej numba-zgodności).

### Przykład poprawny (rolling mean pętlą NumPy)

```python
def rolling_mean(close):
    n = 3
    out = np.empty_like(close)
    for i in range(len(close)):
        if i < n - 1:
            out[i] = np.nan
        else:
            s = 0.0
            for j in range(i - n + 1, i + 1):
                s += close[j]
            out[i] = s / n
    return out
```

`compile_custom_indicator(code)` zwróci klasę z `.run(close)` — pierwsze
wywołanie skompiluje rdzeń przez Numba.

### Przykład odrzucony (import)

```python
import os                     # ← Unsafe code detected: niedozwolona konstrukcja 'Import'.
def bad(close):
    return close
```

Walidator odrzuci kod na etapie AST, zanim cokolwiek się wykona.
