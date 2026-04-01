# Silnik Backtestingu (Engine)

Serce **BlockBT** to zoptymalizowany moduł wykonawczy (Execution Engine), bazujący na bibliotece *vectorbt* (nie na `pandas-ta`). Jest on zaprojektowany pod kątem szybkości iteracji, maksymalnej zgodności z natywnym kodem biblioteki oraz elastyczności, dzięki architekturze "Dual-Engine Ready".

## Wzorzec Architektoniczny: "Dual-Engine Ready"

System obsługi strategii jest przygotowany do skalowania. Osiągnięto to dzięki implementacji wzorca Abstract Factory / Adapter. W praktyce oznacza to, że wywołania silnika posiadają ustandaryzowany interfejs.

*   Silniki (takie jak np. otwartoźródłowy *vectorbt* w wersji `opensource_engine.py` lub opcjonalne, w pełni autorskie rozszerzenia np. dla wersji pro) muszą realizować ten sam kontrakt i akceptować zunifikowane wywołania metod.
*   Zapewnia to separację warstwy prezentacji (Frontend, API FastAPI) od zawiłości operacyjnych backtestingu, co jest konieczne dla środowiska nie posługującego się już widżetami Streamlit.
*   Zwracane wyniki, w celu zagwarantowania spójności interfejsu API i zmniejszenia powiązań pomiędzy komponentami aplikacji, muszą być standardowymi słownikami Pythona (`dict`), zamiast niestandardowych, specjalizowanych obiektów wyników (takich jak klasa `BacktestResult`). Upraszcza to znacząco serializację do formatu JSON.

## Zasady Pisania Optymalizacji

Zastosowanie optymalizacji hiperparametryzacji (Grid Search) za pomocą biblioteki `vectorbt` wymaga przestrzegania określonych reguł formatowania danych:

*   **Płaskie Listy (Flat Lists) i itertools.product:** Aby uniknąć problemów z rozgłaszaniem błędów multi-indeksu (MultiIndex broadcasting errors) w dystrybucji open-source, wejściowe listy parametrów kombinacji dla testowania (np. zmienne okna dla RSI, różne poziomy Stop-Loss) muszą być wygenerowane przy pomocy `itertools.product` i przekazane do wskaźników wyłącznie jako zunifikowane "płaskie listy". Należy rygorystycznie unikać przekazywania wielowymiarowych zagnieżdżonych list parametrów.

## Metryki Obliczeniowe i Wydajność (vectorbt vs pandas-ta)

Do generowania wskaźników i obliczania wskaźników wewnątrz środowiska wykonawczego, z punktu widzenia wydajności aplikacji wielo-parametrycznej, stosuje się wyłącznie natywne struktury z `vectorbt`.

*   Zabronione jest wprowadzanie zewnętrznych zależności typu `pandas-ta`. Optymalizacja i obliczenia równoległe na dużych zbiorach danych wymagają natywnej integracji zwektoryzowanych wskaźników wewnątrz całego silnika.
*   Bezpośrednie zapytania do struktury DataFrame (np. z metody `portfolio.stats()`) muszą z precyzją odczytywać konkretne tekstowe klucze (np. `'Total Return [%]'`). Należy wystrzegać się abstrakcyjnych słowników mapujących pomiędzy zmiennymi w celu uniknięcia problemów z rzutowaniem podczas parsowania metryk w Pythonie.

## Wymagania Testowe

Podczas pisania, bądź rozwijania silnika obliczeniowego z wykorzystaniem `vectorbt`, do testowania modułów warstwy logiki wykonawczej (Engine/Optimizer):

*   **Brak Mockowania Wewnętrznych Obiektów:** Zabronione jest używanie technik mockowania dla kluczowych metod z `vectorbt`. Do poprawnego przeprowadzenia testów jednostkowych (na obiekcie Pandas DataFrame/VBT) zaleca się użycie autorskiego, niewielkiego syntetycznego zbioru danych oraz oryginalnych wywołań środowiska deweloperskiego.
