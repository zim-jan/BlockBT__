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
