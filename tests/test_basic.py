"""
Enkle tester for Turnus
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from core.vaktkoder import VaktKodeManager
from core.simulator import TurnusSimulator, Shift
from core.analyzer import HistoricalAnalyzer

def test_vaktkoder():
    """Test vaktkode-håndtering"""
    print("Testing vaktkoder...")
    
    mgr = VaktKodeManager()
    
    # Sjekk at standard institusjon finnes
    assert "default" in mgr.list_institutions()
    
    # Sjekk at D1 er en dagvakt
    info = mgr.get_code_info("D1")
    assert info["type"] == "day"
    assert info["duration_hours"] == 8
    
    # Sjekk at F er fri
    assert not mgr.is_working_shift("F")
    
    print("✅ Vaktkoder OK")

def test_simulator():
    """Test simulator"""
    print("Testing simulator...")
    
    sim = TurnusSimulator("default")
    
    # Lag en enkel turnus med problem: D2 (lang dag) etterfulgt av N1 (kort hvile)
    # D2 slutter 19:00, N1 starter 21:00 samme kveld = kun 2t hvile!
    shifts = [
        Shift(datetime(2024, 1, 1), "D2", "EMP001"),  # Slutter 19:00
        Shift(datetime(2024, 1, 1), "N1", "EMP001"),  # Starter 21:00 samme dag - kun 2t hvile!
    ]
    
    result = sim.simulate_schedule(shifts)
    
    # Skal finne daily_rest violation
    violations = [v for v in result['violations'] if v.type == 'daily_rest']
    assert len(violations) > 0, "Skal finne kort hviletid"
    
    print(f"✅ Simulator OK (fant {len(violations)} hvile-brudd)")

def test_analyzer():
    """Test historisk analyse"""
    print("Testing analyzer...")
    
    import polars as pl
    
    # Lag testdata
    data = {
        "dato": [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        "vakt": ["D1", "N1", "F"],
        "ansatt_id": ["EMP001", "EMP001", "EMP001"]
    }
    df = pl.DataFrame(data)
    
    analyzer = HistoricalAnalyzer("default")
    result = analyzer.analyze_dataframe(df)
    
    assert "compliance" in result
    assert "historical" in result
    
    print("✅ Analyzer OK")

def test_equity_score():
    """Test rettferdighetsberegning"""
    print("Testing equity score...")
    
    # Perfekt rettferdighet
    perfect = HistoricalAnalyzer._calculate_equity_score([10, 10, 10, 10])
    assert perfect == 100, f"Forventet 100, fikk {perfect}"
    
    # Ujevn fordeling
    uneven = HistoricalAnalyzer._calculate_equity_score([5, 10, 15])
    assert uneven < 100, f"Forventet <100, fikk {uneven}"
    
    print(f"✅ Equity score OK (perfekt: {perfect}, ujevn: {uneven})")

if __name__ == "__main__":
    print("=" * 50)
    print("Kjører Turnus-tester")
    print("=" * 50)
    
    test_vaktkoder()
    test_simulator()
    test_analyzer()
    test_equity_score()
    
    print("=" * 50)
    print("Alle tester bestått! ✅")
    print("=" * 50)
