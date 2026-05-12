# Frontend - Architecture & State

Frontend aplikacji BlockBT to nowoczesna aplikacja typu Single Page (SPA) zbudowana w oparciu o bibliotekę React oraz system budowania Vite. Została zaprojektowana z myślą o wysokiej wydajności interfejsu wizualnego oraz ścisłym typowaniu danych.

## Stos Technologiczny

- **Framework**: React 18.3+ (Functional Components, Hooks).
- **Język**: TypeScript (rygorystyczne typowanie schematów API i stanu).
- **Budowanie**: Vite (zapewnia błyskawiczny HMR i zoptymalizowany build).
- **Stylizacja**: Tailwind CSS + PostCSS (architektura Utility-first).
- **Ikony**: Lucide React.

---

## Zarządzanie Stanem

BlockBT stosuje hybrydowe podejście do zarządzania stanem, rozdzielając dane pochodzące z serwera od stanu interfejsu użytkownika.

### TanStack Query (Server State)
Zarządza danymi pobieranymi z backendu (lista strategii, wyniki backtestów, ustawienia).
- **Cache**: Dane są przechowywane w pamięci podręcznej z domyślnym `staleTime` równym 30 sekund.
- **Synchronizacja**: Automatyczne odświeżanie danych w tle i obsługa stanów ładowania/błędów.
- **Konfiguracja**: Główny klient zdefiniowany w `frontend/src/main.tsx`.

### Zustand (Client State)
Zarządza stanem, który nie wymaga synchronizacji z bazą danych w czasie rzeczywistym lub jest specyficzny dla UI.
- **`workflowStore.ts`**: Serce wizualnego kreatora. Przechowuje pozycje węzłów (React Flow), połączenia między nimi oraz lokalny stan parametrów wewnątrz węzłów.
- **`chatStore.ts`**: Zarządza historią rozmowy w panelu bocznym.
- **Zaleta**: Lekka i szybka alternatywa dla Reduxa, idealna dla dynamicznych grafów React Flow.

---

## Komunikacja z API

Warstwa usług (`frontend/src/services/api.ts`) stanowi jedyny punkt kontaktu z backendem.

- **Typowanie**: Wszystkie żądania i odpowiedzi są typowane za pomocą `api.d.ts`, generowanego automatycznie ze specyfikacji OpenAPI backendu.
- **Vite Proxy**: W trybie deweloperskim Vite przekierowuje zapytania z `/api` na `http://127.0.0.1:8000`, co eliminuje problemy z CORS.
- **Wzorzec Request**: Enkapsulacja `fetch` z logowaniem żądań w konsoli (w trybie dev) i ujednoliconą obsługą błędów.

---

## Struktura Katalogów (`/src`)

Aplikacja jest zorganizowana modularnie:
- **`features/`**: Większe moduły funkcjonalne (np. `visual_builder`, `ai_chat`).
- **`flows/`**: Komponenty i konfiguracje specyficzne dla React Flow (edytor grafu).
- **`components/`**: Komponenty wspólne (layout, UI, przyciski).
- **`hooks/`**: Niestandardowe hooki Reacta (np. `useWorkflowExecution` – orkiestrator uruchamiania zadań).
- **`store/`**: Definicje sklepów Zustand.
- **`services/`**: Klient API i definicje typów OpenAPI.
- **`pages/`**: Główne widoki aplikacji (Builder, Settings).

---

## Routing i Nawigacja

Aplikacja wykorzystuje `react-router-dom` do obsługi nawigacji:
- **`/`**: `BuilderPage` – główny pulpit z wizualnym edytorem i panelami wyników.
- **`/settings`**: `SettingsPage` – konfiguracja parametrów globalnych systemu.
