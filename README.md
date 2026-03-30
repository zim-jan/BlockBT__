# 📈 BlockBT — Algorithmic Backtesting Ecosystem

BlockBT to zaawansowane środowisko do testowania strategii inwestycyjnych typu "Self-Hosted", zbudowane dla inżynierów i analityków Quant. System łączy potęgę biblioteki `vectorbt` z nowoczesnym interfejsem React oraz analityką AI.
<img width="1865" height="1102" alt="obraz" src="https://github.com/user-attachments/assets/897ce675-d24e-4ecf-8720-b43cf11d25a1" />


## 🚀 Szybki Start (Instalacja)

Aby uruchomić projekt lokalnie **bez użycia Dockera**, wykonaj poniższe kroki. Projekt składa się z dwóch części: backendu w FastAPI (Python) oraz frontendu w React (Vite).

### 1. Przygotowanie Backendu (Python/FastAPI)

Najlepiej użyć narzędzia [uv](https://github.com/astral-sh/uv):

```bash
# Pobierz konkretną wersję Pythona (jeśli jej nie masz):
uv python install 3.12

# Utwórz środowisko przypisane do Pythona 3.12
uv venv --python 3.12

# Aktywuj środowisko (Linux/macOS)
source .venv/bin/activate

# Instalacja zależności
uv pip install -e .
```

**Konfiguracja zmiennych środowiskowych**
Backend wymaga zmiennej `SECRET_KEY` (oraz innych ew. zmiennych) w pliku `.env`. Możesz wygenerować go poleceniem:
```bash
echo "SECRET_KEY=$(dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64)" > .env
```

Baza danych SQLite oraz cache Parquet domyślnie zapiszą się w lokalnych katalogach `local_data/db/` i `local_data/cache/` (w głównym folderze projektu).

**Uruchomienie Backendu**
W osobnej karcie terminala uruchom serwer deweloperski FastAPI na porcie 8000:
```bash
# Upewnij się, że .venv jest aktywowane!
uvicorn blockbt.api.main:app --reload --host 127.0.0.1 --port 8000
```
API będzie dostępne pod [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Przygotowanie Frontendu (Node.js/React)

Wymagany jest zainstalowany [Node.js](https://nodejs.org/) (najlepiej w wersji 18+).

```bash
# Przejdź do folderu frontendu
cd frontend

# Zainstaluj pakiety
npm install

# Uruchom serwer deweloperski Vite na porcie 3000
npm run dev
```
Aplikacja Frontendowa będzie dostępna pod adresem: [http://localhost:3000](http://localhost:3000). Serwer automatycznie kieruje zapytania API (proxy) do lokalnego backendu na porcie 8000.

### ⚡ Sposób Alternatywny: Skrypt All-in-One (`run_local.sh`)

Zamiast uruchamiać wszystko osobno, możesz użyć wbudowanego skryptu (wymaga powłoki Bash):

```bash
chmod +x run_local.sh
./run_local.sh
```
Skrypt ten automatycznie wygeneruje `.env` z `SECRET_KEY` (jeśli go nie ma), upewni się, że masz pobrane zależności Node.js (`npm install`), a następnie wystartuje równocześnie backend (FastAPI) w tle oraz frontend na pierwszym planie. Zakończenie skryptu `Ctrl+C` poprawnie zatrzyma oba procesy.

### 4. vectorbt
```bash
# VectorBT OpenSource
git clone https://github.com/polakowo/vectorbt.git
```

## 🏗️ Kluczowe Funkcje

- **Dual-Engine Architecture**: Obsługa `vectorbt` (Open Source) oraz dynamiczne ładowanie ProEngine (BYOL).
- **Visual Builder**: Kreator strategii typu Drag & Drop oparty na React Flow.
- **AI Analyst**: Automatyczna interpretacja wyników backtestu przez lokalne modele LLM (Llama/Qwen via Ollama).
- **Market Connectors**: Zintegrowane pobieranie danych z Yahoo Finance i Alpaca z cache'owaniem Parquet.
- **Optimizer**: Poszukiwanie parametrów optymalnych metodą Bayesowską (Optuna).

## 📚 Dokumentacja dla Deweloperów

Jeśli chcesz rozszerzyć możliwości BlockBT, zajrzyj do dedykowanych przewodników w folderze `docs/developer/`:

- [Mata Architektury](docs/developer/overview.md)
- [Dodawanie Nowych API](docs/developer/extending_data.md)
- [Rozszerzanie GUI i Węzłów](docs/developer/extending_gui.md)
- [Zarządzanie Bazą Danych](docs/developer/extending_db.md)

## 📚 Uruchomienie mkdocs
```bash
uv sync --extra dev
uv run mkdocs serve
```

```bash
dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64
```

## 👤 Autor & Licencja
Stworzone przez: **przydan**
Licencja: MIT / Proprietary (dla modułów PRO)
