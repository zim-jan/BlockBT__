import pytest

# To import spowoduje błąd, bo plik nie istnieje - i o to chodzi w TDD (RED phase)
try:
    from app.services.engine.qsadapter import QSAdapterService
except ImportError:
    QSAdapterService = None

def test_generate_html_tearsheet():
    # Zakładając mockowany obiekt portfela vectorbt
    class MockPortfolio:
        def stats(self):
            return {"Sharpe Ratio": 1.5}
            
    pf = MockPortfolio()
    if QSAdapterService is None:
        pytest.fail("QSAdapterService not implemented yet")
        
    html_output = QSAdapterService.generate_tearsheet(pf)

    assert html_output is not None
    assert "<html>" in html_output
    assert "Sharpe Ratio" in html_output


def test_generate_tearsheet_from_series_stats():
    """Faza 13: stats() zwracające pandas.Series musi być poprawnie znormalizowane."""
    import pandas as pd

    if QSAdapterService is None:
        pytest.fail("QSAdapterService not implemented yet")

    class SeriesPortfolio:
        def stats(self):
            return pd.Series({"Sharpe Ratio": 1.5, "Max Drawdown [%]": -12.3})

    html_output = QSAdapterService.generate_tearsheet(SeriesPortfolio())

    assert "<html>" in html_output
    assert "Sharpe Ratio" in html_output
    assert "Max Drawdown [%]" in html_output
    assert "1.5" in html_output


def test_generate_tearsheet_empty_metrics():
    """Faza 13: portfel bez metryk (stats() rzuca) → poprawny HTML, komunikat o braku."""
    if QSAdapterService is None:
        pytest.fail("QSAdapterService not implemented yet")

    class BrokenPortfolio:
        def stats(self):
            raise RuntimeError("no stats available")

    html_output = QSAdapterService.generate_tearsheet(BrokenPortfolio())

    assert "<html>" in html_output
    assert "Brak dostępnych metryk" in html_output
