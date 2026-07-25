# Strategie demonstracyjne — zestaw do zrzutów ekranu

**Cel:** gotowe konfiguracje pokazujące możliwości BlockBT, z konkretnymi parametrami do wpisania i opisem, co dana strategia demonstruje. Kolejność jest zaplanowana tak, by kolejne strategie budować przez modyfikację poprzedniej, a nie od zera.

**Data:** 2026-07-25 · Parametry zweryfikowane względem formularzy `InspectorPanel.tsx` i schematów `backend/app/schemas/`.

---

## 0. Przygotowanie sesji

```bash
make api                        # terminal 1
cd frontend && npm run dev      # terminal 2
```

**Konektor danych** — wybór ma znaczenie dla wiarygodności demonstracji:

| Konektor | Kiedy używać na zrzutach |
|:--|:--|
| `yahoo` | domyślny, realne dane rynkowe — najlepszy do zrzutów wyników i tearsheetu |
| `synthetic` | **tryb offline** — działa bez internetu, deterministyczny. Warto pokazać osobno jako dowód działania w trybie air-gapped (BYOL) |
| `alpaca` | wymaga kluczy API w `.env`; pomiń, jeśli ich nie masz |

**Ograniczenia danych intraday** (walidacja w konektorze Yahoo): dla `5m`/`15m`/`30m` dostawca oddaje ~60 dni historii, dla `1h` ~730 dni. Zakres dat dłuższy niż limit zwróci błąd walidacji — to zresztą dobry zrzut pokazujący czytelne komunikaty błędów.

**Dostępne wartości pól** (pełna lista z formularzy):

- Interwały: `5m`, `15m`, `30m`, `1h`, `1d`, `1w`
- Wskaźniki: `sma_crossover`, `macd`, `rsi`, `custom`
- Wielkość pozycji (`size_type`): `amount`, `percent`, `value`
- Metryka optymalizacji: `Total Return [%]`, `Sharpe Ratio`, `Max Drawdown [%]`, `Win Rate [%]`
- Okno WFO: `anchored`, `rolling`
- Alokacja kapitału: `distribution`, `mapping`, `ranking`

---

## S1. Baza — SMA crossover na jednym instrumencie

**Demonstruje:** kompletny przepływ DAG (dane → wskaźnik → sygnał → portfel), tearsheet, metryki KPI w nagłówku, zapis strategii.

| Węzeł | Parametr | Wartość |
|:--|:--|:--|
| Data Source | symbol | `AAPL` |
| | timeframe | `1d` |
| | dataSource | `yahoo` |
| | startDate / endDate | `2023-01-01` / `2025-01-01` |
| | point_in_time_enforcement | włączone |
| Indicator | indicatorType | `sma_crossover` |
| | smaFast / smaSlow | `10` / `30` |
| Signal | signalType | `sma_crossover` |
| | (bez dodatkowych pól) | przesunięcie sygnałów wymusza silnik, nie użytkownik — patrz uwaga niżej |
| Portfolio | init_cash | `10000` |
| | fees / slippage | `0.001` / `0.001` |
| | size_type | `amount` |

**Wynik uzyskany na tej konfiguracji:** Total Return **+22,85%**, Sharpe **0,91**, Max Drawdown **−18,19%**, Win Rate **44,4%**, 9 transakcji, kapitał końcowy 12 285 zł.

**Co złapać:** kanwa z czterema połączonymi węzłami · karty KPI w nagłówku po wykonaniu · modal wyników z tabelą metryk · panel notatek przy jobie.

> **Argument metodologiczny do slajdu — mocniejszy, niż widać w interfejsie.** Zabezpieczenia przed look-ahead bias nie da się w BlockBT wyłączyć ani źle ustawić, bo nie jest parametrem. Silnik stosuje `fshift(1)` na sygnałach wejścia i wyjścia **bezwarunkowo**, w obu ścieżkach wykonania — DAG (`opensource_engine.py:170`) i klasycznej (`:443`) — zgodnie z **ADR-0007**. W węźle sygnału nie ma i nie powinno być pola do jego konfiguracji.
>
> Drugi, niezależny mechanizm **jest** widoczny w formularzu i warto go pokazać: `point_in_time_enforcement` w węźle danych (domyślnie włączone, `schemas/dag.py:22`).
>
> Zdanie na slajd: *„platforma nie pozwala policzyć backtestu obciążonego look-ahead bias — przesunięcie sygnału o jedną świecę jest wymuszone w silniku, nie zależy od konfiguracji użytkownika"*.

---

## S2. Multi-symbol — broadcasting i metryki per ticker

**Demonstruje:** Fazę 10 (broadcasting wielowymiarowy), metryki liczone osobno dla każdego tickera, kolumnę Return z wartościami rozdzielonymi na instrumenty.

Modyfikacja S1: w węźle Data Source podaj **listę** symboli.

| Parametr | Wartość |
|:--|:--|
| symbol | `AAPL, GOOG` |
| endDate | `2026-01-01` (dłuższy zakres wyostrza różnicę między instrumentami) |

**Wynik uzyskany:** AAPL **+24,53%** (Sharpe 0,64, DD −28,87%, 13 transakcji) · GOOG **+138,09%** (Sharpe 1,61, DD −20,93%, 9 transakcji).

**Co złapać:** lista jobów na Dashboardzie — kolumna Symbol pokazuje `AAPL, GOOG`, kolumna Return dwie wartości `24.53% / 138.09%` w kolorach zależnych od znaku · modal wyników z metrykami per ticker.

> Kontrast 24% vs 138% na tym samym zestawie reguł to mocny argument prezentacyjny: pokazuje, że silnik liczy każdy instrument niezależnie, a nie usrednia.

---

## S3. Zarządzanie ryzykiem — stop loss, take profit, wielkość pozycji

**Demonstruje:** Fazę 12 (zaawansowane zarządzanie ryzykiem portfela), wpływ ograniczeń ryzyka na liczbę transakcji.

Modyfikacja S1: interwał intraday plus parametry ryzyka.

| Węzeł | Parametr | Wartość |
|:--|:--|:--|
| Data Source | timeframe | `1h` |
| | startDate / endDate | `2025-01-01` / `2026-07-01` |
| Portfolio | init_cash | `100000` |
| | sl_stop | `0.02` (2% stop loss) |
| | tp_stop | `0.05` (5% take profit) |
| | size / size_type | `99` / `amount` |
| Indicator | smaFast / smaSlow | `15` / `25` |

**Wynik uzyskany:** Total Return **+2,33%**, Sharpe **0,86**, Max Drawdown **−4,23%**, **54 transakcje**.

**Co złapać:** panel Inspector z wypełnionymi polami ryzyka · zestawienie z S1 — 54 transakcje kontra 9 i drawdown −4,2% kontra −18,2%.

> Najlepszy zrzut porównawczy w całym zestawie: te same reguły wejścia, a profil ryzyka zupełnie inny. Na drugi przebieg zamiast trailing stopa (nie ma go w formularzu — patrz sekcja o ograniczeniach) zmień `size_type` na `percent` i pokaż wpływ sposobu określania wielkości pozycji.

---

## S4. Inne wskaźniki — MACD i RSI

**Demonstruje:** że silnik nie jest zaszyty pod jedną strategię; rejestr wskaźników (158 z TA-Lib plus wskaźniki vectorbt).

**Wariant MACD** — modyfikacja S1:

| Parametr | Wartość |
|:--|:--|
| indicatorType | `macd` |
| macdFast / macdSlow / macdSignal | `12` / `26` / `9` |

**Wariant RSI** — modyfikacja S1:

| Parametr | Wartość |
|:--|:--|
| indicatorType | `rsi` (w liście: *RSI Oscillator*) |
| rsiWindow | `14` |
| rsiLower | `30` (poziom wyprzedania) |
| rsiUpper | `70` (poziom wykupienia) |

**Co złapać:** panel Inspector przy zmianie typu wskaźnika — formularz przebudowuje pola pod wybrany wskaźnik.

---

## S4b. Wskaźniki z rejestru — formularz generowany z introspekcji

**Demonstruje:** Fazę 14 (dynamiczna introspekcja), i to jest jedna z najmocniejszych rzeczy w całym interfejsie.

W liście *Indicator Type* poniżej czterech pozycji wbudowanych jest grupa **`Registry Indicators (Introspection)`** zasilana z `GET /api/indicators/`. `InspectorPanel` **generuje pola formularza z metadanych wskaźnika** — nazwa parametru, typ (`int`/`float`/tekst) i wartość domyślna (`InspectorPanel.tsx:359-368`).

**Stan na 2026-07-25: rejestr zawiera tylko dwa wpisy — `vbt_MA` (window 10) i `vbt_RSI` (window 14).** `discover_talib_indicators` (`indicator_registry.py:71`) iteruje po 158 funkcjach TA-Lib, ale w pętli ma `pass` i **nie rejestruje niczego**; log ze startu „Discovered 158 indicators from TA-Lib" podaje liczbę funkcji dostępnych w bibliotece, nie zarejestrowanych. `discover_vbt_indicators` ma analogiczną martwą pętlę i rejestruje ręcznie dwa wskaźniki.

**Jak pokazać dzisiaj:** wybierz `vbt_MA` albo `vbt_RSI` → zrzut wygenerowanego formularza z parametrem `window` → uruchom backtest. Demonstruje **mechanizm**, nie bogactwo biblioteki.

> Nie mów na slajdzie o „158 wskaźnikach do wyboru" — lista ma dwie pozycje. Uczciwa teza: *„formularze parametrów nie są zaszyte w interfejsie, powstają w czasie działania z metadanych rejestru; rozszerzenie rejestru nie wymaga zmian we froncie"*. Rejestracja wskaźników TA-Lib jest w TODO (Faza 26) — po jej wdrożeniu ten zrzut zyska pełną wymowę.

---

## S5. Własny wskaźnik w Numbie

**Demonstruje:** Fazę 11 — własna logika sygnałów wykonywana w piaskownicy z walidacją AST, bez ingerencji w kod silnika.

| Parametr | Wartość |
|:--|:--|
| indicatorType | `custom` |
| codeContent | kod z przykładów poniżej |

### Kontrakt kodu (`indicators.py:380-395`)

Kod **nie definiuje funkcji** — przypisuje dwie zmienne na najwyższym poziomie:

| Dostępne w przestrzeni nazw | Wymagane na wyjściu | Blokowane przez walidację AST |
|:--|:--|:--|
| `close` (`pd.Series`), `vbt`, `np`, `pd` | `entries` i `exits` — maski boolowskie o kształcie `close` | importy, `eval`, `exec`, dostęp systemowy |

Brak `entries` albo `exits` daje błąd *„Custom code must define 'entries' and 'exits' variables"*. **Nie pisz `import numpy as np`** — `np`, `pd` i `vbt` są już wstrzyknięte, a każdy import jest odrzucany przez piaskownicę.

**Ograniczenie do zapamiętania:** w przestrzeni nazw jest **tylko `close`**. Wskaźników wymagających `high`/`low`/`volume` (ATR, STOCH, OBV) w tej ścieżce nie zaimplementujesz.

### Przykład 1 — przecięcie średnich, wprost na pandasie

```python
fast = close.rolling(10).mean()
slow = close.rolling(30).mean()

entries = (fast > slow) & (fast.shift(1) <= slow.shift(1))
exits   = (fast < slow) & (fast.shift(1) >= slow.shift(1))
```

Dobre na pierwszy zrzut: wynik powinien być zbliżony do S1, co potwierdza, że własna implementacja odtwarza wbudowaną strategię.

### Przykład 2 — RSI napisany od zera

```python
delta = close.diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rsi = 100 - 100 / (1 + gain / loss)

entries = rsi < 30
exits   = rsi > 70
```

Mocniejszy materiał prezentacyjny: pokazuje wskaźnik zaimplementowany od podstaw, nie wywołanie gotowego.

**Co złapać:** edytor kodu w panelu Inspector · wynik backtestu · dla kontrastu wklej kod z `import numpy` i zrzuć komunikat piaskownicy *„Unsafe code detected"* — dowód, że wykonywanie własnego kodu jest kontrolowane, a nie surowym `exec`.

> Argument do pracy: użytkownik dopisuje własną logikę badawczą bez modyfikowania silnika, a platforma waliduje kod przed wykonaniem (AST) i udostępnia zamkniętą przestrzeń nazw z ograniczonym zestawem wbudowanych. To środowisko badawcze z kontrolą, nie zdalne `exec`.

---

## S6. Optymalizacja Optuna

**Demonstruje:** węzeł Optimizer, przestrzeń parametrów, wykres przebiegu optymalizacji, wybór metryki celu.

| Parametr | Wartość |
|:--|:--|
| strategia bazowa | S1 (zapisz ją wcześniej) |
| metric | `Sharpe Ratio` |
| n_trials | `20` (na zrzut wystarczy; więcej wydłuża tylko czas) |
| param_bounds → `sma_fast` | min `5`, max `20`, step `1` |
| param_bounds → `sma_slow` | min `20`, max `60`, step `5` |
| initial_capital | `10000` |

**Co złapać:** węzeł Optimizer na kanwie · wykres optymalizacji (`OptimizationChart`) · najlepszy zestaw parametrów kontra wartość bazowa z S1.

> Pokaż celowo **inną metrykę** w drugim przebiegu (`Max Drawdown [%]`) — inne optimum przy tej samej przestrzeni parametrów dobrze ilustruje, że dobór funkcji celu jest decyzją badawczą.

---

## S7. Walk-Forward Optimization

**Demonstruje:** Fazę 15 (WFO), odporność strategii na przeuczenie — najpoważniejszy metodologicznie element platformy.

| Parametr | Wartość |
|:--|:--|
| strategia bazowa | S1 |
| window_size | `365d` |
| step_size | `90d` |
| tryb okna | `rolling` (drugi przebieg: `anchored`) |
| zakres dat | `2020-01-01` → `2026-01-01` (potrzebna dłuższa historia) |

**Co złapać:** węzeł WFO na kanwie · wyniki per okno (in-sample kontra out-of-sample) · porównanie `rolling` i `anchored`.

> Jeśli w pracy dyplomowej jest wątek walidacji strategii, to jest zrzut, który powinien być na slajdzie tytułowym tej sekcji.

---

## S8. Alokacja kapitału między instrumenty

**Demonstruje:** ADR-0009 (analiza alokacji kapitału, liczba syntetycznych tickerów).

Modyfikacja S2 (multi-symbol), w węźle portfela:

| Tryb | Co pokazuje |
|:--|:--|
| `distribution` | rozkład kapitału między instrumenty |
| `ranking` | alokacja według rankingu instrumentów |
| `mapping` | jawne przypisanie wag |

**Co złapać:** timeline wag w czasie · podsumowanie per symbol · te same reguły z trzema trybami alokacji obok siebie.

---

## S9. Tryb offline — konektor synthetic

**Demonstruje:** działanie bez dostępu do internetu (self-hosted, air-gapped), determinizm danych testowych.

Modyfikacja S1: `dataSource` → `synthetic`. Reszta parametrów bez zmian.

**Co złapać:** ten sam DAG działający bez sieci · wybór konektora w panelu Inspector.

> Warto zrobić ten zrzut z **wyłączonym Wi-Fi** — to dowód, nie deklaracja.

---

## S10. Funkcje towarzyszące

Nie są strategiami, ale dopełniają obraz możliwości:

| Funkcja | Jak pokazać |
|:--|:--|
| **Analiza AI (Ollama)** | otwórz job → zakładka AI Chat → poproś o interpretację wyników. Wymaga działającego Ollamy; przy jej braku pokaże czytelny komunikat błędu |
| **Notatki badawcze** | panel Notes przy jobie — dodaj, przypnij, usuń. Notatki są wspólne dla wszystkich przebiegów danej strategii |
| **Dashboard — dane rynkowe** | wykres świecowy z nakładką SMA/EMA, przełączanie instrumentu i interwału, historia jobów z metrykami |
| **Zarządzanie użytkownikami** | Settings → Users: włączenie autoryzacji, role, JWT. Operacje uprzywilejowane przy wyłączonej autoryzacji działają wyłącznie z loopbacku |
| **Ustawienia promptów AI** | Settings → prompty systemowe, wybór domyślnego |

---

## Sugerowana kolejność sesji zrzutowej

1. **S1** zbuduj od zera — to jedyna strategia, którą warto pokazać w trakcie budowania (przeciąganie węzłów, łączenie portów)
2. **Zapisz** ją pod nazwą i zrób zrzut modalu zapisu oraz listy strategii
3. **S3** przez modyfikację S1 — zestaw obok siebie wyniki obu (najlepszy materiał porównawczy)
4. **S2** przez zmianę symbolu na listę — zrzut Dashboardu z kolumną Return per ticker
5. **S4** i **S5** — panel Inspector, przebudowa formularza i edytor kodu
6. **S6**, potem **S7** — najdłużej się liczą, więc na końcu; w tle możesz opisywać poprzednie zrzuty
7. **S9** z wyłączoną siecią
8. **S10** — funkcje towarzyszące

---

## Czego nie obiecywać na zrzutach

Rzeczy, które w interfejsie wyglądają na dostępne, ale nie są. Warto o nich wiedzieć, żeby nie zapowiedzieć na slajdzie czegoś, czego zrzut nie pokaże:

| Ograniczenie | Stan faktyczny |
|:--|:--|
| **Tearsheet nie zawiera wykresów** | `qsadapter.py` generuje tabelę metryk (~5,7 kB HTML, zero obrazów). Nazywaj to „zestawieniem metryk QuantStats", nie „raportem z wykresami" |
| **RSI i MACD nie rysują się na wykresie Dashboardu** | Backend je liczy, wykres nakłada tylko SMA i EMA — brak subplotu z osobną osią Y. W formularzu Dashboardu są tylko SMA i EMA |
| **Krzywa kapitału nie jest utrwalana** | `equity_curve` w odpowiedzi joba jest `null`; wykresu equity z historycznego joba nie da się pokazać |
| **Metryki multi-symbol** | job multi-symbol nie ma zagregowanego `total_return_pct` — są wartości per ticker. Nie szukaj jednej liczby dla całego portfela |
| **Dane intraday** | limity dostawcy (~60 dni dla 5m, ~730 dni dla 1h); dłuższy zakres to błąd walidacji, nie awaria |
| **Trailing stop (`sl_trail`)** | schemat backendu go przyjmuje, ale **formularz go nie wystawia** — nie zapowiadaj trailing stopa na slajdzie |
| **Przesunięcie sygnału** | **nie jest** parametrem użytkownika i nie ma go w węźle sygnału — silnik stosuje `fshift(1)` bezwarunkowo (ADR-0007). To zaleta, nie brak, ale nie szukaj pola do ustawienia |

---

## Odtworzenie stanu bazy pod zrzuty

Jeśli chcesz mieć historię jobów wyglądającą jak po realnej pracy badawczej, wykonaj S1 → S3 → S2 → S4 (MACD) w tej kolejności — dostaniesz listę z różnymi instrumentami, interwałami i profilami ryzyka, w tym wpisy multi-symbol. Do każdego dodaj notatkę, żeby panel Notes nie był pusty na zrzucie.

Kopia bazy sprzed sesji: `backend/data/db/backup/`.
