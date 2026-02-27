"""
Tester for GAT-parser
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
import polars as pl
from core.parser import GatParser, WideFormatParser, auto_detect_format

def test_long_format_parsing():
    """Test parsing av long format data"""
    print("Testing long format parsing...")
    
    # Lag testdata
    data = {
        "Dato": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Ansattnr": ["A001", "A001", "A002"],
        "Vakt": ["D1", "N1", "D1"],
        "Avdeling": ["Kirurgi", "Kirurgi", "Medisin"]
    }
    df = pl.DataFrame(data)
    
    parser = GatParser()
    result = parser.parse_dataframe(df)
    
    # Sjekk at kolonner er standardisert
    assert "dato" in result.columns
    assert "ansatt_id" in result.columns
    assert "vakt" in result.columns
    assert "avdeling" in result.columns
    
    # Sjekk at vaktkoder er uppercase
    assert all(v in ["D1", "N1"] for v in result["vakt"].to_list())
    
    print("✅ Long format parsing OK")

def test_wide_format_parsing():
    """Test parsing av wide format data"""
    print("Testing wide format parsing...")
    
    # Lag testdata i wide format
    data = {
        "Ansatt": ["A001", "A002"],
        "01.01": ["D1", "F"],
        "02.01": ["N1", "D1"],
        "03.01": ["F", "N1"]
    }
    df = pl.DataFrame(data)
    
    parser = WideFormatParser()
    result = parser.parse(df, employee_col="Ansatt")
    
    # Sjekk at vi fikk long format
    assert len(result) == 6  # 2 ansatte * 3 dager
    assert "ansatt_id" in result.columns
    assert "dato" in result.columns
    assert "vakt" in result.columns
    
    print(f"✅ Wide format parsing OK ({len(result)} rader)")

def test_auto_detect():
    """Test auto-deteksjon av format"""
    print("Testing auto-detect...")
    
    # Wide format
    wide_data = {"Ansatt": ["A"], "01.01": ["D"], "02.01": ["N"], "03.01": ["F"]}
    wide_df = pl.DataFrame(wide_data)
    assert auto_detect_format(wide_df) == "wide"
    
    # Long format
    long_data = {"dato": ["2024-01-01"], "vakt": ["D1"], "ansatt": ["A"]}
    long_df = pl.DataFrame(long_data)
    assert auto_detect_format(long_df) == "long"
    
    print("✅ Auto-detect OK")

def test_merged_cells():
    """Test håndtering av merged cells"""
    print("Testing merged cells...")
    
    # Simuler merged cells med null-verdier
    data = {
        "dato": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "ansatt_id": ["A001", None, None],  # Merged cell
        "vakt": ["D1", "N1", "F"]
    }
    df = pl.DataFrame(data)
    
    parser = GatParser()
    result = parser.parse_dataframe(df)
    
    # Sjekk at null-verdier er fylt
    assert result["ansatt_id"].null_count() == 0
    assert all(a == "A001" for a in result["ansatt_id"].to_list())
    
    print("✅ Merged cells OK")

def test_norwegian_dates():
    """Test parsing av norske datoformater"""
    print("Testing Norwegian date formats...")
    
    formats = [
        ("2024-01-01", "%Y-%m-%d"),
        ("01.01.2024", "%d.%m.%Y"),
        ("01/01/2024", "%d/%m/%Y"),
    ]
    
    for date_str, fmt in formats:
        data = {"dato": [date_str], "vakt": ["D1"], "ansatt_id": ["A001"]}
        df = pl.DataFrame(data)
        
        parser = GatParser()
        result = parser.parse_dataframe(df)
        
        # Sjekk at dato ble parsed
        assert result["dato"].dtype in [pl.Date, pl.Datetime]
    
    print("✅ Norwegian date formats OK")

if __name__ == "__main__":
    print("=" * 50)
    print("Kjører GAT-parser-tester")
    print("=" * 50)
    
    test_long_format_parsing()
    test_wide_format_parsing()
    test_auto_detect()
    test_merged_cells()
    test_norwegian_dates()
    
    print("=" * 50)
    print("Alle parser-tester bestått! ✅")
    print("=" * 50)
