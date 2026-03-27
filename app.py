"""
BlockBT — Main Streamlit entry point.

This file bootstraps the database, applies the authentication gate,
and wires the multipage navigation sidebar.
"""

import streamlit as st

from blockbt.ui.auth import is_logged_in, logout, render_auth_gate

# ── Page meta ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BlockBT",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Authentication gate ───────────────────────────────────────────────────────
if not is_logged_in():
    render_auth_gate()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 BlockBT")
    st.caption(f"Zalogowany: **{st.session_state.get('username', '—')}**")
    st.divider()
    st.page_link("app.py", label="🏠 Strona główna", icon="🏠")
    st.page_link("pages/1_Wizard.py", label="🧙 Kreator Strategii", icon="🧙")
    st.page_link("pages/2_Dashboard.py", label="📊 Dashboard", icon="📊")
    st.divider()
    if st.button("🚪 Wyloguj", use_container_width=True):
        logout()
        st.rerun()

# ── Home page content ─────────────────────────────────────────────────────────
st.title("BlockBT — Środowisko Backtestingu")
st.markdown(
    """
    Witaj w **BlockBT** — self-hosted środowisku do backtestingu strategii algorytmicznych.

    ### Jak zacząć?
    1. Przejdź do **🧙 Kreator Strategii** i zdefiniuj parametry.
    2. Otwórz **📊 Dashboard**, aby uruchomić backtest i przejrzeć wyniki.
    """
)

col1, col2, col3 = st.columns(3)
col1.metric("Silnik", "OpenSource (vectorbt)")
col2.metric("Baza danych", "SQLite (local)")
col3.metric("Interfejs LLM", "MCP / JSON")
