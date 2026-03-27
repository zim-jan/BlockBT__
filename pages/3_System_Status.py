"""
BlockBT — Page 3: System Status & Diagnostics (Phase 2.5).

Sections:
  1. Dual-Engine Monitor  — shows which engine is active; force-OSS toggle
  2. Data Cache Monitor   — scans the Parquet directory and lists cached files
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st

from blockbt.config import settings
from blockbt.engine.loader import EngineLoader
from blockbt.ui.auth import is_logged_in, render_auth_gate

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_auth_gate()

st.set_page_config(
    page_title="Status Systemu — BlockBT",
    page_icon="⚙️",
    layout="wide",
)
st.title("⚙️ Status Systemu — Diagnostyka BlockBT")
st.caption("Widok diagnostyczny architektury Dual-Engine oraz bufora danych Parquet.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SEKCJA 1 — Monitor Silnika (Dual-Engine Status)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🔧 Monitor Silnika — Architektura Dual-Engine")

# Sprawdź dostępność silnika PRO (lazy — bez importu kodu zastrzeżonego)
def _is_pro_available() -> bool:
    """Return True if vbtpro imports without error (BYOL path present)."""
    try:
        vbtpro_path = settings.VBTPRO_PATH
        if vbtpro_path and Path(vbtpro_path).exists():
            import sys as _sys
            _sys.path.insert(0, str(vbtpro_path))
        import importlib
        importlib.import_module("vectorbtpro")
        return True
    except (ImportError, ModuleNotFoundError):
        return False

pro_available = _is_pro_available()

# Toggle: wymuszenie silnika OSS
st.session_state.setdefault("force_oss_engine", False)
force_oss = st.toggle(
    "🔒 Wymuś silnik Open Source (ignoruj licencję PRO)",
    value=st.session_state["force_oss_engine"],
    help="Gdy włączone, EngineLoader zawsze wybierze OpenSourceEngine, "
         "niezależnie od tego czy vbtpro jest zainstalowane.",
)
st.session_state["force_oss_engine"] = force_oss

# --- Ładujemy odpowiedni silnik i pobieramy jego info ---
engine = EngineLoader.load(force_opensource=force_oss)
info = engine.get_engine_info()

# Wyświetl status
colA, colB, colC = st.columns(3)

is_pro = "pro" in info.get("name", "").lower()

with colA:
    if is_pro:
        st.success("🚀 **ProEngine** aktywny")
    else:
        st.warning("🔓 **OpenSourceEngine** aktywny")

with colB:
    st.metric("Nazwa silnika", info.get("name", "—"))

with colC:
    st.metric("Wersja", info.get("version", "—"))

# Tabelka szczegółów
with st.expander("Szczegóły konfiguracji silnika", expanded=False):
    st.json(info)

# Status BYOL
st.markdown("**Status licencji BYOL (vectorbtpro):**")
if pro_available:
    st.success("✅ Biblioteka `vectorbtpro` wykryta i dostępna w systemie.")
else:
    st.info(
        "ℹ️ Biblioteka `vectorbtpro` **nie jest** zainstalowana. "
        "Aktywny jest silnik Open Source (vectorbt). "
        "Aby aktywować ProEngine, ustaw ścieżkę `VBTPRO_PATH` w pliku `.env`."
    )

if force_oss and pro_available:
    st.warning(
        "⚠️ Wymuszono tryb Open Source. ProEngine jest dostępny, "
        "ale **nie** zostanie użyty w tej sesji."
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SEKCJA 2 — Monitor Magazynu Danych (Data Cache)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("💾 Monitor Bufora Danych — Parquet Cache")

parquet_dir: Path = settings.PARQUET_DIR

st.caption(f"Katalog bufora: `{parquet_dir}`")

def _scan_parquet_cache(root: Path) -> list[dict]:
    """Recursively scan *root* for .parquet files and return metadata rows."""
    rows = []
    if not root.exists():
        return rows
    for f in sorted(root.rglob("*.parquet")):
        stat = f.stat()
        size_bytes = stat.st_size
        if size_bytes >= 1_048_576:
            size_str = f"{size_bytes / 1_048_576:.2f} MB"
        else:
            size_str = f"{size_bytes / 1_024:.1f} KB"
        rows.append({
            "Symbol": f.parent.name.upper(),
            "Plik": f.name,
            "Rozmiar": size_str,
            "Ostatnia modyfikacja": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "Ścieżka": str(f.relative_to(root)),
        })
    return rows

cache_rows = _scan_parquet_cache(parquet_dir)

col_ref, col_clear = st.columns([3, 1])
col_ref.markdown(f"Znalezione pliki: **{len(cache_rows)}**")

if col_clear.button("🗑️ Usuń cały cache", type="secondary", disabled=len(cache_rows) == 0):
    import shutil
    if parquet_dir.exists():
        shutil.rmtree(parquet_dir)
        parquet_dir.mkdir(parents=True, exist_ok=True)
    st.success("Cache wyczyszczony.")
    st.rerun()

if cache_rows:
    st.dataframe(
        cache_rows,
        use_container_width=True,
        column_config={
            "Symbol":               st.column_config.TextColumn("Symbol",     width="small"),
            "Plik":                 st.column_config.TextColumn("Plik",       width="medium"),
            "Rozmiar":              st.column_config.TextColumn("Rozmiar",    width="small"),
            "Ostatnia modyfikacja": st.column_config.TextColumn("Modyfikacja",width="medium"),
            "Ścieżka":              st.column_config.TextColumn("Ścieżka",    width="large"),
        },
        hide_index=True,
    )

    # Podsumowanie
    total_bytes = sum(f.stat().st_size for f in parquet_dir.rglob("*.parquet") if f.exists())
    if total_bytes >= 1_048_576:
        total_str = f"{total_bytes / 1_048_576:.2f} MB"
    else:
        total_str = f"{total_bytes / 1_024:.1f} KB"
    st.caption(f"Łączny rozmiar bufora: **{total_str}**")
else:
    st.info(
        "📭 Bufor danych jest pusty. "
        "Pliki Parquet zostaną automatycznie utworzone po uruchomieniu "
        "pierwszego backtestу w widoku **📊 Dashboard**."
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SEKCJA 3 — Informacje o środowisku
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🐍 Środowisko Uruchomieniowe")

import platform

colE1, colE2, colE3, colE4 = st.columns(4)
colE1.metric("Python", platform.python_version())
colE2.metric("OS", platform.system())
colE3.metric("Baza danych", str(settings.DATABASE_URL).split(":///")[-1].split("/")[-1])
colE4.metric("Data/Czas", datetime.now().strftime("%Y-%m-%d %H:%M"))
