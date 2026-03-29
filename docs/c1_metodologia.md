# Metodologia i Technologie (Sekcja C1)

## Wybór Stosu Technologicznego

Implementacja platformy **BlockBT** bazuje na rygorystycznym doborze współczesnych narzędzi programistycznych i wiodących rozwiązań w obszarze data science oraz backendu inżynierskiego języka Python. Wybór każdego komponentu został poparty analizą stabilności, dojrzałości oraz wydajności w kontekście operacji finansowych.

### Język oraz Środowisko (Python)

Całość systemu została zrealizowana w oparciu o język **Python (wersja $\ge$ 3.10)**, korzystając w pełni z jego natywnego systemu statycznego typowania (Type Hints). Zwiększa to nie tylko czytelność kodu dla innych inżynierów, ale również pozwala na stosowanie rygorystycznej analizy statycznej za pomocą narzędzi takich jak `mypy` czy `ruff`. Python stanowi globalny standard w dziedzinie analizy ilościowej (Quantitative Finance), gwarantując swobodny dostęp do zoptymalizowanych (najczęściej w `C` bądź `C++`) bibliotek matematycznych typu `numpy` oraz `pandas`.

### Warstwa Trwałości i ORM (SQLite + SQLAlchemy 2.x)

Dla implementacji warstwy trwałości (Persistence Layer) zdecydowano się na użycie bezserwerowego silnika bazodanowego **SQLite**, działającego z włączonym trybem WAL (Write-Ahead Logging). Zapewnia to kompromis pomiędzy asynchroniczną i szybszą obsługą zapytań a zachowaniem formy pojedynczego, samo-zawierającego się pliku bazodanowego na dysku maszyny badawczej – co jest idealną specyfiką aplikacji *self-hosted*.

Jako narzędzie odwzorowania obiektowo-relacyjnego (ORM) wybrano bibliotekę **SQLAlchemy w generacji 2.x**. Decyzja ta podyktowana była wsparciem dla ujednoliconego, opartego o `dataclass` interfejsu deklaratywnego (`Mapped` / `mapped_column`), minimalizującego próg wejścia w analizie kodu, jednocześnie wymuszającego pełne bezpieczeństwo typów (Type Safety) dla każdej definicji tabeli z bazy. 

### Pamięć Podręczna Danych Szeregów Czasowych (Parquet)

Z uwagi na ogromny wolumen danych związany z przetwarzaniem giełdowych szeregów czasowych (OHLCV – *Open, High, Low, Close, Volume*) w perspektywach długoterminowych, klasyczne metody przechowywania w SQL okazałyby się stanowczym "wąskim gardłem" (bottleneck). Dlatego system oparto na natywnej obsłudze formatu **Apache Parquet**.

Jest to binarny nakierowany kolumnowo (columnar storage) format składowania danych wspierany silnikiem **PyArrow**. Zapewnia on radykalne skrócenie czasów odczytu poprzez ominięcie nieużywanych kolumn pod-zapytania (column pruning) operując natywnie na obiektach DataFrame dostarczanych do silnika testowego. Przeciwdziała zjawisku wyczerpywania przepustowości łączy (Network I/O limitations) z serwisów finansowych, redukując każdorazowe podciągania API jedynie do momentu chybienia pamięci lokalnej (cache miss).

### Integracja z LLM via Model Context Protocol (MCP)

W obszarze analityki po-transakcyjnej platformę wyposażono w wsparcie nowej generacji integracji protokołu MCP. Opracowano ustandaryzowaną reprezentację danych wejściowych z obiektu powrotnego symulatora do tzw. `MCPPayload`. Pakiet ten serwuje pełne metryki finansowe jak współczynnik kształtu Sharpe’a, wskaźniki osunięć kapitału (Max Drawdown) oraz zredukowaną do optymalnych wymiarów próbkę rzędu n-punktów ewolucji kapitałowej do dalszych ewaluacji na agentach AI korzystając z bezkolizyjnych standardów JSON bez sprzęgania implementacji w zamkniętym kodzie chmurowym.

## Wzorzec Architektoniczny Dual-Engine i Komponentizacja BYOL

Fundamentem inżynierskim całego systemu środowiska wykonawczego (Simulation Engine) była nieunikniona konieczność obniżenia tzw. długu licencyjnego z jednoczesnym udostępnieniem środowiska uniwersalnego. 

Rozwiązaniem tego problemu stał się paradygmat **Dual-Engine** z implementacją wektora w modelu **Bring Your Own License (BYOL)**. Stanowi to odpowiedź na odizolowany, zastrzeżony kod dostawcy wektorowej biblioteki finansowej (`vectorbtpro` traktowany jako tzw. *Black Box*).

System zachowuje się elastycznie na podstawie zasady ukrytej fabryki abstrakcyjnej (Abstract Factory Loader). Z użyciem ujednoliconego interfejsu `StrategyEngine`, definiującego jedyną i wspólną referencję wejścia testowego po przekazaniu uformowanego zbioru danych DataFrame, moduł wykonuje:

1. Jeśli silnik wykryje (dynamicznie w czasie importu `__import__`) odpowiednie prawa dostępu w pliku instalacyjnym komercyjnym dla *ProEngine* – korzysta z silnie zaawansowanej optymalizacji. 
2. W wypadku wystąpienia braku biblioteki licencjonowanej w podanym drzewie zasobów – w sposób transparentny dla instrukcji użytkownika (User Graceful Degradation) uruchamiany jest mechanizm implementacji `OpenSourceEngine` bazowany o wolnodostępne rozwiązanie, stanowiący stabilniejszą chociaż uboższą logicznie funkcjonalność.

Tak potężny mechanizm obniża niepewność i pozwala projektowi rosnąc w uniwersalności dostępu jako darmowe rozwiązanie samodzielnie obsługujące zintegrowane wektoryzowane symulacje, umożliwiając skokowe przechodzenie w stronę komercyjnych zastosowań badawczych minimalnym kosztem i zerowym wchodzeniem w ingerencję architektury korowej aplikacji BlockBT.
