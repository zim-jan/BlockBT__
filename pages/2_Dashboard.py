"""
BlockBT — Page 2: Dashboard & Backtest Runner.

Uses the actual SimulationResult ORM column names:
  - strategy_template_id  (FK, not user_id)
  - engine_used           (not engine_name)
  - scalar metric columns (not metrics_json)
  - run_at                (not created_at)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import plotly.graph_objects as go

from blockbt.ui.auth import is_logged_in, render_auth_gate
from blockbt.db.models import SimulationResult, StrategyTemplate
from blockbt.db.session import get_session
from blockbt.engine.loader import EngineLoader
from blockbt.connectors.registry import ConnectorRegistry

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_auth_gate()

st.set_page_config(page_title="Dashboard — BlockBT", page_icon="📊", layout="wide")
st.title("📊 Dashboard — Wyniki Backtestów")

user_id = st.session_state["user_id"]

# ── Load strategies owned by this user ───────────────────────────────────────
with get_session() as db:
    templates = (
        db.query(StrategyTemplate)
        .filter_by(user_id=user_id)
        .order_by(StrategyTemplate.created_at.desc())
        .all()
    )
    template_data = [
        {"id": t.id, "name": t.name, "state": t.wizard_state}
        for t in templates
    ]

if not template_data:
    st.info("Nie masz jeszcze żadnych strategii. Utwórz je w **🧙 Kreatorze Strategii**.")
    st.stop()

# ── Strategy selector ─────────────────────────────────────────────────────────
strategy_names = {t["id"]: f"[#{t['id']}] {t['name']}" for t in template_data}
selected_id = st.selectbox(
    "Wybierz strategię",
    options=list(strategy_names.keys()),
    format_func=lambda x: strategy_names[x],
)

selected = next(t for t in template_data if t["id"] == selected_id)
ws = selected["state"]

with st.expander("Parametry strategii", expanded=False):
    st.json(ws)

st.divider()

# ── Run backtest ──────────────────────────────────────────────────────────────
if st.button("▶ Uruchom Backtest", type="primary"):
    with st.spinner("Pobieram dane i uruchamiam backtest…"):
        # 1. Fetch market data
        connector = ConnectorRegistry.get(ws.get("connector", "yahoo"))
        ohlcv = connector.fetch(
            symbol=ws["symbol"],
            start=ws["start_date"],
            end=ws["end_date"],
            timeframe=ws.get("timeframe", "1d"),
        )

        # 2. Run via engine
        engine = EngineLoader.load()
        params = {
            "initial_capital": float(ws.get("initial_capital", 10_000)),
            "sma_fast": int(ws.get("sma_fast", 10)),
            "sma_slow": int(ws.get("sma_slow", 30)),
        }
        result = engine.run_backtest(ohlcv, params)

        # 3. Build equity curve samples list
        equity_samples: list[dict] = []
        if result.equity_curve is not None:
            eq = result.equity_curve.reset_index()
            eq.columns = ["date", "value"]
            eq["date"] = eq["date"].astype(str)
            equity_samples = eq.to_dict(orient="records")

        # 4. Persist — use actual ORM column names
        import datetime
        try:
            period_start = datetime.datetime.strptime(ws["start_date"], "%Y-%m-%d")
            period_end   = datetime.datetime.strptime(ws["end_date"],   "%Y-%m-%d")
        except (KeyError, ValueError):
            period_start = period_end = datetime.datetime.utcnow()

        with get_session() as db:
            sim = SimulationResult(
                strategy_template_id=selected_id,
                symbol=ws["symbol"],
                timeframe=ws.get("timeframe", "1d"),
                period_start=period_start,
                period_end=period_end,
                engine_used=result.engine_name,
                initial_capital=params["initial_capital"],
                total_return_pct=result.total_return_pct,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown_pct=result.max_drawdown_pct,
                win_rate_pct=result.win_rate_pct,
                num_trades=result.num_trades,
                final_capital=result.final_capital,
                full_metrics_json={
                    "total_return_pct": result.total_return_pct,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "win_rate_pct": result.win_rate_pct,
                    "num_trades": result.num_trades,
                    "final_capital": result.final_capital,
                },
                equity_curve_json=equity_samples,
                status="completed",
            )
            db.add(sim)
            db.flush()
            sim_id = sim.id

        st.session_state["last_result"] = {
            "sim_id": sim_id,
            "result": result,
            "equity_samples": equity_samples,
            "symbol": ws["symbol"],
            "strategy_name": selected["name"],
        }

    st.rerun()

# ── Display last result ───────────────────────────────────────────────────────
if "last_result" in st.session_state:
    data = st.session_state["last_result"]
    r = data["result"]

    st.subheader(f"📋 Wyniki: {data['strategy_name']} / {data['symbol']}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Całkowity zwrot",
              f"{r.total_return_pct:.2f}%" if r.total_return_pct is not None else "—")
    c2.metric("Wskaźnik Sharpe'a",
              f"{r.sharpe_ratio:.3f}" if r.sharpe_ratio is not None else "—")
    c3.metric("Max Drawdown",
              f"{r.max_drawdown_pct:.2f}%" if r.max_drawdown_pct is not None else "—")
    c4.metric("Win Rate",
              f"{r.win_rate_pct:.1f}%" if r.win_rate_pct is not None else "—")
    c5.metric("Transakcje", r.num_trades if r.num_trades is not None else "—")

    st.divider()

    # Equity curve chart
    samples = data["equity_samples"]
    if samples:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[s["date"] for s in samples],
            y=[s["value"] for s in samples],
            mode="lines",
            name="Kapitał",
            line=dict(color="#4f8bf9", width=2),
            fill="tozeroy",
            fillcolor="rgba(79,139,249,0.08)",
            hovertemplate="%{x}<br>%{y:,.2f} USD<extra></extra>",
        ))
        fig.update_layout(
            title=f"Krzywa Kapitału — {data['symbol']}",
            xaxis_title="Data",
            yaxis_title="Wartość portfela (USD)",
            template="plotly_dark",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=40, b=0),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Brak danych krzywej kapitału.")

    st.caption(f"Zapisano jako SimulationResult ID: **{data['sim_id']}**")

# ── History ───────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📜 Historia backtestów")

# Fetch via join StrategyTemplate → filter user_id
with get_session() as db:
    sims = (
        db.query(SimulationResult)
        .join(StrategyTemplate,
              SimulationResult.strategy_template_id == StrategyTemplate.id)
        .filter(StrategyTemplate.user_id == user_id)
        .order_by(SimulationResult.run_at.desc())
        .limit(20)
        .all()
    )
    history = [
        {
            "ID": s.id,
            "Symbol": s.symbol,
            "Silnik": s.engine_used,
            "Zwrot %": f"{s.total_return_pct:.2f}%" if s.total_return_pct else "—",
            "Sharpe": f"{s.sharpe_ratio:.3f}" if s.sharpe_ratio else "—",
            "Max DD %": f"{s.max_drawdown_pct:.2f}%" if s.max_drawdown_pct else "—",
            "Data": str(s.run_at)[:19],
        }
        for s in sims
    ]

if history:
    st.dataframe(history, use_container_width=True)
else:
    st.caption("Brak historycznych wyników.")
