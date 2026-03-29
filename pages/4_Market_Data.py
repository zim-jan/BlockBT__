"""
BlockBT — Page 4: Eksplorator Rynku (Market Data Explorer).

A dashboard to preview and verify data downloaded via Connectors,
overlay popular technical indicators, and visualize candlestick charts.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import plotly.graph_objects as go
import streamlit as st
from blockbt.connectors.registry import ConnectorRegistry
from blockbt.ui.auth import is_logged_in, render_auth_gate

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_logged_in():
    render_auth_gate()

st.set_page_config(page_title="Eksplorator Rynku — BlockBT", page_icon="📈", layout="wide")
st.title("📈 Eksplorator Rynku")
st.caption("Weryfikacja danych pochodzących m.in. z Yahoo Finance oraz podgląd ulubionych wskaźników.")

# ── Sidebar defaults & inputs ─────────────────────────────────────────────────
st.sidebar.subheader("Pobieranie Danych")

available = ConnectorRegistry.available()
connector_key = st.sidebar.selectbox("Dostawca danych", options=available)
symbol = st.sidebar.text_input("Symbol", value="AAPL").upper()
timeframe = st.sidebar.selectbox("Interwał", options=["1d", "1wk", "1mo"])

col_start, col_end = st.sidebar.columns(2)
start_date = col_start.date_input("Od", value=datetime.today() - timedelta(days=365))
end_date = col_end.date_input("Do", value=datetime.today())

st.sidebar.divider()
st.sidebar.subheader("Wskaźniki (Przecięcia SMA)")
sma_fast_len = st.sidebar.number_input("SMA Fast", value=10, min_value=2, max_value=200)
sma_slow_len = st.sidebar.number_input("SMA Slow", value=30, min_value=5, max_value=500)

use_cache = st.sidebar.checkbox("Użyj lokalnego bufora (Parquet)", value=True)

# ── Fetch Data ────────────────────────────────────────────────────────────────
st.divider()

if st.sidebar.button("Pobierz i analizuj", type="primary", use_container_width=True):
    if not symbol:
        st.warning("Podaj symbol.")
        st.stop()
        
    with st.spinner(f"Pobieranie danych dla {symbol}..."):
        connector = ConnectorRegistry.get(connector_key)
        try:
            df = connector.fetch(
                symbol=symbol,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                timeframe=timeframe,
                use_cache=use_cache,
            )
        except Exception as e:
            st.error(f"Błąd podczas pobierania danych: {e}")
            st.stop()

    if df.empty:
        st.warning(f"Brak danych dla symbolu {symbol} w wybranym okresie.")
        st.stop()

    # Calculate indicators
    df["sma_fast"] = df["close"].rolling(window=sma_fast_len).mean()
    df["sma_slow"] = df["close"].rolling(window=sma_slow_len).mean()

    # Layout: Top row with metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Liczba świec", len(df))
    period_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
    c2.metric("Zwrot w okresie", f"{period_return:.2f}%")
    c3.metric("Ostatnia cena (Close)", f"{df['close'].iloc[-1]:.2f}")
    c4.metric("Ostatni wolumen", f"{df['volume'].iloc[-1]:,.0f}")

    # Layout: Chart
    st.subheader(f"Wykres Świecowy: {symbol}")
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Cena',
    ))

    # Overlays
    fig.add_trace(go.Scatter(
        x=df.index, y=df['sma_fast'], 
        mode='lines', name=f'SMA {sma_fast_len}', line=dict(color='orange', width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['sma_slow'], 
        mode='lines', name=f'SMA {sma_slow_len}', line=dict(color='blue', width=1.5)
    ))

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
        height=550,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Layout: Raw Data
    st.subheader("Surowe Dane (Podgląd weryfikacyjny)")
    st.dataframe(
        df.sort_index(ascending=False),
        use_container_width=True,
    )
else:
    st.info("Skonfiguruj parametry w panelu bocznym i kliknij **Pobierz i analizuj**.")
