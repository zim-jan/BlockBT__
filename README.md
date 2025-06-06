## Projekt: Web‑owa platforma "BlockBT" (może być do zmiany)

### 1. Zakres MVP

| #  | Element                                    | Definicja ukończenia (DoD)                                                                                                                          |
|----|--------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | **Edytor bloków**                          | Drag‑and‑drop oparte na **Blockly / Scratch‑blocks**; Input Data, Math Ops, Output Buckets                                                           |
| 2  | **Generator kodu**                         | Mapowanie bloków do kodu Python (PEP‑8).                                                                                                            |
| 3  | **SandboxPython**                          | Wykonanie kodu (limit CPU + czas + RAM, brak sieci) zwrócenie wyników symulacji.                                                                    |
| 5  | **Analiza wyników**                        | Backend wykonuje analizę statystyczną wyników symulacji i renderuje strone z podsumowaniem wyników (Tabele i wykresy).                              |
| 6  | **Baza danych**                            | PostgreSQL: tabele *users, block_sequences, runs, run_results*. Plus szyforwanie danych.                                                            |
| 8  | **Panel admina**                           | Django‑admin z listą użytkowników, sekwencjami użytkowników, logów sandboxa użytkowników                                                            |
| 9  | **Podstawowe testy i Pipeline CI/CD**      | -/-                                                                                                                                                 |
| 10 | **Dokumentacja**                           | Dokumentacja wewnętrzna oraz poradnik korzystania z aplikacji.                                                                                      |

### 2. Architektura

```
┌───────────┐     HTTP/REST      ┌────────────┐
│ React/TS  │  ◄───────────────► │ Django API │
│  (Next.js)│                    │  + DRF     │
└───────────┘                    └────┬───────┘
      ▲  WebSockets (podgląd)          │
      │                                ▼
Blockly/Scratch‑blocks            Sandbox Manager
      │                                │  docker run
      ▼                                ▼
UI → JSON AST → CodeGen         Isolated Python container
```

* **Front‑end**: Next.js14, React‑18, TypeScript, Tailwind CSS.  
  *Drag‑and‑drop*: `react‑blockly`.
* **API**: Django5 + DjangoRestFramework.  
* **Symulator**: VectorBt.PRO
* **Docker**: Do wykonywania symulacji z ogranicząną ilością zasobów

### 3. Rozszerzenia po MVP

| Funkcja                | Uwagi                                                  |
|------------------------|--------------------------------------------------------|
| OAuth                  | Logowanie poprzez Google, GitHub itp...                |
| Role „Silver/Gold”     | Zwiększony limit CPU, czas, RAM                        |
| MobileUI               | React Native Expo lub PWA                              |
| Community gallery      | Możliwość udostępniania wyników na publiczny ranking   |