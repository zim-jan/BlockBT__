from __future__ import annotations

"""
Parquet I/O helpers used by data connectors.

All data cached on disk goes through these two functions so the serialisation
format, compression, and schema enforcement are consistent across connectors.
"""


from pathlib import Path

import pandas as pd
from loguru import logger


def save_parquet(df: pd.DataFrame, path: Path, *, compression: str = "snappy") -> None:
    """Write a DataFrame to Parquet, creating parent directories as needed.

    Parameters
    ----------
    df:          DataFrame to persist.
    path:        Destination file path (should end in ``.parquet``).
    compression: Parquet codec — ``"snappy"`` (fast) or ``"gzip"`` (smaller).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", compression=compression, index=True)
    logger.trace("Parquet written: {} ({} bytes)", path, path.stat().st_size)


def load_parquet(path: Path) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame.

    Parameters
    ----------
    path: File to read.

    Raises
    ------
    FileNotFoundError — if the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Parquet cache file not found: {path}")
    df = pd.read_parquet(path, engine="pyarrow")
    logger.trace("Parquet loaded: {} ({} rows)", path, len(df))
    return df


def list_cached_symbols(cache_dir: Path) -> list[str]:
    """Return a list of symbols that have at least one cached Parquet file."""
    if not cache_dir.exists():
        return []
    return sorted(d.name for d in cache_dir.iterdir() if d.is_dir() and any(d.glob("*.parquet")))


def purge_cache(cache_dir: Path, symbol: str | None = None) -> int:
    """Delete Parquet cache files.

    Parameters
    ----------
    cache_dir: Root of the Parquet cache tree.
    symbol:    If given, purge only this symbol. Otherwise purge all.

    Returns
    -------
    Number of files deleted.
    """
    import shutil

    if symbol:
        target = cache_dir / symbol.upper().replace("/", "_")
        if target.exists():
            shutil.rmtree(target)
            return 1
        return 0

    count = 0
    for sym_dir in cache_dir.iterdir():
        if sym_dir.is_dir():
            shutil.rmtree(sym_dir)
            count += 1
    return count
