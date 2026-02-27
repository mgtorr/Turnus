#!/usr/bin/env python3
"""
Demo script for Turnus - tests core functionality without Streamlit
"""
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.vaktkoder import VaktKodeManager
from core.simulator import TurnusSimulator, Shift
from core.analyzer import HistoricalAnalyzer
from core.parser import GatParser, WideFormatParser

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def demo_vaktkoder():
    print_header("VAKTKODER - Konfigurerbare vaktkoder")
    
    mgr = VaktKodeManager()
    
    print(f"\nTilgjengelige institusjoner:")
    for inst in mgr.list_institutions():
        print(f"  - {inst}: {mgr.get_institution_name(inst)}")
    
    print(f"\nStandard vaktkoder:")
    for code, info in list(mgr.get_codes("default").items())[:5]:
        print(f"  {code}: {info['name']} ({info['duration_hours']}t)")

def demo_simulator():
    print_header("SIMULATOR - Test turnus mot AML og HTA")
    
    sim = TurnusSimulator("default")
    
    # Lag en turnus med noen problemer
    shifts = [
        # Ansatt 1: Kort hvile (D2 slutter 19:00, N1 starter 21:00)
        Shift(datetime(2024, 1, 1), "D2", "EMP001"),
        Shift(datetime(2024, 1, 1), "N1", "EMP001"),
        
        # Ansatt 2: Mange netter på rad
        Shift(datetime(2024, 1, 1), "N1", "EMP002"),
        Shift(datetime(2024, 1, 2), "N1", "EMP002"),
        Shift(datetime(2024, 1, 3), "N1", "EMP002"),
        Shift(datetime(2024, 1, 4), "N1", "EMP002"),  # 4. natt - brudd!
        
        # Ansatt 3: OK turnus
        Shift(datetime(2024, 1, 1), "D1", "EMP003"),
        Shift(datetime(2024, 1, 2), "D1", "EMP003"),
        Shift(datetime(2024, 1, 3), "F", "EMP003"),
    ]
    
    result = sim.simulate_schedule(shifts)
    
    print(f"\nResultater:")
    print(f"  Total risikoscore: {result['risk_score']['normalized']}")
    print(f"  AML-brudd: {result['risk_score']['aml_violations']}")
    print(f"  HTA-brudd: {result['risk_score']['hta_violations']}")
    print(f"  Kritiske: {result['risk_score']['critical_count']}")
    print(f"  Advarsler: {result['risk_score']['warning_count']}")
    
    print(f"\nFunne avvik:")
    for v in result['violations']:
        icon = "🔴" if v.severity == 'critical' else "🟡" if v.severity == 'warning' else "🔵"
        print(f"  {icon} [{v.paragraph or 'N/A'}] {v.description}")

def demo_analyzer():
    print_header("ANALYZER - Historisk analyse")
    
    import polars as pl
    
    # Lag testdata
    data = []
    start = datetime(2024, 1, 1)
    
    for emp_id in ["A001", "A002", "A003"]:
        for week in range(8):
            for day in range(7):
                date = start + timedelta(days=week * 7 + day)
                # Ujevn fordeling: A001 får flere netter
                if emp_id == "A001":
                    code = ["D1", "N1", "N1", "F"][day % 4]
                else:
                    code = ["D1", "D1", "F", "F"][day % 4]
                data.append({"dato": date.date(), "ansatt_id": emp_id, "vakt": code})
    
    df = pl.DataFrame(data)
    
    analyzer = HistoricalAnalyzer("default")
    result = analyzer.analyze_dataframe(df)
    
    print(f"\nOppsummering:")
    print(f"  Helsetilstand: {result['summary']['overall_health']}")
    
    print(f"\nHovedproblemer:")
    for concern in result['summary']['main_concerns']:
        print(f"  ⚠️  {concern}")
    
    print(f"\nAnbefalinger:")
    for rec in result['summary']['recommendations']:
        print(f"  💡 {rec}")
    
    # Belastningsfordeling
    wd = result['historical']['workload_distribution']
    print(f"\nBelastningsfordeling:")
    print(f"  Gj.snitt timer: {wd['average_hours']}")
    print(f"  Rettferdighet: {wd['equity_score']}%")
    
    # Nattefordeling
    ne = result['historical']['night_equity']
    print(f"\nNattefordeling:")
    print(f"  Gj.snitt netter: {ne['average_nights']}")
    print(f"  Rettferdighet: {ne['equity_score']}%")
    print(f"  Flest netter: {ne['most_nights']}")

def demo_parser():
    print_header("PARSER - Excel/GAT import")
    
    import polars as pl
    
    # Test long format
    long_data = {
        "Dato": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Pers.Nr": ["A001", "A001", "A002"],
        "Vaktkode": ["D1", "N1", "D1"],
    }
    df_long = pl.DataFrame(long_data)
    
    parser = GatParser()
    result = parser.parse_dataframe(df_long)
    
    print(f"\nLong format parsing:")
    print(f"  Input kolonner: {list(df_long.columns)}")
    print(f"  Output kolonner: {list(result.columns)}")
    print(f"  Rader: {len(result)}")
    
    # Test wide format
    wide_data = {
        "Ansatt": ["A001", "A002"],
        "01.01": ["D1", "F"],
        "02.01": ["N1", "D1"],
        "03.01": ["F", "N1"]
    }
    df_wide = pl.DataFrame(wide_data)
    
    wide_parser = WideFormatParser()
    result_wide = wide_parser.parse(df_wide, employee_col="Ansatt")
    
    print(f"\nWide format parsing:")
    print(f"  Input: {len(df_wide)} rader x {len(df_wide.columns)} kolonner")
    print(f"  Output: {len(result_wide)} rader (long format)")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🏥 TURNUS - Turnusplanlegging & Analyse               ║
    ║                                                          ║
    ║   Demo av core-funksjonalitet uten Streamlit UI         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    demo_vaktkoder()
    demo_simulator()
    demo_analyzer()
    demo_parser()
    
    print_header("DEMO FULLFØRT")
    print("\nFor å kjøre Streamlit UI:")
    print("  streamlit run app.py")
    print()

if __name__ == "__main__":
    main()
