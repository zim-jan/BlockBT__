"""
BlockBT — Page 6: Visual Node-based Builder (Phase 7).

Drag & Drop GUI using streamlit-flow.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import streamlit_flow as sf
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout

from blockbt.ui.auth import is_logged_in, render_auth_gate
from blockbt.db.models import StrategyTemplate
from blockbt.db.session import get_session

if not is_logged_in():
    render_auth_gate()

st.set_page_config(page_title="Visual Builder — BlockBT", page_icon="🔀", layout="wide")
st.title("🔀 Wizualny Kreator Strategii (Węzły)")
st.caption("Buduj logikę handlową w ujęciu Drag & Drop przy pomocy klocków decyzyjnych.")

st.divider()

# Node Definitions
nodes = [
    StreamlitFlowNode("source", (100, 100), {"content": "Data Source (Cena Zmknięcia)"}, node_type="input", source_position="right", target_position="left"),
    StreamlitFlowNode("sma_fast", (400, 0), {"content": "Wskaźnik: SMA (10)"}, node_type="default", source_position="right", target_position="left"),
    StreamlitFlowNode("sma_slow", (400, 200), {"content": "Wskaźnik: SMA (50)"}, node_type="default", source_position="right", target_position="left"),
    StreamlitFlowNode("crossover", (700, 100), {"content": "Logika (Przecięcie w GÓRĘ)"}, node_type="default", source_position="right", target_position="left"),
    StreamlitFlowNode("portfolio", (1000, 100), {"content": "Konto (Portfolio Wejście)"}, node_type="output", source_position="right", target_position="left"),
]

# Edge Definitions
edges = [
    StreamlitFlowEdge("source-sma_fast", "source", "sma_fast", animated=True),
    StreamlitFlowEdge("source-sma_slow", "source", "sma_slow", animated=True),
    StreamlitFlowEdge("sma_fast-cross", "sma_fast", "crossover", animated=True),
    StreamlitFlowEdge("sma_slow-cross", "sma_slow", "crossover", animated=True),
    StreamlitFlowEdge("cross-portfolio", "crossover", "portfolio", animated=True),
]

st.subheader("Płótno (Canvas)")

try:
    flow_state = StreamlitFlowState(nodes, edges)
    state = sf.streamlit_flow(
        "viz_builder",
        flow_state,
        layout=TreeLayout(direction="right"),
        fit_view=True,
        height=500,
        enable_node_menu=True,
        enable_edge_menu=True,
        enable_pane_menu=True,
        pan_on_drag=True,
        allow_new_edges=True,
        allow_zoom=True,
    )
except Exception as e:
    st.error(f"Krytyczny błąd renderowania węzłów React Flow: {e}")
    state = None

if state:
    st.subheader("Wygenerowany Graf AST (JSON):")
    with st.expander("Pokaż zrzucone dane", expanded=False):
        parsed_nodes = []
        for n in state.nodes:
            if isinstance(n, dict):
                parsed_nodes.append({"id": n.get("id"), "type": n.get("node_type", n.get("type", "default")), "data": n.get("data", {})})
            else:
                parsed_nodes.append({"id": getattr(n, "id", ""), "type": getattr(n, "node_type", getattr(n, "type", "default")), "data": getattr(n, "data", {})})
                
        parsed_edges = []
        for e in state.edges:
            if isinstance(e, dict):
                parsed_edges.append({"id": e.get("id"), "source": e.get("source"), "target": e.get("target")})
            else:
                parsed_edges.append({"id": getattr(e, "id", ""), "source": getattr(e, "source", ""), "target": getattr(e, "target", "")})
        
        ast_dict = {"type": "visual_ast", "nodes": parsed_nodes, "edges": parsed_edges}
        st.json(ast_dict)
        
    
    if st.button("Zapisz JSON do nowej struktury `StrategyTemplate`", type="primary"):
        import datetime
        user_id = st.session_state.get("user_id")
        
        # Tworzy AST w standardzie Wizard State
        wizard_state = {
            "symbol": "BTC-USD", # default for visualization prototype
            "timeframe": "1d",
            "start_date": "2023-01-01",
            "end_date": datetime.date.today().strftime("%Y-%m-%d"),
            "initial_capital": 10000,
            "strategy_type": "visual_ast",
            "ast": ast_dict
        }
        
        with get_session() as db:
            new_strategy = StrategyTemplate(
                user_id=user_id,
                name=f"Wizualna Strategia {datetime.datetime.now().strftime('%H:%M:%S')}",
                description="Zbudowana z klocków Drag & Drop",
                engine_type="opensource",
                wizard_state=wizard_state
            )
            db.add(new_strategy)
            db.commit()
            st.session_state["ast_saved"] = True
            st.rerun()

if st.session_state.get("ast_saved"):
    st.toast("Strategia została pomyslnie zbudowana z Grafu i zapisana w Bazie! Przejdź do Dashboardu by ją odpalić.", icon="✅")
    st.success("Strategia została pomyslnie zbudowana z Grafu i zapisana w Bazie! Przejdź do Dashboardu by ją odpalić.")
    st.session_state.pop("ast_saved")


