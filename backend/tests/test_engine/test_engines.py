from __future__ import annotations

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
