### Pomysły
#### 1. Dodanie modułu do tworzenia lub edytowania algorytmów. Z boku Wskazóœki gdzie szukać darmowych algorytmów. 

- rozszerzenie bazy o tabele trzymającą algorytmy per user
- walidacja kodu ze wskazaniem w której linijce jest błąd

#### 2. Możliwość edycji system prompta do analizy strategii. 

- trzymanie w bazie system prompta per user
- pierwszy niech bedzie domyslny 
- uzytkownik moze zapisać kilka system promptów

#### 3. Najbliższe refaktoryzaje i usprawnienia 

BlockBT MVP - Lista To-Do (Faza Poprawek i Refaktoryzacji UX/UI)

##### Task 8: Reorganizacja Architektury Interfejsu (Nawigacja i Ustawienia)
Usunięcie modułu Dashboard: Likwidacja zakładki wprowadzającej niejednoznaczność.

Nowy moduł Preferencje: Stworzenie zakładki do globalnej konfiguracji dostawców danych (Yahoo Finance - parametryzacja; Alpaca - pola na klucze API/Secret).

Utrzymanie modułu Market Data: Pozostawienie sekcji do przeglądu i pobierania danych giełdowych.

##### Task 9: Konsolidacja "Zarządzania Strategiami" (Kreator / Wizard)
Połączenie funkcjonalności: Zintegrowanie kreatora, optymalizatora i narzędzi do testowania w jeden, spójny przepływ (Workflow).

Wyszukiwarka Tickerów: Wdrożenie wyszukiwania nie tylko po symbolu, ale i po nazwie spółki (np. z wykorzystaniem pakietu yfinance lub wbudowanej słownikowej bazy popularnych tickerów).

Rozszerzenie bazy strategii: Wystawienie natywnych wskaźników vectorbt (RSI, MACD, BBANDS) jako dynamicznej, rozwijanej listy do wyboru w Wizardzie, zamiast jednej zahardkodowanej opcji.

##### Task 10: Naprawa i Rozbudowa "Visual Buildera" (Drag & Drop)
Naprawa interaktywności: Zdiagnozowanie i naprawa problemów z frameworkiem graficznym (brak możliwości przesuwania bloków i dodawania powiązań – prawdopodobnie problem z odświeżaniem stanu w Streamlit).

Kafelki Wskaźników: Usunięcie zahardkodowanej strategii i dodanie bocznego panelu z kafelkami reprezentującymi różne wskaźniki vectorbt do przeciągania na pole robocze.

##### Task 11: Naprawa Architektury Dual-Engine (Przełącznik OS/PRO)
Diagnostyka błędu: Naprawa mechanizmu zmiany silnika w locie. Aktualnie przełączenie z OpenSource na PRO nie działa (prawdopodobnie mechanizm ładujący engine.loader nieprawidłowo przechwytuje stan w Streamlit lub brakuje obsługi błędu, gdy brakuje paczki vectorbtpro).