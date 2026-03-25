import os
from pathlib import Path

import optuna
import pandas as pd
import pytest

from blockbt.engine.loader import EngineLoader
from blockbt.db.models import StrategyTemplate


def test_scenario_1_macd_pipeline(tmp_path, sample_ohlcv):
    """
    Scenario 1: Signals and Engine.
    Load data from Parquet cache, run pandas-ta MACD integration,
    and verify the OpenSourceEngine returns non-empty simulation metrics.
    """
    # 1. Simulate Parquet Cache Loading
    parquet_path = tmp_path / "TEST_1d.parquet"
    sample_ohlcv.to_parquet(parquet_path)
    
    # Load from cache (as the real connector with use_cache=True would do)
    cached_df = pd.read_parquet(parquet_path)
    assert not cached_df.empty, "Parquet cache load failed."
    
    # 2. Setup MACD Strategy params required by OpenSourceEngine
    params = {
        "symbol": "TEST",
        "timeframe": "1d",
        "initial_capital": 10000.0,
        "strategy_type": "macd",
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
    }

    # 3. Run Pipeline
    engine = EngineLoader.load(force_opensource=True)
    result = engine.run_backtest(cached_df, params)

    # 4. Verify SimulationResult structure & metrics
    assert result["symbol"] == "TEST"
    assert result["engine_name"] == "opensource"
    assert isinstance(result["total_return_pct"], float)
    assert result["num_trades"] is not None
    assert isinstance(result["raw"], dict)
    
    # Check if raw portfolio stats are effectively loaded
    assert "Start Value" in result["raw"] or "Start" in result["raw"]
    assert "End Value" in result["raw"] or "End" in result["raw"]


def test_scenario_2_optuna_optimizer(db_session, sample_ohlcv):
    """
    Scenario 2: Optimizer.
    Run Optuna TPE to find best parameters (n_trials=5),
    then verify if the best parameters can be correctly saved to the database.
    """
    engine = EngineLoader.load(force_opensource=True)
    
    base_ws = {
        "symbol": "TEST",
        "timeframe": "1d",
        "initial_capital": 10000.0,
        "strategy_type": "sma_crossover",
    }
    
    def objective(trial: optuna.Trial) -> float:
        # Search space
        sma_fast = trial.suggest_int("sma_fast", 2, 10)
        sma_slow = trial.suggest_int("sma_slow", 11, 30)
        
        params = base_ws.copy()
        params.update({"sma_fast": sma_fast, "sma_slow": sma_slow})
        
        result = engine.run_backtest(sample_ohlcv, params)
        sr = result["sharpe_ratio"]
        
        # In this tiny sample some trials might have 0 trades -> None Sharpe Ratio
        if sr is None or pd.isna(sr):
            return -99.0
            
        return sr

    # 1. Run Optuna Optimization (TPE)
    study = optuna.create_study(direction="maximize")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study.optimize(objective, n_trials=5)

    assert len(study.trials) == 5
    best_params = study.best_params
    assert "sma_fast" in best_params
    assert "sma_slow" in best_params
    
    # 2. Save best parameters to Database
    final_state = base_ws.copy()
    final_state.update(best_params)

    # Create dummy user to fulfill foreign key if needed
    from blockbt.db.models import User
    test_user = User(username="quant", email="q@test.com", password_hash="hash")
    db_session.add(test_user)
    db_session.flush()

    tpl = StrategyTemplate(
        user_id=test_user.id,
        name="Optimized SMA",
        description="Optuna TPE results",
        wizard_state=final_state,
    )
    db_session.add(tpl)
    db_session.commit()
    
    # 3. Verify Database persistence
    saved_tpl = db_session.query(StrategyTemplate).filter_by(name="Optimized SMA").first()
    assert saved_tpl is not None
    assert saved_tpl.wizard_state["sma_fast"] == best_params["sma_fast"]
    assert saved_tpl.wizard_state["sma_slow"] == best_params["sma_slow"]
