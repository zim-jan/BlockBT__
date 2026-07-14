import ast
import builtins
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from app.services.engine.indicator_registry import IndicatorRegistry


class IndicatorService:
    """
    Service for generating entry and exit signals (entries/exits) based on OHLCV data.
    Supports native vectorbt vectorization for parameters and dynamic registry.
    """

    # --- Faza 11: sandbox dla kodu użytkownika (walidator AST deny-by-default) ---
    # Dozwolone typy węzłów AST. Wszystko spoza tej listy jest odrzucane —
    # w szczególności Import/ImportFrom, ClassDef, With, Try, Raise, Global,
    # Yield, Await (nie ma ich tutaj → walidator je blokuje).
    _ALLOWED_AST_NODES: frozenset[str] = frozenset(
        {
            "Module", "FunctionDef", "arguments", "arg", "Return",
            "Assign", "AugAssign", "AnnAssign", "Expr", "Pass",
            "If", "IfExp", "For", "While", "Break", "Continue",
            "Name", "Load", "Store",
            "Constant",
            "BinOp", "UnaryOp", "BoolOp", "Compare",
            "Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow",
            "LShift", "RShift", "BitOr", "BitXor", "BitAnd", "MatMult",
            "Invert", "Not", "UAdd", "USub",
            "And", "Or",
            "Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "Is", "IsNot", "In", "NotIn",
            "Call", "keyword", "Starred",
            "Attribute",
            "Subscript", "Slice", "Tuple", "List", "Dict", "Set",
            "ListComp", "SetComp", "DictComp", "GeneratorExp", "comprehension",
            "Lambda",
        }
    )

    # Nazwy zabronione (ucieczki z sandboxa: introspekcja, I/O, dostęp systemowy).
    # Import tych modułów jest już blokowany przez brak Import/ImportFrom w
    # `_ALLOWED_AST_NODES`; nazwy trzymamy dodatkowo jako obronę w głąb.
    _FORBIDDEN_NAMES: frozenset[str] = frozenset(
        {
            "eval", "exec", "compile", "open", "__import__", "input",
            "getattr", "setattr", "delattr", "hasattr",
            "globals", "locals", "vars", "dir", "breakpoint",
            "object", "type", "super", "memoryview", "help",
            "exit", "quit", "classmethod", "staticmethod",
            "os", "sys", "subprocess", "socket", "shutil", "importlib",
            "builtins", "__builtins__", "pickle", "marshal", "ctypes",
        }
    )

    # Niebezpieczne nazwy atrybutów (NIE-dunder). Blokada dunderów łapie
    # `__class__`/`__globals__`, ale poniższe atrybuty są zwykłymi nazwami i
    # otwierają ucieczkę z sandboxa: dostęp do ramek/globalsów przez generatory,
    # surowa pamięć/interfejs C numpy oraz zapis dowolnego pliku na dysk
    # (serializatory pandas/numpy) — krytyczne w trybie Air-Gapped.
    _FORBIDDEN_ATTRIBUTES: frozenset[str] = frozenset(
        {
            # ramki wykonania / generatory / korutyny → f_globals (nie-dunder!)
            "gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame",
            "f_globals", "f_locals", "f_back", "f_builtins", "f_code",
            "func_globals", "func_code", "func_closure",
            # surowa pamięć / interfejs C numpy
            "ctypes", "tobytes", "tostring", "getbuffer", "setflags",
            # zapis na dysk (numpy)
            "tofile", "save", "savez", "savetxt",
            # zapis / serializacja na dysk (pandas)
            "to_pickle", "to_csv", "to_parquet", "to_hdf", "to_sql",
            "to_json", "to_feather", "to_excel", "to_xml", "to_html",
            "to_latex", "to_stata", "to_gbq", "to_clipboard", "to_orc",
            # wykonanie procesów / serializacja bajtów
            "system", "popen", "spawn", "communicate", "dump", "dumps",
            # str.format sięga atrybutów przez pola '{0.__globals__}' → obejście
            # zakazu dunderów; wskaźnik liczbowy nie potrzebuje formatowania stringów.
            "format", "format_map",
        }
    )

    # Minimalny, bezpieczny zestaw wbudowanych funkcji udostępniany kodowi usera.
    _SAFE_BUILTIN_NAMES: tuple[str, ...] = (
        "abs", "min", "max", "len", "range", "enumerate", "zip", "sum",
        "round", "float", "int", "bool", "str", "list", "dict", "tuple",
        "set", "sorted", "reversed", "map", "filter", "any", "all",
        "pow", "divmod", "print",
    )

    @classmethod
    def _safe_builtins(cls) -> dict[str, Any]:
        """Faza 11: buduje słownik dozwolonych wbudowanych funkcji dla sandboxa."""
        return {name: getattr(builtins, name) for name in cls._SAFE_BUILTIN_NAMES}

    @classmethod
    def _validate_code_safety(cls, code: str) -> ast.Module:
        """
        Faza 11 (bezpieczeństwo eval/exec): statyczna analiza AST kodu użytkownika.

        Model deny-by-default: dozwolone są tylko węzły z `_ALLOWED_AST_NODES`.
        Dodatkowo blokujemy dostęp do atrybutów dunder (np. `__globals__`,
        `__class__`) oraz użycie niebezpiecznych nazw wbudowanych. Każde
        naruszenie kończy się `ValueError` z frazą "Unsafe code detected".
        """
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as exc:
            raise ValueError(
                f"Unsafe code detected: niepoprawna składnia ({exc})."
            ) from exc

        for node in ast.walk(tree):
            node_name = type(node).__name__
            if node_name not in cls._ALLOWED_AST_NODES:
                raise ValueError(
                    f"Unsafe code detected: niedozwolona konstrukcja '{node_name}'."
                )
            if isinstance(node, ast.Attribute) and (
                node.attr.startswith("__")
                or node.attr.endswith("__")
                or node.attr in cls._FORBIDDEN_ATTRIBUTES
            ):
                raise ValueError(
                    f"Unsafe code detected: dostęp do atrybutu '{node.attr}' zabroniony."
                )
            if isinstance(node, ast.Name) and node.id in cls._FORBIDDEN_NAMES:
                raise ValueError(
                    f"Unsafe code detected: użycie nazwy '{node.id}' zabronione."
                )

        return tree

    @classmethod
    def compile_custom_indicator(cls, code: str) -> Any:
        """
        Faza 11 (Filary 2 i 3): kompiluje wskaźnik zdefiniowany przez użytkownika.

        Kroki:
        1. Walidacja AST (sandbox — brak importów, eval/exec, dostępu systemowego).
        2. Bezpieczne wykonanie kodu w zamkniętej przestrzeni nazw → wyciągnięcie
           funkcji rdzenia liczbowego.
        3. Kompilacja rdzenia numba `@njit` ("Prędkość C") i opakowanie w
           `vbt.IndicatorFactory` — zwracana klasa udostępnia metodę `.run(...)`.

        Kompilacja numba jest leniwa (następuje przy pierwszym `.run()`), więc
        samo zbudowanie fabryki nie wymaga, by kod był w pełni numba-zgodny.
        """
        tree = cls._validate_code_safety(code)

        import vectorbt as vbt_mod
        from numba import njit

        # Jedna wspólna przestrzeń nazw (globals == locals). Kluczowe dla kontraktu
        # funkcji pomocniczych: definicje najwyższego poziomu lądują w `safe_ns`,
        # a każda funkcja rozwiązuje wolne nazwy przez własne `__globals__` = `safe_ns`.
        # Rozdzielone globals/locals sprawiały, że rdzeń wołający helpera dostawał
        # `NameError` przy `.run()` (helper był niewidoczny w globalsach funkcji).
        safe_ns: dict[str, Any] = {
            "__builtins__": cls._safe_builtins(),
            "np": np,
        }
        try:
            exec(compile(code, "<custom_indicator>", "exec"), safe_ns)
        except Exception as exc:
            raise ValueError(
                f"Unsafe code detected: błąd wykonania kodu wskaźnika ({exc})."
            ) from exc

        # Kontrakt: PIERWSZA funkcja najwyższego poziomu = rdzeń wskaźnika,
        # kolejne (jeśli są) traktujemy jako pomocnicze. Wybór po AST (kolejność
        # źródłowa) jest deterministyczny i udokumentowany — inaczej niż wcześniejsze
        # `funcs[-1]`, które przy funkcji-helperze na końcu liczyło zły rdzeń.
        func_names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        if not func_names:
            raise ValueError(
                "Kod wskaźnika musi definiować funkcję (np. 'def custom_oscillator(close): ...')."
            )
        user_fn = safe_ns.get(func_names[0])
        if not callable(user_fn):
            raise ValueError("Nie udało się pobrać funkcji wskaźnika z kodu użytkownika.")

        # Kontrakt dla użytkownika: funkcja przyjmuje 1-wymiarową serię cen
        # (numpy) i zwraca 1-wymiarowy wynik. Rdzeń liczbowy kompilujemy @njit
        # ("Prędkość C"); kompilacja jest leniwa — następuje przy pierwszym `.run()`.
        #
        # njit-ujemy KAŻDĄ funkcję najwyższego poziomu i podmieniamy ją w safe_ns.
        # Numba w trybie nopython nie potrafi wywołać zwykłej funkcji-globala
        # (TypingError: untyped global), więc helper wołany przez rdzeń też musi być
        # dispatcherem njit. njit jest leniwe — owinięcie nieużywanego helpera nic
        # nie kosztuje (skompiluje się dopiero przy realnym wywołaniu z rdzenia).
        for name in func_names:
            fn = safe_ns.get(name)
            if callable(fn):
                try:
                    safe_ns[name] = njit(fn)
                except Exception:  # pragma: no cover - nietypowe domknięcia
                    logger.warning(
                        "compile_custom_indicator: njit nie owinął '{}', fallback bez JIT", name
                    )
        jit_core = safe_ns.get(func_names[0])

        def apply_func(close: np.ndarray) -> np.ndarray:
            """
            Adapter kontraktu: vbt przekazuje tablicę 2D (wiersze=czas, kolumny=symbole).
            Aplikujemy rdzeń 1D per kolumnę — dzięki temu użytkownik pisze prostą
            funkcję jednowymiarową, a wektoryzacja po symbolach dzieje się tutaj.
            """
            arr = np.asarray(close, dtype=np.float64)
            if arr.ndim == 1:
                return np.asarray(jit_core(np.ascontiguousarray(arr)), dtype=np.float64)
            out = np.empty_like(arr, dtype=np.float64)
            for col in range(arr.shape[1]):
                out[:, col] = np.asarray(
                    jit_core(np.ascontiguousarray(arr[:, col])), dtype=np.float64
                )
            return out

        factory = vbt_mod.IndicatorFactory(
            input_names=["close"], output_names=["out"]
        ).from_apply_func(apply_func)
        return factory

    @staticmethod
    def _get_val(params: dict[str, Any], key: str, default: Any) -> Any:
        """Helper to extract a parameter value, supporting lists for vectorization."""
        val = params.get(key, default)
        if isinstance(val, (list, np.ndarray, pd.Series)):
            return val
        try:
            # Try to convert to int if it's a simple scalar string/float
            return int(val)
        except (TypeError, ValueError):
            return val

    @staticmethod
    def _is_param_list(*params: Any) -> bool:
        """Faza 10: wykrywa wektoryzację parametrów (lista/tablica okien)."""
        return any(isinstance(p, (list, np.ndarray, pd.Series)) for p in params)

    @staticmethod
    def _guard_multi_symbol_params(close: pd.Series | pd.DataFrame, *params: Any) -> bool:
        """
        Faza 10: zwraca True, gdy close reprezentuje wiele symboli (DataFrame — kolumny=symbole).
        Blokuje jednoczesną wektoryzację parametrów i symboli (poza zakresem Fazy 10).
        """
        is_multi_symbol = isinstance(close, pd.DataFrame)
        if is_multi_symbol and IndicatorService._is_param_list(*params):
            raise ValueError(
                "Faza 10 nie wspiera jednoczesnej wektoryzacji parametrów i symboli "
                "(lista okien + wiele tickerów)."
            )
        return is_multi_symbol

    @staticmethod
    def _align_to_symbols(
        indicator: pd.Series | pd.DataFrame, close: pd.Series | pd.DataFrame
    ) -> pd.Series | pd.DataFrame:
        """
        Faza 10: przy DataFrame wieloma symbolami vbt dokleja poziom parametru (np. 'ma_window')
        do kolumn wskaźnika. Sprowadzamy kolumny z powrotem do czystych symboli (close.columns),
        aby crossed_above/portfel operowały na jednoznacznych kluczach per ticker.
        """
        if isinstance(close, pd.DataFrame) and isinstance(indicator, pd.DataFrame):
            aligned = indicator.copy()
            aligned.columns = close.columns
            return aligned
        return indicator

    @staticmethod
    def generate_sma_crossover(
        close: pd.Series, fast_window: Any, slow_window: Any, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Generate signals based on SMA Crossover strategy.
        Supports vectorization (fast_window and slow_window can be lists).
        Faza 10: obsługuje też DataFrame wielu symboli (broadcasting po kolumnach).
        """
        logger.debug(f"IndicatorService: Generating SMA signals (fast={fast_window}, slow={slow_window})")

        IndicatorService._guard_multi_symbol_params(close, fast_window, slow_window)

        align = IndicatorService._align_to_symbols
        fast_ma = align(vbt.MA.run(close, window=fast_window).ma, close)
        slow_ma = align(vbt.MA.run(close, window=slow_window).ma, close)

        entries = fast_ma.vbt.crossed_above(slow_ma)
        exits = fast_ma.vbt.crossed_below(slow_ma)

        return entries, exits

    @staticmethod
    def generate_macd(
        close: pd.Series, fast: Any, slow: Any, signal: Any, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Generate signals based on MACD strategy.
        Supports vectorization.
        """
        # Defensive defaults — frontend may send None when fields weren't filled
        fast = fast if fast is not None else 12
        slow = slow if slow is not None else 26
        signal = signal if signal is not None else 9

        logger.debug(f"IndicatorService: Generating MACD signals (fast={fast}, slow={slow}, signal={signal})")

        IndicatorService._guard_multi_symbol_params(close, fast, slow, signal)

        macd = vbt.MACD.run(close, fast_window=fast, slow_window=slow, signal_window=signal)
        macd_line = IndicatorService._align_to_symbols(macd.macd, close)
        signal_line = IndicatorService._align_to_symbols(macd.signal, close)

        entries = macd_line.vbt.crossed_above(signal_line)
        exits = macd_line.vbt.crossed_below(signal_line)

        return entries, exits

    @staticmethod
    def generate_custom(
        close: pd.Series, code_content: str, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Execute custom Python/vectorbt code to generate signals.
        The code should define 'entries' and 'exits' variables.
        """
        logger.info("IndicatorService: Executing custom strategy code")

        # Faza 11: sandbox — walidacja AST przed wykonaniem. Zgłasza ValueError
        # ("Unsafe code detected: ...") dla importów/eval/exec/dostępu systemowego.
        IndicatorService._validate_code_safety(code_content)

        # Pojedyncza, zamknięta przestrzeń nazw z ograniczonymi wbudowanymi.
        # Kluczowe: pusty `{}` jako globals i tak wstrzykuje pełne builtins —
        # dlatego jawnie podajemy __builtins__ z bezpiecznego zestawu.
        safe_ns: dict[str, Any] = {
            "__builtins__": IndicatorService._safe_builtins(),
            "close": close,
            "vbt": vbt,
            "np": np,
            "pd": pd,
        }

        try:
            exec(compile(code_content, "<custom_strategy>", "exec"), safe_ns)

            entries = safe_ns.get("entries")
            exits = safe_ns.get("exits")

            if entries is None or exits is None:
                raise ValueError("Custom code must define 'entries' and 'exits' variables.")

            return entries, exits
        except ValueError:
            # Błędy sandboxa / kontraktu przekazujemy bez owijania (czytelny komunikat).
            raise
        except Exception as e:
            logger.error(f"Error executing custom strategy code: {e}")
            raise RuntimeError(f"Custom strategy execution failed: {e}") from e

    @classmethod
    def generate_signals(
        cls, close: pd.Series, params: dict[str, Any], vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Orchestrator for signal generation based on the strategy defined in `params`.
        """
        strategy_type = params.get("strategy_type", "sma_crossover").lower()

        if strategy_type == "custom":
            code_content = params.get("code_content", "")
            if not code_content:
                # Fallback or error? Let's try to find it in parameters if not top-level
                code_content = params.get("parameters", {}).get("code_content", "")
            
            if not code_content:
                raise ValueError("Custom strategy type requested but no code_content provided.")
                
            return cls.generate_custom(close, code_content, vbt)

        if strategy_type == "macd":
            fast = cls._get_val(params, "sma_fast", 12)  # Shared UI fields for simplicity
            if "macd_fast" in params:
                fast = cls._get_val(params, "macd_fast", 12)
            
            slow = cls._get_val(params, "sma_slow", 26)
            if "macd_slow" in params:
                slow = cls._get_val(params, "macd_slow", 26)
                
            signal = cls._get_val(params, "macd_signal", 9)

            return cls.generate_macd(close, fast, slow, signal, vbt)

        # --- Bridge: vbt_MA → SMA crossover using DAG params ---
        if strategy_type == "vbt_ma":
            fast_w = cls._get_val(params, "sma_fast", 10)
            slow_w = cls._get_val(params, "sma_slow", 30)
            logger.info(f"IndicatorService: vbt_MA bridge → SMA crossover (fast={fast_w}, slow={slow_w})")
            import vectorbt as vbt_mod
            return cls.generate_sma_crossover(close, fast_w, slow_w, vbt_mod)

        # --- Bridge: vbt_RSI → threshold-based entries/exits ---
        if strategy_type == "vbt_rsi":
            window = cls._get_val(params, "window", 14)
            oversold = float(cls._get_val(params, "oversold", 30))
            overbought = float(cls._get_val(params, "overbought", 70))
            logger.info(f"IndicatorService: vbt_RSI bridge → threshold (win={window}, OS={oversold}, OB={overbought})")
            import vectorbt as vbt_mod
            cls._guard_multi_symbol_params(close, window)
            rsi = vbt_mod.RSI.run(close, window=window).rsi.astype("float64")
            rsi = cls._align_to_symbols(rsi, close)
            entries = rsi.vbt.crossed_below(oversold)  # Buy when RSI < oversold
            exits = rsi.vbt.crossed_above(overbought)   # Sell when RSI > overbought
            return entries, exits

        # Check Indicator Registry (generic path)
        registered = IndicatorRegistry.get(strategy_type)
        if registered:
            logger.info(f"IndicatorService: Executing registry indicator '{strategy_type}'")
            call_params = {}
            for p in registered["params"]:
                p_name = p["name"]
                if p_name in params:
                    call_params[p_name] = cls._get_val(params, p_name, p["default"])
            
            res = IndicatorRegistry.execute(strategy_type, close, **call_params)
            
            if hasattr(res, "entries") and hasattr(res, "exits"):
                return res.entries, res.exits
            if hasattr(res, "signals"):
                return res.signals, ~res.signals
            
            # Safety: if result is not bool-like, raise clear error
            logger.warning(f"Registry indicator '{strategy_type}' returned non-signal object: {type(res)}")
            raise TypeError(
                f"Registry indicator '{strategy_type}' returned {type(res).__name__}, "
                f"not entries/exits. Add explicit bridge in IndicatorService."
            )

        # Default / Fallback: SMA Crossover
        fast_w = cls._get_val(params, "sma_fast", 10)
        slow_w = cls._get_val(params, "sma_slow", 30)

        return cls.generate_sma_crossover(close, fast_w, slow_w, vbt)
