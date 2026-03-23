# 📈 BlockBT — Algorithmic Backtesting Ecosystem

BlockBT to zaawansowane środowisko do testowania strategii inwestycyjnych typu "Self-Hosted", zbudowane dla inżynierów i analityków Quant. System łączy potęgę biblioteki `vectorbt` z nowoczesnym interfejsem Streamlit oraz analityką AI.

## 🚀 Szybki Start (Instalacja)

Aby uruchomić projekt lokalnie, wykonaj poniższe kroki:

### 1. Klonowanie i Środowisko
```bash
git clone <repository_url>
cd my_project
python -m venv .venv
source .venv/bin/activate  # lub .venv\Scripts\activate na Windows
```

### 2. Instalacja zależności
```bash
pip install --upgrade pip
pip install -e .
```

### 3. Konfiguracja (Baza Danych)
Projekt korzysta z SQLite. Przy pierwszym uruchomieniu tabele zostaną utworzone automatycznie, lub możesz użyć migruacji:
```bash
alembic upgrade head
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

## 👤 Autor & Licencja
Stworzone przez: **przydan**
Licencja: MIT / Proprietary (dla modułów PRO)
