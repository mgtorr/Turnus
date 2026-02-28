"""
Optimization Agent for Turnus
Genererer optimale turnusplaner basert på constraints og preferanser
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
from enum import Enum
import random
import copy

from .vaktkoder import VaktKodeManager
from .simulator import TurnusSimulator, Shift

class OptimizationAgent:
    """
    Agent for automatisk generering av turnusplaner
    
    Bruker constraint-satisfaction + local search for å finne gode løsninger
    """
    
    def __init__(self, institution_id: str = "default"):
        self.vakt_mgr = VaktKodeManager()
        self.vakt_mgr.set_institution(institution_id)
        self.simulator = TurnusSimulator(institution_id)
        self.rules = self.vakt_mgr.get_rules()
        self.vakt_mgr.set_institution(institution_id)
        self.simulator = TurnusSimulator(institution_id)
        self.rules = self.vakt_mgr.get_rules()
        
        # Tilgjengelige vaktkoder
        self.codes = [
            code for code, info in self.vakt_mgr.get_codes().items()
            if self.vakt_mgr.is_working_shift(code)
        ]
    
    def generate_schedule(
        self,
        employees: list[str],
        start_date: datetime,
        num_days: int,
        staffing_requirements: dict[str, int],
        employee_preferences: Optional[dict] = None,
        employee_competencies: Optional[dict] = None,
        fixed_shifts: Optional[list] = None,
        max_iterations: int = 1000
    ) -> dict:
        """
        Generer optimal turnusplan
        
        Args:
            employees: Liste over ansatt-IDer
            start_date: Startdato for turnus
            num_days: Antall dager å planlegge
            staffing_requirements: {dato: antall_personer} eller {ukedag: antall}
            employee_preferences: {emp_id: {preferanser}}
            employee_competencies: {emp_id: [kompetanser]}
            fixed_shifts: Låste vakter som ikke skal endres
            max_iterations: Maks optimaliseringsrunder
        
        Returns:
            {
                "schedule": [Shift, ...],
                "score": float,
                "violations": [Violation, ...],
                "iterations": int,
                "converged": bool
            }
        """
        
        # 1. Initial løsning (greedy)
        current = self._generate_initial_solution(
            employees, start_date, num_days, 
            staffing_requirements, fixed_shifts
        )
        
        # 2. Evaluer initial løsning
        best = copy.deepcopy(current)
        best_score = self._evaluate_solution(best)
        
        # 3. Local search (hill climbing med simulated annealing)
        temperature = 1.0
        cooling_rate = 0.995
        
        for iteration in range(max_iterations):
            # Generer nabo-løsning
            neighbor = self._generate_neighbor(current, employees)
            
            # Evaluer
            neighbor_score = self._evaluate_solution(neighbor)
            
            # Aksepter hvis bedre, eller med sannsynlighet basert på temperatur
            delta = neighbor_score - best_score
            
            if delta > 0 or random.random() < self._acceptance_probability(delta, temperature):
                current = neighbor
                
                if neighbor_score > best_score:
                    best = copy.deepcopy(neighbor)
                    best_score = neighbor_score
            
            temperature *= cooling_rate
            
            # Early stopping hvis konvergert
            if temperature < 0.001:
                break
        
        # 4. Returner beste funnet løsning
        result = self.simulator.simulate_schedule(best)
        
        return {
            "schedule": best,
            "score": best_score,
            "violations": result['violations'],
            "iterations": iteration + 1,
            "converged": temperature < 0.001,
            "compliance": result['compliant'],
            "hta_compliant": result.get('hta_compliant', True)
        }
    
    def _generate_initial_solution(
        self,
        employees: list[str],
        start_date: datetime,
        num_days: int,
        staffing_requirements: dict,
        fixed_shifts: Optional[list] = None
    ) -> list[Shift]:
        """Generer initial (greedy) løsning"""
        shifts = []
        fixed = fixed_shifts or []
        
        # Legg til faste vakter først
        shifts.extend(fixed)
        
        # For hver dag
        for day in range(num_days):
            date = start_date + timedelta(days=day)
            date_str = date.strftime("%Y-%m-%d")
            
            # Finn behov for denne dagen
            required = staffing_requirements.get(
                date_str,
                staffing_requirements.get(str(date.weekday()), 3)
            )
            
            # Fordel vakter (round-robin med rotasjon)
            for i in range(required):
                emp_idx = (day + i) % len(employees)
                emp_id = employees[emp_idx]
                
                # Velg vakttype basert på dag
                if date.weekday() >= 5:  # Helg
                    code = "H" if "H" in self.codes else "D1"
                else:
                    code = self.codes[emp_idx % len(self.codes)]
                
                # Sjekk at ikke allerede har vakt denne dagen
                existing = [s for s in shifts if s.employee_id == emp_id and s.date == date]
                if not existing:
                    shifts.append(Shift(date=date, code=code, employee_id=emp_id))
        
        return shifts
    
    def _generate_neighbor(self, current: list[Shift], employees: list[str]) -> list[Shift]:
        """Generer en nabo-løsning ved å gjøre en liten endring"""
        neighbor = copy.deepcopy(current)
        
        if not neighbor:
            return neighbor
        
        # Velg tilfeldig operasjon
        operation = random.choice(["swap", "change_code", "move"])
        
        if operation == "swap" and len(neighbor) >= 2:
            # Bytt to vakter mellom ansatte
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1].employee_id, neighbor[idx2].employee_id = \
                neighbor[idx2].employee_id, neighbor[idx1].employee_id
        
        elif operation == "change_code":
            # Endre vaktkode
            idx = random.randint(0, len(neighbor) - 1)
            old_code = neighbor[idx].code
            new_code = random.choice(self.codes)
            if new_code != old_code:
                neighbor[idx].code = new_code
        
        elif operation == "move":
            # Flytt en vakt til annen ansatt
            idx = random.randint(0, len(neighbor) - 1)
            new_emp = random.choice(employees)
            neighbor[idx].employee_id = new_emp
        
        return neighbor
    
    def _evaluate_solution(self, shifts: list[Shift]) -> float:
        """
        Evaluer en løsning og returner score
        
        Høyere score = bedre løsning
        """
        if not shifts:
            return -1000
        
        result = self.simulator.simulate_schedule(shifts)
        
        score = 100.0  # Baseline
        
        # Trekk for violations (vektet etter severity)
        for v in result['violations']:
            if v.severity == "critical":
                score -= 20
            elif v.severity == "warning":
                score -= 10
            else:
                score -= 2
        
        # Trekk for høy risikoscore
        score -= result['risk_score']['normalized'] * 0.5
        
        # Bonus for god dekning (antall vakter)
        score += len(shifts) * 0.5
        
        # Bonus for jevn fordeling
        stats = result['stats']
        if stats['hours_per_employee']:
            hours = list(stats['hours_per_employee'].values())
            avg_hours = sum(hours) / len(hours)
            variance = sum((h - avg_hours) ** 2 for h in hours) / len(hours)
            score -= variance * 0.1  # Trekk for ujevn fordeling
        
        return score
    
    def _acceptance_probability(self, delta: float, temperature: float) -> float:
        """Simulated annealing acceptance probability"""
        if delta > 0:
            return 1.0
        return 0.0  # Ikke aksepter dårligere løsninger (kan endres for SA)
    
    def explain_solution(self, result: dict) -> str:
        """Generer forklaring av løsningen"""
        lines = []
        lines.append("## Turnus-forslag")
        lines.append("")
        lines.append(f"**Score:** {result['score']:.1f}")
        lines.append(f"**Iterasjoner:** {result['iterations']}")
        lines.append(f"**Konvergert:** {'Ja' if result['converged'] else 'Nei'}")
        lines.append("")
        
        if result['compliance']:
            lines.append("✅ **AML-compliant:** Ingen kritiske brudd")
        else:
            lines.append("❌ **AML-brudd funnet**")
        
        if result['hta_compliant']:
            lines.append("✅ **HTA-compliant:** Ingen kritiske brudd")
        else:
            lines.append("⚠️ **HTA-brudd funnet**")
        
        lines.append("")
        lines.append("### Avvik som bør rettes:")
        
        critical = [v for v in result['violations'] if v.severity == 'critical']
        warnings = [v for v in result['violations'] if v.severity == 'warning']
        
        if critical:
            lines.append(f"\n**Kritiske ({len(critical)}):**")
            for v in critical[:5]:
                lines.append(f"- {v.description}")
        
        if warnings:
            lines.append(f"\n**Advarsler ({len(warnings)}):**")
            for v in warnings[:5]:
                lines.append(f"- {v.description}")
        
        if not critical and not warnings:
            lines.append("Ingen avvik funnet! 🎉")
        
        return "\n".join(lines)


# Hjelpefunksjoner for constraint-definisjon
def hard_constraint(func: Callable) -> Callable:
    """Marker en constraint som hard (må oppfylles)"""
    func.is_hard = True
    return func

def soft_constraint(weight: float = 1.0):
    """Marker en constraint som soft (kan brytes, men med straff)"""
    def decorator(func: Callable) -> Callable:
        func.is_hard = False
        func.weight = weight
        return func
    return decorator
