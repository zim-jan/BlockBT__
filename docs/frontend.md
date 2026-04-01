# Frontend (React)

Warstwa interfejsu użytkownika **BlockBT** została całkowicie przeprojektowana i unowocześniona. Porzucono pierwotne, prototypowe rozwiązanie oparte na bibliotece Streamlit na rzecz profesjonalnej i wydajnej architektury **Single-Page Application (SPA)** zbudowanej w oparciu o **React**, **TypeScript** i narzędzie budujące **Vite**.

## Założenia Architektoniczne

Frontend został zaprojektowany zgodnie ze standardami branżowymi, kładąc nacisk na modularność, przewidywalność stanu i izolację logiki biznesowej od warstwy prezentacji.

1.  **Feature-Driven Architecture (Architektura oparta na funkcjonalnościach)**
    Struktura projektu wewnątrz katalogu `src/` opiera się na podziale funkcjonalnym, a nie wyłącznie na typach plików. Kod specyficzny dla danej domeny biznesowej (np. moduł konfiguracji strategii, moduł wizualizacji wyników backtestingu) jest zgrupowany w dedykowanych folderach wewnątrz `src/features/`.
2.  **Globalna Infrastruktura**
    Kod współdzielony, który nie przynależy do żadnej konkretnej funkcjonalności (np. globalne hooki, usługi API, konfiguracja Redux/Zustand, typy generyczne), znajduje się bezpośrednio w głównych podkatalogach `src/` (tj. `src/hooks/`, `src/services/`, `src/store/`, `src/types/`).
3.  **App.tsx jako Minimalny Kontener**
    Główny komponent `App.tsx` pełni rolę wyłącznie orkiestratora i kontenera dla globalnych dostawców kontekstu (Context Providers), takich jak provider routingu, provider stanu czy provider motywu. Właściwa struktura strony głównej i zarządzanie widokami (np. `BuilderPage.tsx`) delegowane są głębiej.
4.  **Globalny Layout i Stan Systemu**
    Wskaźniki stanu całego systemu (np. status połączenia z backendem, wskaźniki zdrowia - health indicators) są zintegrowane na poziomie globalnego komponentu `MainLayout`, zapewniając spójne doświadczenie użytkownika niezależnie od aktualnie wyświetlanego widoku.

## Konwencje i Ograniczenia

Podczas rozwoju frontendu React należy bezwzględnie przestrzegać następujących reguł:

*   **Brak autoryzacji:** System MVP nie posiada i nie planuje implementacji mechanizmów logowania, rejestracji ani autoryzacji (JWT, OAuth itp.). Interfejs musi zakładać dostęp dla pojedynczego, lokalnego użytkownika.
*   **Izolacja (Air-gapped):** Frontend nie powinien zawierać żadnego kodu śledzącego, analityki (np. Google Analytics), ani odwoływać się do zewnętrznych zasobów CDN (fonty, skrypty) w sposób uniemożliwiający pracę bez dostępu do Internetu. Wszystkie zasoby muszą być hostowane lokalnie.
*   **Brak plików Barrel (index.ts) dla eksportów funkcjonalności:** Zgodnie z wytycznymi projektu, aby uniknąć problemów z cyklicznymi zależnościami i ułatwić analizę statyczną kodu, zabrania się stosowania plików `index.ts` jako punktów zbiorczego eksportu wewnątrz katalogów `src/features/`. Należy używać bezpośrednich, jawnych importów plików (np. `import MyComponent from "../features/my_feature/MyComponent"`).
*   **Usuwanie pustych katalogów:** Po refaktoryzacji lub przeniesieniu plików, puste lub osierocone katalogi muszą być całkowicie usuwane z drzewa plików, aby utrzymać czystość struktury.
*   **Bindowanie serwera deweloperskiego Vite:** W przypadku uruchamiania serwera deweloperskiego Vite wewnątrz kontenera Docker, należy wymusić nasłuchiwanie na wszystkich interfejsach za pomocą parametru `host: '0.0.0.0'`. Konfiguracja proxy dla żądań API musi kierować ruch na wewnętrzną nazwę DNS kontenera backendu (np. `http://blockbt-api:8000`), a nie na `127.0.0.1`.
