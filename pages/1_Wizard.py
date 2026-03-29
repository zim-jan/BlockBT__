"""
BlockBT — Page 1: Kreator Strategii (Strategy Wizard).

A 3-step form stored in st.session_state:
  Step 1 — Data provider & symbol selection
  Step 2 — Strategy parameters (SMA Fast/Slow)
  Step 3 — Confirmation & save to StrategyTemplate
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from blockbt.connectors.registry import ConnectorRegistry
from blockbt.db.models import StrategyTemplate
from blockbt.db.session import get_session
from blockbt.ui.auth import is_logged_in, render_auth_gate

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_auth_gate()

st.set_page_config(page_title="Kreator Strategii — BlockBT", page_icon="🧙", layout="centered")
st.title("🧙 Kreator Strategii")

# ── Session state defaults ────────────────────────────────────────────────────
defaults: dict = {
    "wizard_step": 1,
    "wiz_connector": "yahoo",
    "wiz_symbol": "AAPL",
    "wiz_timeframe": "1d",
    "wiz_start": "2022-01-01",
    "wiz_end": "2023-12-31",
    "wiz_sma_fast": 10,
    "wiz_sma_slow": 30,
    "wiz_strategy_name": "SMA Crossover",
    "wiz_notes": "",
    "wiz_initial_capital": 10_000.0,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ── Step indicator ────────────────────────────────────────────────────────────
step = st.session_state["wizard_step"]
progress_labels = ["1 · Dane", "2 · Parametry", "3 · Potwierdzenie"]
cols = st.columns(3)
for i, label in enumerate(progress_labels, start=1):
    with cols[i - 1]:
        if i < step:
            st.success(f"✔ {label}")
        elif i == step:
            st.info(f"▶ {label}")
        else:
            st.caption(f"○ {label}")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Data provider & symbol
# ─────────────────────────────────────────────────────────────────────────────
if step == 1:
    st.subheader("Krok 1: Źródło danych i instrument")

    available = ConnectorRegistry.available()
    wiz_connector = st.selectbox(
        "Dostawca danych",
        options=available,
        index=available.index(st.session_state["wiz_connector"])
        if st.session_state["wiz_connector"] in available
        else 0,
    )
    wiz_symbol = st.text_input("Symbol (ticker)", value=st.session_state["wiz_symbol"]).upper()
    wiz_timeframe = st.selectbox(
        "Interwał",
        options=["1d", "1wk", "1mo"],
        index=["1d", "1wk", "1mo"].index(st.session_state["wiz_timeframe"]),
    )
    col_s, col_e = st.columns(2)
    wiz_start = col_s.text_input("Data początkowa (YYYY-MM-DD)", value=st.session_state["wiz_start"])
    wiz_end = col_e.text_input("Data końcowa (YYYY-MM-DD)", value=st.session_state["wiz_end"])

    if st.button("Dalej →", use_container_width=True, type="primary"):
        if not wiz_symbol:
            st.error("Podaj symbol instrumentu.")
        else:
            st.session_state.update(
                wiz_connector=wiz_connector,
                wiz_symbol=wiz_symbol,
                wiz_timeframe=wiz_timeframe,
                wiz_start=wiz_start,
                wiz_end=wiz_end,
                wizard_step=2,
            )
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Strategy parameters
# ─────────────────────────────────────────────────────────────────────────────
elif step == 2:
    st.subheader("Krok 2: Parametry Strategii")
    st.caption("Strategia: **SMA Crossover** — kupno przy przecięciu SMA Fast > SMA Slow, sprzedaż odwrotnie.")

    wiz_strategy_name = st.text_input("Nazwa strategii", value=st.session_state["wiz_strategy_name"])
    wiz_initial_capital = st.number_input(
        "Kapitał początkowy (USD)", min_value=100.0, value=st.session_state["wiz_initial_capital"], step=1000.0
    )
    col_f, col_s = st.columns(2)
    wiz_sma_fast = col_f.number_input("SMA Fast (okresy)", min_value=2, max_value=100, value=st.session_state["wiz_sma_fast"])
    wiz_sma_slow = col_s.number_input("SMA Slow (okresy)", min_value=5, max_value=500, value=st.session_state["wiz_sma_slow"])

    wiz_notes = st.text_area("Notatki do strategii (opcjonalnie)", value=st.session_state.get("wiz_notes", ""))

    if wiz_sma_fast >= wiz_sma_slow:
        st.warning("⚠ SMA Fast powinno być mniejsze niż SMA Slow.")

    col_back, col_next = st.columns(2)
    if col_back.button("← Wstecz", use_container_width=True):
        st.session_state["wizard_step"] = 1
        st.rerun()
    if col_next.button("Dalej →", use_container_width=True, type="primary"):
        st.session_state.update(
            wiz_strategy_name=wiz_strategy_name,
            wiz_notes=wiz_notes,
            wiz_initial_capital=wiz_initial_capital,
            wiz_sma_fast=int(wiz_sma_fast),
            wiz_sma_slow=int(wiz_sma_slow),
            wizard_step=3,
        )
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Confirmation & save
# ─────────────────────────────────────────────────────────────────────────────
elif step == 3:
    st.subheader("Krok 3: Podsumowanie i Zapis")

    s = st.session_state
    st.json(
        {
            "Strategia": s["wiz_strategy_name"],
            "Dostawca": s["wiz_connector"],
            "Symbol": s["wiz_symbol"],
            "Interwał": s["wiz_timeframe"],
            "Okres": f"{s['wiz_start']} → {s['wiz_end']}",
            "SMA Fast": s["wiz_sma_fast"],
            "SMA Slow": s["wiz_sma_slow"],
            "Kapitał": s["wiz_initial_capital"],
        }
    )

    col_back, col_save = st.columns(2)
    if col_back.button("← Wstecz", use_container_width=True):
        st.session_state["wizard_step"] = 2
        st.rerun()
    if col_save.button("💾 Zapisz strategię", use_container_width=True, type="primary"):
        wizard_state = {
            "connector": s["wiz_connector"],
            "symbol": s["wiz_symbol"],
            "timeframe": s["wiz_timeframe"],
            "start_date": s["wiz_start"],
            "end_date": s["wiz_end"],
            "sma_fast": s["wiz_sma_fast"],
            "sma_slow": s["wiz_sma_slow"],
            "initial_capital": s["wiz_initial_capital"],
        }
        with get_session() as db:
            tpl = StrategyTemplate(
                user_id=s["user_id"],
                name=s["wiz_strategy_name"],
                description=s.get("wiz_notes", "Brak notatki") or "Brak notatki",
                wizard_state=wizard_state,
            )
            db.add(tpl)
            db.flush()
            tpl_id = tpl.id

        st.session_state["last_template_id"] = tpl_id
        st.success(f"✅ Strategia zapisana (ID: {tpl_id}). Przejdź do Dashboardu, aby uruchomić backtest.")
        st.session_state["wizard_step"] = 1  # reset for next strategy
