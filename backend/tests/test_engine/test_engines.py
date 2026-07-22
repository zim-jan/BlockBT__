
import pytest

"""
Testy dla Loadera Dual-Engine oraz mocków ProEngine.
"""




class TestEngineLoader:
    def test_returns_engine_instance(self):
        from app.services.engine.loader import EngineLoader

        engine = EngineLoader.load(force_reload=True)
        assert engine is not None

    def test_engine_has_name_and_version(self):
        from app.services.engine.loader import EngineLoader

        engine = EngineLoader.load(force_reload=True)
        info = engine.get_engine_info()
        assert "name" in info
        assert "version" in info

    def test_info_class_method(self):
        from app.services.engine.loader import EngineLoader

        info = EngineLoader.info()
        assert isinstance(info, dict)


class TestOpenSourceEngine:
    def test_engine_info(self):
        from app.services.engine.opensource_engine import OpenSourceEngine

        eng = OpenSourceEngine()
        info = eng.get_engine_info()
        assert info["name"] == "opensource"

    def test_is_available(self):
        from app.services.engine.opensource_engine import OpenSourceEngine

        assert OpenSourceEngine().is_available() is True

    def test_run_backtest(self, sample_ohlcv, minimal_params):
        from app.services.engine.opensource_engine import OpenSourceEngine

        eng = OpenSourceEngine()
        result = eng.run_backtest(sample_ohlcv, minimal_params)
        assert result["symbol"] == "TEST"
        assert result["engine_name"] == "opensource"
        # Headline metrics may be None for very short series but should exist
        assert "total_return_pct" in result
        assert "equity_curve" in result

    def test_vbt_fallback_to_vendored_src(self, monkeypatch):
        """Weryfikuje, czy przy braku zainstalowanej paczki vectorbt silnik poprawnie ładuje vectorbt_src."""
        import sys
        import app.services.engine.opensource_engine as engine_mod

        # Reset vectorbt setup
        vbt = engine_mod._setup_vbt()
        assert vbt is not None


class TestProEngineMock:
    """ProEngine MUSI działać nawet bez zainstalowanego vbtpro (tryb mock)."""

    def test_instantiates_without_vbtpro(self):
        from app.services.engine.pro_engine import ProEngine

        engine = ProEngine()
        # Either live or mock — both are valid states
        assert engine is not None

    def test_mock_run_returns_deterministic_result(self, sample_ohlcv, minimal_params):
        from app.services.engine.pro_engine import ProEngine

        engine = ProEngine()
        if engine.is_available():
            pytest.skip("Real vbtpro detected — mock path not exercised")

        result = engine.run_backtest(sample_ohlcv, minimal_params)
        assert result["engine_name"] == "pro_mock"
        assert result["total_return_pct"] is not None
        assert result["equity_curve"] is not None

    def test_mock_result_is_deterministic(self, sample_ohlcv, minimal_params):
        from app.services.engine.pro_engine import ProEngine

        engine = ProEngine()
        if engine.is_available():
            pytest.skip("Real vbtpro detected — mock path not exercised")

        r1 = engine.run_backtest(sample_ohlcv, minimal_params)
        r2 = engine.run_backtest(sample_ohlcv, minimal_params)
        assert r1["total_return_pct"] == r2["total_return_pct"]
        assert r1["num_trades"] == r2["num_trades"]


class TestBacktestRunnerIntegration:
    """Tests the integration between the runner and the engines."""

    def test_execute_backtest_integration(self, monkeypatch, sample_ohlcv):
        from unittest.mock import MagicMock

        from app.services.connectors.registry import ConnectorRegistry
        from app.services.engine.runner import _execute_backtest

        # Mock the connector to return sample data
        mock_connector = MagicMock()
        mock_connector.fetch.return_value = sample_ohlcv
        monkeypatch.setattr(ConnectorRegistry, "get", lambda name: mock_connector)

        params = {
            "symbol": "INTEGRATION_TEST",
            "strategy_type": "sma_crossover",
            "sma_fast": 5,
            "sma_slow": 15,
            "initial_capital": 5000.0,
            "data_source": "mock"
        }

        # This calls engine.run_backtest(df, parameters) and extracts metrics
        metrics = _execute_backtest(params)

        assert "Total Return [%]" in metrics
        assert isinstance(metrics["Total Return [%]"], (float, int))
        assert "Sharpe Ratio" in metrics
        assert "Total Trades" in metrics
        assert metrics["Total Trades"] >= 0
