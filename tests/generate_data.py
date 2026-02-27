"""
Generer testdata for Turnus
"""
from datetime import datetime, timedelta
import random
import polars as pl

def generate_sample_data(num_employees: int = 5, num_weeks: int = 4, 
                         institution: str = "default") -> pl.DataFrame:
    """Generer eksempeldata for testing"""
    
    # Vaktkoder fra standard institusjon
    shift_codes = ["D1", "D2", "A1", "N1", "F"]
    weights = [0.4, 0.15, 0.2, 0.15, 0.1]  # Sannsynlighetsfordeling
    
    data = []
    start_date = datetime(2024, 1, 1)
    
    for emp_id in range(1, num_employees + 1):
        for day in range(num_weeks * 7):
            date = start_date + timedelta(days=day)
            code = random.choices(shift_codes, weights=weights)[0]
            
            data.append({
                "dato": date.date(),
                "ansatt_id": f"EMP{emp_id:03d}",
                "vakt": code,
                "avdeling": "Kirurgi"
            })
    
    return pl.DataFrame(data)

def generate_problematic_data(num_employees: int = 3, num_weeks: int = 2) -> pl.DataFrame:
    """Generer data med kjente problemer (for testing av violations)"""
    
    data = []
    start_date = datetime(2024, 1, 1)
    
    # Ansatt 1: Korte hvileperioder (D1 -> N1)
    emp1_pattern = ["D1", "N1", "D1", "N1", "F", "F"]
    
    # Ansatt 2: Mange netter på rad
    emp2_pattern = ["N1", "N1", "N1", "N1", "N1", "F", "F"]
    
    # Ansatt 3: OK mønster
    emp3_pattern = ["D1", "D1", "A1", "N1", "F", "F", "D1"]
    
    patterns = [emp1_pattern, emp2_pattern, emp3_pattern]
    
    for emp_idx, pattern in enumerate(patterns):
        emp_id = f"EMP{emp_idx + 1:03d}"
        for day in range(num_weeks * 7):
            date = start_date + timedelta(days=day)
            code = pattern[day % len(pattern)]
            
            data.append({
                "dato": date.date(),
                "ansatt_id": emp_id,
                "vakt": code,
                "avdeling": "Kirurgi"
            })
    
    return pl.DataFrame(data)

if __name__ == "__main__":
    # Lagre testdata
    normal_data = generate_sample_data()
    problem_data = generate_problematic_data()
    
    normal_data.write_csv("/root/.openclaw/workspace/Turnus/data/sample_normal.csv")
    problem_data.write_csv("/root/.openclaw/workspace/Turnus/data/sample_problems.csv")
    
    print("Testdata generert:")
    print(f"- data/sample_normal.csv ({len(normal_data)} rader)")
    print(f"- data/sample_problems.csv ({len(problem_data)} rader)")
