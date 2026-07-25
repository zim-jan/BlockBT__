# C3. Plany rozwoju

Materiał źródłowy do sekcji pracy dyplomowej. Lista nie jest zbiorem życzeń — pochodzi z trzech rund testów manualnych modułu Dashboard, przeglądu bezpieczeństwa warstwy autoryzacji oraz analizy kodu wykonanej 2026-07-25. Każda pozycja ma wskazanie miejsca w kodzie i uzasadnienie, dlaczego warto ją zrealizować.

Porządek nie jest przypadkowy. Najwyższy priorytet mają rzeczy, które w interfejsie **wyglądają na dostępne, a nie są** — ich domknięcie nie dodaje funkcji, lecz przywraca zgodność między tym, co aplikacja obiecuje, a tym, co robi. Dopiero potem idą rozszerzenia i kierunki badawcze.

---

## C3.1 Domknięcie funkcji zapowiedzianych w interfejsie

Kategoria najważniejsza dla wiarygodności narzędzia badawczego. Użytkownik widzi kontrolkę albo komunikat sugerujący możliwość, która nie została zaimplementowana.

### C3.1.1 Tryb portfelowy dla wielu instrumentów

**Stan obecny:** backtest wielu instrumentów wykonywany jest jako *N niezależnych kolumn bez współdzielenia kapitału* (`opensource_engine.py:797`). Zestaw dwóch instrumentów z kapitałem początkowym 10 000 angażuje realnie 20 000 — każdy instrument otrzymuje pełną kwotę. W konsekwencji nie istnieją zagregowane metryki portfela i karty podsumowania pozostają puste (`MainLayout.tsx:25`).

**Dlaczego to istotne metodologicznie:** wskaźnik Sharpe'a portfela zależy od korelacji składników, a maksymalne obsunięcie kapitału od tego, że obsunięcia poszczególnych instrumentów nie zachodzą jednocześnie. Uśrednienie tych miar po instrumentach jest **statystycznie nieprawidłowe** — dałoby liczbę wyglądającą poprawnie i wniosek fałszywy. Obecne zachowanie jest więc uczciwe, ale niepełne.

**Kierunek:** wykorzystanie mechanizmu grupowania biblioteki vectorbt (`group_by` wraz z `cash_sharing`) jako **parametru węzła portfela**, nie ukrytej decyzji silnika. Jedna symulacja obsługuje wówczas oba poziomy odczytu: metryki portfela na wspólnej krzywej kapitału oraz rozbicie na instrumenty. Tryb badania sygnału pozostaje domyślnym, tryb portfelowy dochodzi obok niego.

**Wartość badawcza:** różnica między sumą wyników niezależnych a wynikiem portfela ze wspólnym kapitałem jest **zmierzoną dywersyfikacją**. Przestaje być deklaracją, a staje się wynikiem eksperymentu — możliwym do zaprezentowania na tych samych danych i tych samych regułach.

**Uwaga wdrożeniowa:** zmiana narusza porównywalność dotychczasowych wyników wielosymbolowych. Wymaga wcześniejszego sprawdzenia zachowania analizy alokacji kapitału (ADR-0009) oraz liczników wyjść przez stop loss i take profit po zgrupowaniu.

### C3.1.2 Rejestracja wskaźników TA-Lib

**Stan obecny:** funkcja `discover_talib_indicators` (`indicator_registry.py:71`) iteruje po 158 funkcjach biblioteki TA-Lib, lecz ciało pętli stanowi instrukcja `pass` — do rejestru nie trafia żaden wskaźnik. Komunikat startowy *„Discovered 158 indicators from TA-Lib"* podaje liczbę funkcji dostępnych w bibliotece, nie zarejestrowanych, przez co sugeruje istnienie funkcji, której nie ma. Analogiczna martwa pętla występuje w `discover_vbt_indicators`; ręcznie zarejestrowane są dwa wskaźniki: `vbt_MA` i `vbt_RSI`.

**Co działa:** mechanizm dynamicznej introspekcji (ADR-0005) jest sprawny — panel inspektora generuje pola formularza z metadanych wskaźnika: nazwy parametrów, typów i wartości domyślnych (`InspectorPanel.tsx:359-368`). Infrastruktura istnieje, brakuje jej treści.

**Kierunek:** rejestracja przez interfejs `talib.abstract.Function`, który udostępnia metadane parametrów wraz z wartościami domyślnymi. Konieczny jest adapter wywołania, ponieważ `IndicatorRegistry.execute` wywołuje funkcję w konwencji `func(data, **kwargs)`, natomiast abstrakcyjne funkcje TA-Lib przyjmują odmienny kształt wejścia. Należy również poprawić komunikat logu, aby raportował liczbę wskaźników faktycznie zarejestrowanych.

**Efekt:** rozszerzalność przestaje być argumentem teoretycznym. Dodanie wskaźnika po stronie silnika nie wymaga zmian w interfejsie, a użytkownik zyskuje dostęp do pełnej biblioteki wskaźników analizy technicznej.

### C3.1.3 Wizualizacja oscylatorów na wykresie danych rynkowych

Backend wylicza RSI oraz MACD i zwraca je w odpowiedzi, natomiast wykres nakłada wyłącznie średnie kroczące — brak panelu z osobną osią wartości. Wymaga budowy dynamicznych dziedzin (`domain`) osi w zależności od liczby aktywnych oscylatorów oraz zwiększenia wysokości kontenera. Warunkiem wstępnym jest decyzja opisana w C3.2.1, ponieważ zmienia ona kształt odpowiedzi endpointu.

### C3.1.4 Wykresy w raporcie analitycznym i utrwalanie krzywej kapitału

Generator raportu (`qsadapter.py:66`) składa dokument HTML zawierający wyłącznie tabelę metryk — brak elementów graficznych. Jednocześnie krzywa kapitału nie jest utrwalana w bazie (pole `equity_curve` pozostaje puste), co uniemożliwia odtworzenie wykresu z historycznego przebiegu. Kolejność prac jest zatem wymuszona: najpierw utrwalanie serii czasowej, następnie wizualizacja — czy to przez pełny raport biblioteki QuantStats, czy przez wykresy interaktywne po stronie interfejsu.

### C3.1.5 Uzupełnienia formularzy

Parametr trailing stop (`sl_trail`) jest przyjmowany przez schemat backendu, ale nie został wystawiony w formularzu węzła portfela. Podobnie kod użytkownika (C3.1.6) otrzymuje w przestrzeni nazw wyłącznie serię cen zamknięcia.

### C3.1.6 Rozszerzenie kontraktu kodu użytkownika

Piaskownica wykonująca własną logikę sygnałów (ADR-0002) udostępnia zmienne `close`, `vbt`, `np` i `pd`, wymagając przypisania masek `entries` oraz `exits`. Walidacja składni abstrakcyjnej blokuje importy i dostęp systemowy — mechanizm działa poprawnie i został potwierdzony testem. Ograniczeniem jest brak dostępu do serii `high`, `low` i `volume`, co uniemożliwia implementację wskaźników zmienności i wolumenu (ATR, STOCH, OBV). Rozszerzenie przestrzeni nazw o pełny zestaw serii OHLCV jest zmianą niewielką, a znacząco poszerza zakres możliwych badań.

---

## C3.2 Zgodność z architekturą i odtwarzalność badań

### C3.2.1 Ujednolicenie dostępu do danych rynkowych

Endpoint danych bieżących (`/api/data/realtime`) wywołuje bibliotekę `yfinance` bezpośrednio, pomijając rejestr konektorów oraz pamięć podręczną w formacie Parquet. Narusza to regułę projektową dotyczącą izolacji warstwy danych i uniemożliwia pracę w trybie odciętym od sieci — bez połączenia moduł prezentacji danych rynkowych pozostaje niefunkcjonalny, mimo że pozostałe komponenty aplikacji działają na danych lokalnych.

Przeniesienie endpointu na rejestr konektorów daje trzy efekty: spójność architektury, działanie w trybie air-gapped oraz odtwarzalność — dane raz pobrane trafiają do pamięci podręcznej i kolejne uruchomienia badania operują na identycznym zbiorze.

### C3.2.2 Nowe źródła danych

Rejestr konektorów obsługuje obecnie Yahoo Finance, dane syntetyczne oraz Alpaca. Naturalnym rozszerzeniem jest import z plików lokalnych (CSV, Parquet), co ma znaczenie dwojakie: umożliwia pracę na danych własnych lub zakupionych oraz czyni badanie w pełni odtwarzalnym, niezależnym od dostępności i zmienności zewnętrznego dostawcy.

### C3.2.3 Odtwarzalność wyników

Aplikacja wymusza przesunięcie sygnałów o jeden okres (ADR-0007), zapobiegając przeciekowi informacji z przyszłości. Kolejnym krokiem jest pełna odtwarzalność eksperymentu: zapis wersji danych wejściowych wraz z wynikiem, ziarna generatora dla przebiegów wykorzystujących losowość (Optuna) oraz metadanych środowiska. Bez tego wynik zapisany w bazie nie jest weryfikowalny po czasie.

---

## C3.3 Jakość, automatyzacja i dług techniczny

### C3.3.1 Ciągła integracja

Repozytorium nie zawiera konfiguracji ciągłej integracji — katalog `.github/workflows/` nie istnieje. Zestaw testów obejmuje 275 testów backendu oraz 47 testów interfejsu, uruchamianych wyłącznie ręcznie.

Doświadczenie z sesji 2026-07-25 pokazuje, dlaczego to istotne, i jednocześnie że sama obecność testów nie wystarcza. Przez ponad dwa miesiące build interfejsu generował 20% klas stylów, ponieważ aktualizacja biblioteki Tailwind do wersji 4 nie została uzupełniona migracją pliku wejściowego. Awaria pozostawała niewidoczna: testy jednostkowe przechodziły w całości, a polecenie budowania kończyło się sukcesem, gdyż środowisko testowe nie ładuje arkuszy stylów i żaden test nie weryfikował wyglądu. Wniosek: obok uruchamiania testów potrzebne są **asercje na artefaktach budowania** — na przykład kontrola rozmiaru wygenerowanego arkusza, który przy poprawnym buildzie wynosi około 74 kB, a przy zepsutym spada do 23 kB.

### C3.3.2 Pokrycie testami obszarów nieobjętych

Endpointy danych bieżących oraz notatek nie mają żadnego pokrycia w zestawie testów backendu. Regresja, która doprowadziła do awarii modułu Dashboard — niepoprawna serializacja wartości nieliczbowych — również nie ma testu regresyjnego, mimo że asercje zostały już napisane w skrypcie kontrolnym `scripts/smoke_faza25.py` i wystarczy przenieść je do zestawu testów z zamockowanym dostawcą danych. Analogicznie brakuje testów komponentów interfejsu modułu Dashboard.

### C3.3.3 Ujednolicenie systemu wizualnego

W aplikacji współistnieją dwa niezależne zestawy tokenów projektowych: paleta Material 3 zdefiniowana w konfiguracji Tailwind, obowiązująca dla całego interfejsu, oraz starsza paleta w zmiennych CSS, obsługująca wyłącznie kanwę edytora przepływu. Skutkuje to widoczną różnicą stylistyczną między kanwą a pozostałymi widokami. Stan został udokumentowany, ujednolicenie pozostaje do wykonania.

### C3.3.4 Pozostałe pozycje długu

| Pozycja | Stan |
|:--|:--|
| Rozróżnienie „brak danych" od „usługa nie odpowiada" w liście przebiegów | brak obsługi stanu błędu zapytania |
| Martwe klasy stylów (`prose`, `modal-overlay`, `strategy-item`) | wywołania bez definicji; brak wtyczki typografii |
| Skrypt uruchomieniowy `run_local.sh` | wskazuje nieistniejący moduł, wprowadza w błąd przy pierwszym uruchomieniu |
| Rozmiar pakietu interfejsu | 5,2 MB w jednym fragmencie; wymaga podziału kodu |
| Dokumentacja decyzji | 11 rekordów ADR; dyscyplinę należy utrzymać dla każdej zmiany z tej listy |

---

## C3.4 Bezpieczeństwo — kolejne kroki

Blokujące podatności zostały usunięte: granicą zaufania przy wyłączonej autoryzacji jest interfejs pętli zwrotnej (ADR-0011), sprawdzanie właściciela zasobu obejmuje sześć punktów wejścia, rekordy bez przypisanego właściciela są odrzucane, odczyt konfiguracji autoryzacji zachowuje się bezpiecznie w razie błędu, a warstwa posiada 17 testów regresyjnych.

Pozostają zadania o niższym priorytecie:

1. **Weryfikacja stanu konta przy każdym żądaniu.** Warstwa pośrednia ufa zawartości tokenu, którego czas życia wynosi 24 godziny. Dezaktywacja konta lub obniżenie uprawnień nie odnoszą skutku do wygaśnięcia tokenu. Rozwiązaniem jest odczyt stanu użytkownika z bazy lub skrócenie czasu życia tokenu wraz z mechanizmem odświeżania.
2. **Ograniczanie liczby prób logowania w środowisku wieloprocesowym.** Licznik przechowywany jest w pamięci procesu, co przy wielu instancjach roboczych obniża skuteczność zabezpieczenia.
3. **Kolejność warstw pośrednich.** Zgłoszona wątpliwość co do obsługi żądań wstępnych mechanizmu CORS wymaga potwierdzenia eksperymentalnego.
4. **Rejestr operacji uprzywilejowanych.** Zmiana konfiguracji autoryzacji, tworzenie i modyfikacja kont nie są odnotowywane w dzienniku audytowym.

---

## C3.5 Kierunki rozwoju badawczego

Propozycje wychodzące poza domykanie istniejącej funkcjonalności — obszary, w których platforma może wnieść wartość jako narzędzie badawcze.

**Analiza portfelowa.** Po wdrożeniu trybu portfelowego (C3.1.1) otwiera się cała klasa badań: rebalansowanie okresowe, wagi oparte na ryzyku (odwrotność zmienności, parytet ryzyka), ograniczenia ekspozycji na instrument i sektor, wpływ kosztów transakcyjnych na strategię o wysokiej rotacji.

**Rozszerzona walidacja strategii.** Optymalizacja krocząca (ADR-0006) jest solidnym fundamentem. Kolejnymi krokami są metody odporne na przeuczenie: walidacja krzyżowa z oczyszczaniem i embargiem, kombinatoryczna walidacja krzyżowa, a także miary istotności statystycznej uwzględniające liczbę przetestowanych wariantów — bez nich wysoki wskaźnik Sharpe'a znaleziony w przestrzeni tysięcy kombinacji nie jest wynikiem, lecz artefaktem poszukiwania.

**Porównanie z benchmarkiem.** Raport analityczny powinien zestawiać wynik strategii ze strategią pasywną oraz indeksem odniesienia. Bez punktu odniesienia stopa zwrotu nie odpowiada na pytanie, czy strategia wnosi wartość.

**Eksport raportów.** Generowanie dokumentu do postaci PDF lub źródła LaTeX, z metrykami, wykresami i parametrami przebiegu — bezpośrednio użyteczne w pracy naukowej i w dokumentowaniu wyników badań.

**Asystent analityczny.** Integracja z lokalnym modelem językowym istnieje i działa na metrykach przebiegu. Rozwinięciem jest krytyka metodologiczna: wskazywanie zbyt małej liczby transakcji, podejrzanie wysokiego wskaźnika trafień, przeuczenia widocznego w rozbieżności wyników w próbie i poza nią. Model przestaje wtedy opisywać wyniki, a zaczyna kwestionować wnioski.

**Skalowanie obliczeń.** Optymalizacja i walidacja krocząca są z natury równoległe. Rozproszenie obliczeń pozwoliłoby na przestrzenie parametrów o rząd wielkości większe, co jest warunkiem wiarygodnego badania odporności strategii.

---

## C3.6 Proponowana kolejność

| Priorytet | Zakres | Uzasadnienie |
|:--:|:--|:--|
| 1 | Rejestracja wskaźników TA-Lib (C3.1.2) | mały koszt, natychmiastowa i widoczna zmiana wartości narzędzia |
| 2 | Ciągła integracja z asercjami na artefaktach (C3.3.1) | zabezpiecza wszystkie kolejne zmiany; brak tego mechanizmu kosztował dwa miesiące niezauważonej awarii |
| 3 | Ujednolicenie dostępu do danych (C3.2.1) | warunek wstępny dla wizualizacji oscylatorów i pracy w trybie odciętym od sieci |
| 4 | Tryb portfelowy (C3.1.1) | największa wartość badawcza; wymaga decyzji przed zbieraniem materiału do pracy, ponieważ narusza porównywalność wyników |
| 5 | Utrwalanie krzywej kapitału i wykresy w raporcie (C3.1.4) | domyka warstwę analityczną |
| 6 | Pokrycie testami obszarów nieobjętych (C3.3.2) | asercje w większości już napisane, pozostaje przeniesienie |
| 7 | Pozostałe pozycje z C3.1, C3.3.4 i C3.4 | prace porządkowe, wykonalne przyrostowo |

---

## Zasada porządkująca

Lista jest uporządkowana według jednej reguły: **najpierw zgodność obietnicy z implementacją, potem nowe możliwości.** Narzędzie badawcze, które pokazuje kontrolkę bez działania albo raportuje w dzienniku funkcję nieistniejącą, podważa zaufanie do każdego wyniku, który wyprodukuje — również do tych policzonych poprawnie. Dopiero po domknięciu tej kategorii rozszerzenia z sekcji C3.5 mają sens, ponieważ będą budowane na fundamencie, którego zachowanie jest znane i sprawdzalne.

---

## Podsumowanie

Pierwszym planowanym rozszerzeniem jest tryb portfelowy dla wielu instrumentów. Obecnie backtest zestawu instrumentów wykonywany jest jako niezależne kolumny bez współdzielenia kapitału, wobec czego dwa instrumenty z kapitałem początkowym dziesięciu tysięcy angażują realnie dwadzieścia tysięcy, a zagregowane metryki portfela nie powstają. Planowane jest wystawienie mechanizmu grupowania biblioteki vectorbt jako parametru węzła portfela, dzięki czemu jedna symulacja pozwoli odczytać zarówno wynik portfela na wspólnej krzywej kapitału, jak i rozbicie na poszczególne instrumenty. Wartość tej zmiany wykracza poza samą funkcjonalność, ponieważ różnica między sumą wyników niezależnych a wynikiem portfela ze wspólnym kapitałem stanowi zmierzoną dywersyfikację, czyli wynik eksperymentu zamiast deklaracji.

Drugim zadaniem jest rejestracja wskaźników biblioteki TA-Lib w rejestrze wskaźników. Funkcja odkrywająca iteruje obecnie po stu pięćdziesięciu ośmiu funkcjach biblioteki, lecz nie zapisuje żadnej z nich, przez co lista dostępna w interfejsie zawiera dwie pozycje zarejestrowane ręcznie. Mechanizm generowania formularzy z metadanych działa poprawnie, brakuje mu wyłącznie treści, dlatego uzupełnienie rejestru przez interfejs abstrakcyjny biblioteki natychmiast przełoży się na widoczną wartość narzędzia. Konieczne będzie napisanie adaptera wywołania oraz poprawienie komunikatu dziennika, który dziś raportuje liczbę funkcji dostępnych, a nie zarejestrowanych.

Kolejnym krokiem jest wizualizacja oscylatorów na wykresie danych rynkowych. Warstwa serwerowa wylicza wskaźnik siły relatywnej oraz zbieżność i rozbieżność średnich kroczących, natomiast wykres nakłada wyłącznie średnie kroczące, ponieważ brakuje panelu z osobną osią wartości. Wdrożenie wymaga wyznaczania dziedzin osi w zależności od liczby aktywnych oscylatorów oraz zwiększenia wysokości kontenera wykresu.

Osobnym zadaniem jest utrwalanie krzywej kapitału i uzupełnienie raportu analitycznego o wykresy. Generator raportu składa dziś dokument zawierający wyłącznie tabelę metryk, a przebiegi nie zapisują serii czasowej wartości portfela, wobec czego wykresu nie da się odtworzyć z historycznego wyniku. Kolejność prac jest wymuszona przez tę zależność, ponieważ dopiero utrwalona seria czasowa umożliwia wizualizację, niezależnie od tego, czy powstanie ona po stronie serwera, czy w interfejsie.

Piaskownica wykonująca kod użytkownika zyska dostęp do pełnego zestawu serii cenowych. Dziś udostępnia wyłącznie ceny zamknięcia, co uniemożliwia implementację wskaźników zmienności i wolumenu, mimo że sam mechanizm bezpiecznego wykonania kodu wraz z walidacją składni działa prawidłowo i został potwierdzony testem. Przy tej okazji formularz węzła portfela zostanie uzupełniony o parametr kroczącego zlecenia obronnego, który schemat serwera już przyjmuje, lecz interfejs go nie wystawia.

Zmianą architektoniczną o istotnych konsekwencjach jest przeniesienie endpointu danych bieżących na rejestr konektorów wraz z pamięcią podręczną w formacie Parquet. Bezpośrednie wywoływanie biblioteki dostawcy narusza zasadę izolacji warstwy danych i uniemożliwia pracę bez dostępu do sieci, mimo że pozostałe komponenty aplikacji operują na danych lokalnych. Poza spójnością architektury zmiana przynosi odtwarzalność, ponieważ dane raz pobrane zasilają kolejne uruchomienia badania z niezmiennego zbioru.

Rejestr konektorów zostanie rozszerzony o import z plików lokalnych w formatach tekstowym i kolumnowym. Umożliwi to pracę na danych własnych lub zakupionych, a jednocześnie uczyni badanie niezależnym od dostępności i zmienności zewnętrznego dostawcy, co ma bezpośrednie znaczenie dla powtarzalności wyników opisywanych w pracy.

Uzupełnieniem tego kierunku jest pełna odtwarzalność eksperymentu. Aplikacja wymusza już przesunięcie sygnałów o jeden okres, zapobiegając przeciekowi informacji z przyszłości, natomiast wynik zapisany w bazie nie przechowuje wersji danych wejściowych, ziarna generatora liczb losowych ani metadanych środowiska. Bez tych informacji zapisany wynik nie jest weryfikowalny po upływie czasu.

Wdrożenie ciągłej integracji zabezpieczy wszystkie kolejne zmiany. Repozytorium nie zawiera dziś żadnej konfiguracji automatycznego uruchamiania testów, mimo że zestaw obejmuje dwieście siedemdziesiąt pięć testów warstwy serwerowej i czterdzieści siedem testów interfejsu. Doświadczenie z awarii budowania arkuszy stylów, która przez ponad dwa miesiące pozostawała niezauważona przy przechodzących testach, prowadzi do wniosku, że obok uruchamiania testów potrzebne są asercje na artefaktach budowania, na przykład kontrola rozmiaru wygenerowanego arkusza stylów.

Równolegle planowane jest objęcie testami obszarów dotąd niepokrytych, czyli endpointów danych bieżących oraz notatek, a także komponentów interfejsu modułu przeglądowego. Regresja, która doprowadziła do awarii tego modułu, nie ma dziś testu regresyjnego, choć odpowiednie asercje zostały już napisane w skrypcie kontrolnym i wystarczy przenieść je do zestawu testów z zamockowanym dostawcą danych.

Warstwa wizualna wymaga ujednolicenia systemu tokenów projektowych. W aplikacji współistnieją dwa niezależne zestawy, z których jeden obsługuje cały interfejs, a drugi wyłącznie kanwę edytora przepływu, co skutkuje widoczną różnicą stylistyczną między kanwą a pozostałymi widokami.

Do wykonania pozostają również prace porządkowe o mniejszym zasięgu, lecz zauważalne w codziennym użytkowaniu. Lista przebiegów nie odróżnia braku danych od niedostępności usługi, w kodzie występują wywołania klas stylów bez definicji, skrypt uruchomieniowy wskazuje nieistniejący moduł i wprowadza w błąd przy pierwszym starcie, a pakiet interfejsu jest dostarczany jako jeden fragment o rozmiarze pięciu megabajtów i wymaga podziału.

W warstwie bezpieczeństwa, po usunięciu podatności blokujących, planowana jest weryfikacja stanu konta przy każdym żądaniu. Warstwa pośrednia ufa dziś zawartości tokenu o dobowym czasie życia, wobec czego dezaktywacja konta lub obniżenie uprawnień nie odnoszą skutku do wygaśnięcia tokenu. Rozwiązaniem jest odczyt stanu użytkownika z bazy albo skrócenie czasu życia tokenu wraz z mechanizmem odświeżania.

Uzupełnieniem prac nad bezpieczeństwem jest przeniesienie licznika prób logowania do magazynu współdzielonego, ponieważ obecna implementacja przechowuje go w pamięci procesu i traci skuteczność przy wielu instancjach roboczych, oraz wprowadzenie rejestru operacji uprzywilejowanych, obejmującego zmianę konfiguracji autoryzacji oraz tworzenie i modyfikację kont.

Po wdrożeniu trybu portfelowego otwiera się kierunek analizy portfelowej, obejmujący rebalansowanie okresowe, wagi oparte na ryzyku, ograniczenia ekspozycji na instrument i sektor oraz badanie wpływu kosztów transakcyjnych na strategie o wysokiej rotacji. Jest to kierunek, w którym platforma przestaje weryfikować pojedynczą regułę, a zaczyna odpowiadać na pytania o konstrukcję portfela.

Rozszerzona walidacja strategii stanowi kierunek najbardziej istotny metodologicznie. Zaimplementowana optymalizacja krocząca jest solidnym fundamentem, natomiast pełną odporność na przeuczenie zapewniają dopiero metody walidacji krzyżowej z oczyszczaniem i embargiem oraz miary istotności statystycznej uwzględniające liczbę przetestowanych wariantów, bez których wysoki wskaźnik efektywności znaleziony w przestrzeni tysięcy kombinacji pozostaje artefaktem poszukiwania, a nie wynikiem.

Raport analityczny zostanie uzupełniony o porównanie z punktem odniesienia, czyli ze strategią pasywną oraz indeksem rynkowym, ponieważ bez takiego zestawienia stopa zwrotu nie odpowiada na pytanie, czy strategia wnosi wartość dodaną. Planowany jest również eksport raportu do formatu dokumentowego wraz z metrykami, wykresami i parametrami przebiegu, co ma bezpośrednie zastosowanie przy dokumentowaniu wyników badań.

Integracja z lokalnym modelem językowym zostanie rozwinięta z opisu wyników w kierunku krytyki metodologicznej, obejmującej wskazywanie zbyt małej liczby transakcji, podejrzanie wysokiego wskaźnika trafień oraz przeuczenia widocznego w rozbieżności wyników w próbie i poza nią. Model przestaje wtedy relacjonować metryki, a zaczyna kwestionować wnioski badacza.

Ostatnim planowanym kierunkiem jest rozproszenie obliczeń. Optymalizacja parametrów oraz walidacja krocząca są z natury równoległe, wobec czego rozproszenie pozwoliłoby badać przestrzenie parametrów o rząd wielkości większe, co stanowi warunek wiarygodnego wnioskowania o odporności strategii.
