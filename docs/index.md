# Wstęp

## Cel i Koncepcja Projektu

Aplikacja **BlockBT** (Block Backtesting) stanowi środowisko typu *Standalone* (Local/Self-Hosted) dedykowane do zaawansowanego badawczego backtestingu strategii algorytmicznych na rynkach finansowych. Głównym celem systemu jest dostarczenie modularnego, wysoce skalowalnego i niezależnego środowiska eksperymentalnego, które pozwala badaczom (quants) oraz programistom na elastyczne testowanie założeń rynkowych, bez polegania na zamkniętych, chmurowych ekosystemach (vendor lock-in).

Architektura oprogramowania została zaprojektowana w oparciu o zaawansowane wzorce znane z komercyjnych rozwiązań klasy korporacyjnej (np. QuantConnect, Zipline), kładąc szczególny nacisk na ścisłą separację logiki biznesowej od warstwy utrwalania danych i silnika wykonawczego.

## Główne Założenia Architektoniczne

Podstawą budowy systemu jest zachowanie rygorystycznych ograniczeń architektonicznych typu **Air-Gapped Logic**. Oznacza to, że poszczególne domeny systemu komunikują się pomiędzy sobą wyłącznie za pośrednictwem ustalonych interfejsów (Abstrakcji), a wewnętrzna implementacja poszczególnych modułów (silników, konektorów danych) jest ukryta.

Takie podejście umożliwia:

1.  **Łatwą wymianę modułów (Pluggability)** – możliwość zastąpienia jednego dostawcy danych finansowych innym, bez najmniejszej modyfikacji w kodzie odpowiadającym za silnik zasymulowanych transakcji.
2.  **Architekturę Dual-Engine (BYOL)** – zdolność aplikacji do pracy przy użyciu darmowych, otwartoźródłowych bibliotek w trybie domyślnym, przy równoczesnym wsparciu dla zaawansowanych, płatnych narzędzi (technika Bring Your Own License), wprowadzanych do środowiska w czasie rzeczywistym.
3.  **Integrację Algorytmów Sztucznej Inteligencji** – agregację wyjścia z testowanej strategii i automatyczną ekspozycję do nowoczesnych Dużych Modeli Językowych (LLM) za pomocą ustandaryzowanych wektorów wiedzy (Model Context Protocol).
