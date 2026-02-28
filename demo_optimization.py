#!/usr/bin/env python3
"""
Demo av Optimization Agent
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from core.optimization_agent import OptimizationAgent

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🤖 OPTIMIZATION AGENT - Demo                          ║
    ║                                                          ║
    ║   Automatisk generering av turnusplaner                 ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Initialiser agent
    agent = OptimizationAgent("default")
    
    print_header("INPUT")
    
    # Definer problem
    employees = [f"EMP{i:03d}" for i in range(1, 6)]  # 5 ansatte
    start_date = datetime(2024, 3, 1)
    num_days = 14  # 2 uker
    
    # Beleggskrav: minst 3 personer på dagtid
    staffing = {
        "0": 3,  # Mandag
        "1": 3,  # Tirsdag
        "2": 3,  # Onsdag
        "3": 3,  # Torsdag
        "4": 3,  # Fredag
        "5": 2,  # Lørdag
        "6": 2,  # Søndag
    }
    
    print(f"Ansatte: {len(employees)} ({', '.join(employees)})")
    print(f"Periode: {num_days} dager fra {start_date.strftime('%Y-%m-%d')}")
    print(f"Beleggskrav: {staffing}")
    
    print_header("OPTIMALISERING")
    print("Genererer turnusplan... (dette kan ta noen sekunder)")
    
    # Kjør optimalisering
    result = agent.generate_schedule(
        employees=employees,
        start_date=start_date,
        num_days=num_days,
        staffing_requirements=staffing,
        max_iterations=500
    )
    
    print_header("RESULTAT")
    
    print(f"Score: {result['score']:.1f}")
    print(f"Iterasjoner: {result['iterations']}")
    print(f"Konvergert: {'Ja' if result['converged'] else 'Nei'}")
    print(f"Antall vakter: {len(result['schedule'])}")
    
    print("\n" + agent.explain_solution(result))
    
    print_header("EKSEMPEL PÅ VAKTER")
    
    # Vis første uke
    from collections import defaultdict
    by_date = defaultdict(list)
    for shift in sorted(result['schedule'], key=lambda s: s.date):
        by_date[shift.date.strftime('%Y-%m-%d')].append((shift.employee_id, shift.code))
    
    for date_str in sorted(by_date.keys())[:7]:
        shifts = by_date[date_str]
        print(f"\n{date_str}:")
        for emp, code in shifts:
            print(f"  {emp}: {code}")
    
    print_header("DEMO FULLFØRT")
    print("\nFor å integrere dette i Streamlit UI:")
    print("  1. Legg til 'Turnus Generator' side i app.py")
    print("  2. La brukeren definere beleggskrav")
    print("  3. Kjør agent.generate_schedule()")
    print("  4. Vis resultat med forklaring")
    print()

if __name__ == "__main__":
    main()
