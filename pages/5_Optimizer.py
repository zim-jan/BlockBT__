"""
BlockBT — Page 5: Optuna Optymalizator (Phase 5).

Runs Bayesian Optimization (TPE) on strategy parameters to maximize
user-defined metrics (e.g., Sharpe Ratio) using the local vectorbt engine.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import optuna
import streamlit as st
from blockbt.connectors.registry import ConnectorRegistry
from blockbt.db.models import StrategyTemplate
from blockbt.db.session import get_session
from blockbt.engine.loader import EngineLoader
from blockbt.ui.auth import is_logged_in, render_auth_gate

# Optuna plotly visualization uses standard plotly
from optuna.visualization import plot_optimization_history, plot_param_importances

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_auth_gate()

st.set_page_config(page_title="Optymalizator — BlockBT", page_icon="💡", layout="wide")
st.title("💡 Optymalizator Strategii (Optuna)")
st.caption("Wykorzystuje optymalizację bayesowską (drzewa Parzena - TPE) do znajdowania parametrów maksymalizujących Sharpe Ratio.")

user_id = st.session_state["user_id"]

# ── Load strategies ───────────────────────────────────────────────────────────
with get_session() as db:
    templates = (
        db.query(StrategyTemplate)
        .filter_by(user_id=user_id)
        .order_by(StrategyTemplate.created_at.desc())
        .all()
    )
    template_data = [{"id": t.id, "name": t.name, "state": t.wizard_state} for t in templates]

if not template_data:
    st.info("Brak strategii bazowych. Utwórz strategię w **🧙 Kreatorze Strategii**.")
    st.stop()

st.divider()

col_sel, col_param = st.columns([1, 1])

with col_sel:
    st.subheader("1. Wybierz strategię bazową")
    strategy_names = {t["id"]: f"[#{t['id']}] {t['name']}" for t in template_data}
    selected_id = st.selectbox(
        "Strategia",
        options=list(strategy_names.keys()),
        format_func=lambda x: strategy_names[x],
    )
    selected = next(t for t in template_data if t["id"] == selected_id)
    ws = selected["state"]
    st.json(ws)

with col_param:
    st.subheader("2. Parametry Optuny")
    strategy_type = ws.get("strategy_type", "sma_crossover")
    n_trials = st.number_input("Liczba poszukiwań (Trials)", min_value=10, max_value=500, value=50, step=10)

    st.markdown("**Przestrzenie poszukiwań (Search Spaces):**")
    if strategy_type == "macd":
        macd_fast_range = st.slider("Zakres MACD Fast", 2, 50, (5, 20))
        macd_slow_range = st.slider("Zakres MACD Slow", 10, 100, (21, 50))
        macd_sig_range = st.slider("Zakres Signal", 2, 30, (5, 15))
    else:  # sma_crossover
        sma_fast_range = st.slider("Zakres SMA Fast", 2, 100, (5, 30))
        sma_slow_range = st.slider("Zakres SMA Slow", 10, 300, (31, 100))

# ── Run Optimization ──────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 Uruchom Optymalizację", type="primary", use_container_width=True):
    with st.spinner(f"Optuna przeszukuje {n_trials} kombinacji. To może potrwać dłuższą chwilę..."):
        # 1. Fetch market data via Parquet caching (fast local reads during loops)
        connector = ConnectorRegistry.get(ws.get("connector", "yahoo"))
        ohlcv = connector.fetch(
            symbol=ws["symbol"],
            start=ws["start_date"],
            end=ws["end_date"],
            timeframe=ws.get("timeframe", "1d"),
        )

        if ohlcv.empty:
            st.error("Brak danych cenowych dla wybranego symbolu w zadanym oknie.")
            st.stop()

        engine = EngineLoader.load()

        # 2. Define objective function
        def objective(trial: optuna.Trial) -> float:
            params = ws.copy()

            if strategy_type == "macd":
                f = trial.suggest_int("macd_fast", macd_fast_range[0], macd_fast_range[1])
                s = trial.suggest_int("macd_slow", macd_slow_range[0], macd_slow_range[1])
                sig = trial.suggest_int("macd_signal", macd_sig_range[0], macd_sig_range[1])
                if f >= s:
                    raise optuna.TrialPruned()
                params.update({"macd_fast": f, "macd_slow": s, "macd_signal": sig})
            else:
                f = trial.suggest_int("sma_fast", sma_fast_range[0], sma_fast_range[1])
                s = trial.suggest_int("sma_slow", sma_slow_range[0], sma_slow_range[1])
                if f >= s:
                    raise optuna.TrialPruned()
                params.update({"sma_fast": f, "sma_slow": s})

            result = engine.run_backtest(ohlcv, params)

            # Maximize Sharpe. Penalize zero trades.
            sr = result.get("sharpe_ratio")
            num_trades = result.get("num_trades", 0)
            if sr is None or num_trades == 0:
                return -99.0
            return float(sr)

        # 3. Create Study & Optimize
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)

        best_params = study.best_params
        best_val = study.best_value

        st.session_state["optuna_study"] = study
        st.session_state["optuna_best"] = best_params
        st.session_state["optuna_val"] = best_val
        st.session_state["optuna_source_ws"] = ws
        st.session_state["optuna_source_name"] = selected["name"]

    st.rerun()

# ── Render Results ────────────────────────────────────────────────────────────
if "optuna_study" in st.session_state:
    study = st.session_state["optuna_study"]
    best_params = st.session_state["optuna_best"]
    best_val = st.session_state["optuna_val"]

    st.subheader("🎯 Wyniki Optymalizacji")
    st.success(f"Najlepszy wskaźnik Sharpe'a: **{best_val:.3f}**")
    st.json(best_params)

    # Optuna Visualizations
    c_viz1, c_viz2 = st.columns(2)
    with c_viz1:
        fig1 = plot_optimization_history(study)
        fig1.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig1, use_container_width=True)
    with c_viz2:
        try:
            fig2 = plot_param_importances(study)
            fig2.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig2, use_container_width=True)
        except Exception:
            st.info("Zbyt mało ukończonych udanych iteracji by oszacować ważność parametrów.")

    st.divider()

    # Save logic
    if st.button("💾 Zapisz zoptymalizowaną strategię jako nowy szablon", type="secondary"):
        new_ws = st.session_state["optuna_source_ws"].copy()
        new_ws.update(best_params)

        with get_session() as db:
            tpl = StrategyTemplate(
                user_id=user_id,
                name=f"{st.session_state['optuna_source_name']} (Zoptymalizowana)",
                description=f"Automatyczna optymalizacja Optuna (Trials: {len(study.trials)}, Sharpe: {best_val:.2f})",
                wizard_state=new_ws,
            )
            db.add(tpl)
            db.flush()
            st.success(f"Zapisano strategię pod ID #{tpl.id}! Możesz ją teraz zbacktestować w **Dashboardzie**.")
