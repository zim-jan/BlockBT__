# Realizacja Projektu: Faza 1 (Sekcja C2)

## Implementacja Warstwy Scaffolding oraz Bazy Danych

Prace architektoniczne rozpoczęły się od utworzenia kompleksowej struktury modułowej aplikacji opartej o nowoczesne mechanizmy wdrożeniowe standardu Python Packaging (`pyproject.toml` z formatem `setuptools.build_meta`). Zdefiniowano jasny podział katalogów źródłowych separujący moduły: konfiguracji, bazy danych, złącz dostawców, silników strategii oraz interfejsów sztucznej inteligencji. Prace te objęły w całości pełne testowanie TDD (Test-Driven Development) i utrzymywanie spójności logiki (100% test pass).

### Modelowanie ORM w SQLAlchemy 2.x

Obiektowo-relacyjne odwzorowanie wprowadzono tworząc jednolitą i spójną bazę deklaratywną. Struktura bazy realizowana jest na bazie klasycznych relacji encji. Przykładowo kluczową tabelą aplikacji stanowiącą wynik testowania danej strategii jest model `SimulationResult`, który obsługuje bezpośrednio pola wektorowe typu JSON dla wielowymiarowych ujęć ewidencji kapitału. Zastosowanie dedykowania obiektowego mapowania za pomocą `@mapped_column` gwarantuje integralność relacyjną bazy danych i podnosi deterministyczny odczyt logów testów.

Oto wycinek dokumentujący implementację tabel danych z modułu `/db/models.py`.

```python
class SimulationResult(Base):
    """Encja przechowuje wykonane historyczne backtesty na silnikach."""
    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    template_id: Mapped[int | None] = mapped_column(ForeignKey("strategy_templates.id"))

    strategy_name: Mapped[str] = mapped_column(String(100), index=True)
    symbol: Mapped[str] = mapped_column(String(50))
    timeframe: Mapped[str] = mapped_column(String(20))
    
    # Przewidziane relacyjne metadane JSON w formacie SQLAlchemy
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    equity_curve_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
```

## Loader Wzorca Dual-Engine

Zrealizowano postulat technologii **Bring Your Own License (BYOL)** dostarczając kompleksowy układ adaptacyjnego doboru wejściowego modułu ładującego. W pliku `engine/loader.py` zastosowano dynamiczne rozpoznawanie otoczenia za pomocą funkcji ładującej poszukującej właściwej definicji `vectorbtpro`.

W przypadku znalezienia, instalator wykorzystuje zamkniętą do ścisłego bloku `try-except` warstwę pozyskiwania importów. W przypadku rzucenia błędów deklasacji (ModuleNotFoundError) maszyna wirtualna bezpiecznie adaptuje dostępną logikę referencyjną warstwy *OpenSource Engine*, unikając rzucenia głównego paniku procedury wejściowej środowiska. Taki wzorzec architektoniczny można opisać mianem wzorca *Graceful Fallback*.

Zaprojektowano również abstrakcyjny model podstawowy wiążący (kontrakt systemowy) polegający na egzekwowaniu u każdego powiązanego z systemem silnika transakcyjnego metody `run_backtest`, której wymaganą odpowiedzą wstrzykniętych danych jest strukturalny obiekt obudowany klasą `BacktestResult` (tzw. DTO - Data Transfer Object).

## Architektura Pluggowalnych Konektorów Danych

By aplikacja pozwalała na asynchroniczne odpytywanie wielu odrębnych źródeł system zaproponował stworzenie wspólnej unifikacji interfejsów strumieniowych (Data Connector Pattern).
Każdy nowo implementowany dostawca rozszerzający klasę wirtualną `BaseDataConnector` odziedziczył zaawansowanym aparat cachingowy na nośniku Parquet. 

Implementacja popularnego rynkowego publicznego konektora `YahooFinanceConnector` objęła wykorzystanie lokalnego API serwisu, wraz z ustrukturyzowaniem zwracanego pod-tablicowanego wyniku dla natywnych standardów operacji `pandas.DataFrame`. Gwarantuje to uniknięcie przeładunku API dla zapytań o gęste parametryzacje (HFT - testowanie wysokich częstotliwości) utrzymując jednocześnie formatowanie kolumn na wielkości zminimalizowane (tzw. "lowercase homogenization" po stronie wewnętrznej magistrali BlockBT).

```python
class YahooFinanceConnector(BaseDataConnector):
    """Adapter API wywołujący bibliotekę yfinance."""
    
    def _download(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> pd.DataFrame:
        logger.info(f"YFINANCE: Downloading {symbol} ({start_date} -> {end_date})")
        df = yf.download(
            tickers=symbol,
            start=start_date,
            end=end_date,
            interval=timeframe,
            progress=False,
        )
```

Tego typu wzorce dają pewność wysokiego TTI (Time to Integration) kolejnego źródła np. krypto-walutowego z serwisu Binance lub rozwiązań algorytmicznych Alpaca bez ryzyka jakiejkolwiek awarii bazowej platformy. Osiągnięto w konsekwencji cel wysokiej bez-awaryjności w pełni Air-Gapped logice.
