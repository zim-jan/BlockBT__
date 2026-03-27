# 📈 BlockBT — Algorithmic Backtesting Ecosystem

BlockBT to zaawansowane środowisko do testowania strategii inwestycyjnych typu "Self-Hosted", zbudowane dla inżynierów i analityków Quant. System łączy potęgę biblioteki `vectorbt` z nowoczesnym interfejsem Streamlit oraz analityką AI.

## 🚀 Szybki Start (Instalacja)

Aby uruchomić projekt lokalnie, wykonaj poniższe kroki:

### Opcja A: Tradycyjny `pip`
```bash
python -m venv .venv
source .venv/bin/activate  # lub .venv\Scripts\activate na Windows
pip install --upgrade pip
pip install -e .
```

### Opcja B: Nowoczesny `uv` (Zalecane — Szybciej ⚡)
Jeśli masz zainstalowany [uv](https://github.com/astral-sh/uv):
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```
Możesz również po prostu uruchomić aplikację bez ręcznej aktywacji środowiska:
```bash
uv run streamlit run app.py
```

### Opcja C:
Usuń błędne środowisko: 
```bash
rm -rf .venv
```
Pobierz konkretną wersję Pythona (jeśli jej nie masz):
```bash
uv python install 3.12
```

Utwórz środowisko twardo przypisane do 3.12:
```bash
uv venv --python 3.12

```

Aktywuj je w swoim terminalu (fish):
```bash
source .venv/bin/activate.fish
```

Ponów instalację:
```bash
uv pip install -e .
```

### 3. Konfiguracja (Baza Danych)
Projekt korzysta z SQLite. Przy pierwszym uruchomieniu tabele zostaną utworzone automatycznie, lub możesz użyć migruacji:
```bash
alembic upgrade head
```

### 4. vectorbt i vectorbt.pro
```bash
# VectorBT OpenSource
git clone https://github.com/przydan/vectorbt.git

# VectorBT PRO
unzip
go to folder 
uv pip install -U ".[base]"
```

### 4. Uruchomienie Aplikacji
```bash
streamlit run app.py
```
Aplikacja będzie dostępna pod adresem: [http://localhost:8501](http://localhost:8501)

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
