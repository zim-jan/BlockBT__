# Realizacja Projektu: Rozbudowa Interfejsu, Integracja AI oraz Moduły Optymalizacyjne (Sekcja C3)

## Cel Etapów 2–5

Zasadniczym krokiem po implementacji warstwy dostępu do danych cyfrowych oraz abstrakcyjnego silnika wykonawczego, była budowa otwartego ekosystemu GUI i integracja kluczowych podzespołów badawczych dla środowiska Data Science i Quant Trading. Fazy projektowe podzielono na zintegrowane gałęzie:

1. **Graficzny Interfejs Użytkownika (Streamlit)** — realizacja wzorca Multipage App.
2. **Monitorowanie Stanu i Architektury (Diagnostyka)** — widoki pozwalające na audyt środowiska BYOL w czasie rzeczywistym.
3. **Sztuczna Inteligencja (Ollama / MCP)** — adaptacja wzorca Model Context Protocol do delegowania analiz inwestycyjnych pod zewnętrzny model LLM.
4. **Zaawansowany Backtesting (Optuna i pandas-ta)** — automatyczna, bayesowska optymalizacja parametrów strategii oraz wpieranie logiki decyzyjnej za pomocą profesjonalnej biblioteki wskaźników zaimplementowanej w języku C.

---

## 2.1 Architektura Interfejsu (React)

Aplikację oparto o framework **Streamlit**, stosując scentralizowany punkt wejścia (`app.py`), system nawigacji bocznej oraz wymuszaną autoryzację. Ze względu na charakter środowiska (ponowne wykonywanie całego pliku przy interakcji), stan w kreatorze strategii przechowywany jest asynchronicznie poprzez obiekty typu *Streamlit Session State* (`st.session_state`).

1. **Kreator Strategii**: Panel pozwalający na definiowanie założeń (dostawca, instrument, okno czasowe, kapitał początkowy i opis tekstowy).
2. **Dashboard**: Panel egzekucji zdefiniowanych szablonów. Wywołuje abstrakcję z warstwy pierwszej, wizualizując stopy zwrotu oraz nakładając interaktywną krzywą kapitału. Zapisuje wyniki wykonania z powrotem do bazy danych.

---

## 2.2 System Diagnostyczny z Weryfikacją BYOL

Istotną innowacją w inżynierskim podejściu do cyklu uruchomieniowego jest ciągła diagnostyka środowiska. Ze względu na odcięte repozytorium VectorBT PRO ("Air-Gapped Logic"), zaimplementowano mechanizm dynamicznego ładowania:

- Interfejs API weryfikuje bez importowania modułów zastrzeżonych, czy ścieżka do wstrzykniętych pakietów PRO istnieje (wzorzec BYOL). Jeśli nie — awaryjnie przekierowuje zapytania do OpenSourceEngine, który używa darmowej wersji.
- Zarządzanie danymi historycznymi opiera się wyłącznie na zoptymalizowanych plikach Parquet, po jednym pliku per symbol, unikając defragmentacji bazy danych. Zmniejsza to obciążenie sieciowe u dostawców danych giełdowych.

---

## 2.3 Automatyczny Analityk jako klient LLM (Ollama & MCP)

Projekt wykorzystuje standard **MCP (Model Context Protocol)** przygotowując zestandaryzowany, odtwarzalny protokół do integracji modułu wykonawczego ze sztuczną inteligencją.

1. Wzór `ReportBuilder` przetwarza wynikowe struktury `dict` z metrykami z engine'u na czytelny wektor w formacie JSON (zabezpieczenie przed overflowing context window w LLM).
2. Transponowany kontekst trafia do synchronicznego klienta LLM operującego na warstwie lokalnej. Proces nie komunikuje się z chmurą, a zapytania kierowane są wyłącznie do `localhost:11434`.

---

## 2.4 Eksploracja Danych Market Data i Nakładanie Algorytmów

Do podglądu zjawisk analitycznych zaimplementowano mechanizm weryfikacji metryk. Interfejs renderuje wykresy krzywych i dostarcza wskaźniki przed uruchomieniem masowego backtestingu, operując w stu procentach na zestawie narzędzi z otwartego źródła.

---

## 2.5 Obliczeniowa Skala Inżynierska: VectorBT Grid Search
## 2.5 Obliczeniowa Skala Inżynierska: Optuna & Wskaźniki Natywne

Do warstwy analitycznej wstrzyknięto wsparcie dla natywnej optymalizacji (bez obcych, spowalniających bilbiotek wskaźnikowych):

1. **Wskaźniki**: Zaimplementowano generator wskaźników bezpośrednio przy użyciu obiektów vectorbt (np. `vbt.MACD.run`). Pozwala to na pełną wektoryzację podczas testów.
2. **Optymalizacja (Grid Search)**: Wdrożono mechanizm przeszukiwania siatki oparty na `itertools.product`. Algorytm generuje płaskie kombinacje parametrów, co pozwala na masowe przetwarzanie testów unikając problemów z rzutowaniem wielowymiarowych indeksów w otwartej wersji biblioteki. Wyniki poszczególnych przebiegów są rejestrowane jako rekordy, a użytkownik może wyselekcjonować konfigurację o najlepszych proporcjach zysku do ryzyka.
1. **Wskaźniki Natywne**: Architektura została zaprojektowana w oparciu o silnik open-source'owy wspierający podstawowe metody wektoryzacji. System pozwala na szybkie ewaluacje np. metody przecinania prostych średnich kroczących w pamięci.
2. **Optymalizator Parametrów (Optuna)**: Wdrożono osobną sekcję optymalizacyjną `5_Optimizer.py` która wykorzystuje estymatory _Tree-structured Parzen Estimator (TPE)_. Algorytm definiuje przedziały okien (np `sma_fast` 2-50, `sma_slow` 50-300). Każdy *trial* Optuny zamyka zapytanie na ułamek sekundy korzystając z cache wczytanego OHLCV, logując historię z punktem krytycznym dążącym do maksymalizacji Sharpe Ratio z jednoczesną penalizacją braku wejść w rynek (kara -99). Najlepszy parametr jest zwrotnie implementowany z automatycznym aliasem na nowej template'cie bazy danych. Została również naniesiona w pełni zintegrowana wizualizacja procesu z paczki `optuna.visualization`.
