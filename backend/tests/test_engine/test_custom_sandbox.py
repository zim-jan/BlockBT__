"""
Faza 11 — testy bezpieczeństwa sandboxa AST (`IndicatorService._validate_code_safety`).

Model deny-by-default: dozwolone są tylko węzły z `_ALLOWED_AST_NODES`; dodatkowo
blokujemy atrybuty dunder oraz jawną listę niebezpiecznych atrybutów (nie-dunder)
i zabronione nazwy wbudowane. Kontrakt: każdy złośliwy fragment MUSI podnieść
`ValueError` z frazą "Unsafe code detected". Fragmenty benign muszą przejść
walidację (brak nadmiernego blokowania legalnych wskaźników).
"""

import pytest

from app.services.engine.indicators import IndicatorService

# --- Fragmenty złośliwe (MUSZĄ być zablokowane) ---
MALICIOUS_SNIPPETS: list[str] = [
    # introspekcja dunder → dostęp do klas/subclasses/globals
    "out = ().__class__",
    "out = [].__class__.__bases__",
    "out = close.__class__.__mro__",
    "out = (1).__class__.__base__.__subclasses__()",
    "out = ().__class__.__mro__[1].__subclasses__()",
    # zabronione nazwy wbudowane / ucieczki
    "out = eval('1+1')",
    "exec('x=1')",
    "out = compile('1', '<s>', 'eval')",
    "f = open('/etc/passwd')",
    "m = __import__('os')",
    "x = input()",
    "out = getattr(close, 'ctypes')",
    "setattr(close, 'x', 1)",
    "g = globals()",
    "loc = locals()",
    "v = vars(close)",
    "breakpoint()",
    "t = type(close)",
    "o = object()",
    "s = super()",
    # dostęp do ramek/globalsów przez generator/korutynę (NIE-dunder!)
    "g = (x for x in [1])\nout = g.gi_frame.f_globals",
    "g = (x for x in [1])\nout = g.gi_code",
    # surowa pamięć / interfejs C numpy
    "out = close.ctypes",
    "out = close.ctypes.data",
    "out = close.tobytes()",
    # zapis dowolnego pliku na dysk (ucieczka Air-Gapped)
    "close.tofile('/tmp/evil.bin')",
    "close.to_csv('/tmp/evil.csv')",
    "close.to_pickle('/tmp/evil.pkl')",
    "close.to_parquet('/tmp/evil.parquet')",
    # ODCZYT / deserializacja / sieć / alternatywny eval (review 2026-07-15)
    "out = pd.read_pickle('/etc/passwd')",   # pickle → RCE
    "out = pd.read_csv('http://evil/x')",    # odczyt + SSRF
    "out = pd.read_parquet('/tmp/x')",
    "out = np.load('/tmp/x.npy')",           # np.load = pickle → RCE
    "out = np.fromfile('/tmp/x')",
    "out = np.frombuffer(b'')",
    "out = pd.eval('1+1')",                  # alternatywny eval przez atrybut
    "out = close.query('a > 1')",            # DataFrame.query = eval
    "out = vbt.YFData.download('AAPL')",     # dostęp sieciowy
    "out = close.get_data()",
    # importy w każdej odmianie (brak Import/ImportFrom w allowliście)
    "import os",
    "from os import system",
    "import os, sys",
    "from subprocess import Popen",
    # konstrukcje spoza allowlisty
    "out = (y := 5)",              # NamedExpr (walrus)
    "out = f'{close}'",            # JoinedStr / FormattedValue
    "class Evil:\n    pass",       # ClassDef
    "with open('x') as fh:\n    pass",  # With
    "try:\n    pass\nexcept Exception:\n    pass",  # Try
    "raise ValueError('x')",       # Raise
    "global close",                # Global
    "async def f():\n    pass",    # AsyncFunctionDef
    "yield 1",                     # Yield (poza FunctionDef → SyntaxError → Unsafe)
    "del close",                   # Delete
    "assert False",                # Assert
]

# --- Fragmenty benign (MUSZĄ przejść walidację — brak nadmiernego blokowania) ---
BENIGN_SNIPPETS: list[str] = [
    # prosta funkcja skalarna
    "def f(close):\n    out = close * 2\n    return out",
    # pętla numpy z indeksowaniem (typowy rdzeń wskaźnika @njit)
    (
        "def sma(close, window):\n"
        "    out = close.copy()\n"
        "    for i in range(window, len(close)):\n"
        "        out[i] = close[i-window:i].mean()\n"
        "    return out"
    ),
    # styl generate_custom: entries/exits z akcesora .vbt (crossed_above/below)
    (
        "fast = close.rolling(10).mean()\n"
        "slow = close.rolling(30).mean()\n"
        "entries = fast.vbt.crossed_above(slow)\n"
        "exits = fast.vbt.crossed_below(slow)"
    ),
]


@pytest.mark.parametrize("code", MALICIOUS_SNIPPETS)
def test_malicious_code_blocked(code: str):
    """Każdy złośliwy fragment podnosi ValueError('Unsafe code detected')."""
    with pytest.raises(ValueError, match="Unsafe code detected"):
        IndicatorService._validate_code_safety(code)


@pytest.mark.parametrize("code", BENIGN_SNIPPETS)
def test_benign_code_allowed(code: str):
    """Legalne wskaźniki przechodzą walidację (zwracany jest ast.Module)."""
    tree = IndicatorService._validate_code_safety(code)
    assert tree is not None


def test_benign_indicator_still_compiles():
    """Regresja: benign pętla numpy nadal buduje fabrykę (nie przeblokowaliśmy)."""
    code = (
        "def custom_osc(close):\n"
        "    out = close.copy()\n"
        "    for i in range(1, len(close)):\n"
        "        out[i] = close[i] - close[i-1]\n"
        "    return out"
    )
    factory = IndicatorService.compile_custom_indicator(code)
    assert factory is not None
    assert getattr(factory, "run", None) is not None
