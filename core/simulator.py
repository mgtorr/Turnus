"""
Turnus-simulator for testing av scenarier
"""
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
import polars as pl
from .vaktkoder import VaktKodeManager

@dataclass
class Shift:
    """En enkelt vakt"""
    date: datetime
    code: str
    employee_id: str
    
@dataclass  
class Violation:
    """En regelbrudd"""
    type: str
    severity: str  # "critical", "warning", "info"
    description: str
    paragraph: Optional[str]
    shift1: Optional[Shift] = None
    shift2: Optional[Shift] = None

class TurnusSimulator:
    """Simuler turnusplaner og sjekk compliance"""
    
    def __init__(self, institution_id: str = "default"):
        self.vakt_mgr = VaktKodeManager()
        self.vakt_mgr.set_institution(institution_id)
        self.rules = self.vakt_mgr.get_rules()
    
    def simulate_schedule(self, shifts: list[Shift]) -> dict:
        """
        Simuler en turnusplan og returner analyse
        
        Returns:
            dict med violations, stats, og risk_score
        """
        violations = []
        
        # Sorter vakter etter dato
        shifts_sorted = sorted(shifts, key=lambda s: s.date)
        
        # Sjekk hviletid mellom vakter
        violations.extend(self._check_daily_rest(shifts_sorted))
        
        # Sjekk ukentlig hvile
        violations.extend(self._check_weekly_rest(shifts_sorted))
        
        # Sjekk søndagsvakter
        violations.extend(self._check_sunday_rotation(shifts_sorted))
        
        # Sjekk uketimer
        violations.extend(self._check_weekly_hours(shifts_sorted))
        
        # Sjekk påfølgende nattevakter
        violations.extend(self._check_consecutive_nights(shifts_sorted))
        
        # Sjekk rotasjonsretning
        violations.extend(self._check_rotation_direction(shifts_sorted))
        
        # Kalkuler statistikk
        stats = self._calculate_stats(shifts_sorted)
        
        # Kalkuler risikoscore
        risk_score = self._calculate_risk_score(violations, stats)
        
        return {
            "violations": violations,
            "stats": stats,
            "risk_score": risk_score,
            "compliant": len([v for v in violations if v.severity == "critical"]) == 0
        }
    
    def _check_daily_rest(self, shifts: list[Shift]) -> list[Violation]:
        """Sjekk AML § 10-8: 11 timer daglig hvile"""
        violations = []
        min_rest = self.rules["aml_daily_rest"]["hours"]
        
        for i in range(len(shifts) - 1):
            shift1, shift2 = shifts[i], shifts[i + 1]
            
            # Hvis samme ansatt
            if shift1.employee_id != shift2.employee_id:
                continue
                
            rest_hours = self.vakt_mgr.calculate_rest_hours(
                shift1.code, shift2.code, 
                shift1.date, shift2.date
            )
            
            if rest_hours < min_rest and rest_hours >= 0:
                violations.append(Violation(
                    type="daily_rest",
                    severity="critical" if rest_hours < 8 else "warning",
                    description=f"Kun {rest_hours:.1f}t hvile (krever {min_rest}t)",
                    paragraph=self.rules["aml_daily_rest"]["paragraph"],
                    shift1=shift1,
                    shift2=shift2
                ))
        
        return violations
    
    def _check_weekly_rest(self, shifts: list[Shift]) -> list[Violation]:
        """Sjekk AML § 10-8: 35 timer ukentlig hvile"""
        violations = []
        min_weekly_rest = self.rules["aml_weekly_rest"]["hours"]
        
        # Grupper etter ansatt
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            # Sjekk hver 168-timers periode
            for i, shift in enumerate(emp_shifts):
                window_start = shift.date
                window_end = window_start + timedelta(hours=168)
                
                # Finn alle vakter i vinduet
                window_shifts = [
                    s for s in emp_shifts 
                    if window_start <= s.date < window_end
                ]
                
                # Finn lengste hvileperiode
                max_rest = self._find_max_rest_in_window(window_shifts, window_start, window_end)
                
                if max_rest < min_weekly_rest:
                    violations.append(Violation(
                        type="weekly_rest",
                        severity="critical",
                        description=f"Maks {max_rest:.1f}t sammenhengende hvile i 168t periode",
                        paragraph=self.rules["aml_weekly_rest"]["paragraph"],
                        shift1=shift
                    ))
        
        return violations
    
    def _find_max_rest_in_window(self, shifts: list[Shift], window_start: datetime, 
                                  window_end: datetime) -> float:
        """Finn lengste sammenhengende hvileperiode i et tidsvindu"""
        if not shifts:
            return 168  # Hele uken fri
        
        # Legg til start og slutt av vinduet
        times = [window_start]
        for s in shifts:
            if self.vakt_mgr.is_working_shift(s.code):
                info = self.vakt_mgr.get_code_info(s.code)
                start_time = datetime.combine(s.date, datetime.strptime(info["start"], "%H:%M").time())
                end_time = datetime.combine(s.date, datetime.strptime(info["end"], "%H:%M").time())
                if info["end"] < info["start"]:  # Nattvakt
                    end_time += timedelta(days=1)
                times.extend([start_time, end_time])
        times.append(window_end)
        
        times.sort()
        
        # Finn lengste gap
        max_rest = 0
        for i in range(0, len(times) - 1, 2):
            gap = (times[i + 1] - times[i]).total_seconds() / 3600
            max_rest = max(max_rest, gap)
        
        return max_rest
    
    def _check_sunday_rotation(self, shifts: list[Shift]) -> list[Violation]:
        """Sjekk maks 3 påfølgende søndager"""
        violations = []
        max_sundays = self.rules["max_consecutive_sundays"]
        
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        for emp_id, emp_shifts in by_employee.items():
            sundays = sorted([
                s for s in emp_shifts 
                if s.date.weekday() == 6 and self.vakt_mgr.is_working_shift(s.code)
            ], key=lambda s: s.date)
            
            consecutive = 1
            for i in range(1, len(sundays)):
                if (sundays[i].date - sundays[i-1].date).days == 7:
                    consecutive += 1
                    if consecutive > max_sundays:
                        violations.append(Violation(
                            type="sunday_rotation",
                            severity="warning",
                            description=f"{consecutive} påfølgende søndagsvakter",
                            paragraph="AML § 10-8 (lokale avtaler)",
                            shift1=sundays[i-consecutive+1],
                            shift2=sundays[i]
                        ))
                else:
                    consecutive = 1
        
        return violations
    
    def _check_weekly_hours(self, shifts: list[Shift]) -> list[Violation]:
        """Sjekk ukentlig arbeidstid"""
        violations = []
        max_hta = self.rules["max_weekly_hours"]["hta"]
        max_hard = self.rules["max_weekly_hours"]["hard_limit"]
        
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        for emp_id, emp_shifts in by_employee.items():
            # Grupper etter uke
            weeks = {}
            for s in emp_shifts:
                week_key = s.date.isocalendar()[:2]  # (år, uke)
                info = self.vakt_mgr.get_code_info(s.code)
                if info:
                    weeks.setdefault(week_key, 0)
                    if self.vakt_mgr.is_working_shift(s.code):
                        weeks[week_key] += info["duration_hours"]
            
            for week, hours in weeks.items():
                if hours > max_hard:
                    violations.append(Violation(
                        type="weekly_hours",
                        severity="critical",
                        description=f"{hours:.1f}t i uke {week[1]} (maks {max_hard}t)",
                        paragraph="AML § 10-6",
                        shift1=next((s for s in emp_shifts if s.date.isocalendar()[:2] == week), None)
                    ))
                elif hours > max_hta:
                    violations.append(Violation(
                        type="weekly_hours",
                        severity="warning",
                        description=f"{hours:.1f}t i uke {week[1]} (HTA: {max_hta}t)",
                        paragraph="HTA 2024",
                        shift1=next((s for s in emp_shifts if s.date.isocalendar()[:2] == week), None)
                    ))
        
        return violations
    
    def _check_consecutive_nights(self, shifts: list[Shift]) -> list[Violation]:
        """Sjekk maks påfølgende nattevakter"""
        violations = []
        max_nights = self.rules["max_consecutive_nights"]
        
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            consecutive = 0
            for s in emp_shifts:
                if self.vakt_mgr.get_shift_type(s.code) == "night":
                    consecutive += 1
                    if consecutive > max_nights:
                        violations.append(Violation(
                            type="consecutive_nights",
                            severity="warning",
                            description=f"{consecutive} påfølgende nattevakter",
                            paragraph="HTA/Arbeidsmiljø",
                            shift1=s
                        ))
                else:
                    consecutive = 0
        
        return violations
    
    def _check_rotation_direction(self, shifts: list[Shift]) -> list[Violation]:
        """Sjekk for ugunstig rotasjon (natt -> dag)"""
        violations = []
        
        type_order = {"night": 3, "evening": 2, "day": 1, "weekend": 1}
        
        for i in range(len(shifts) - 1):
            s1, s2 = shifts[i], shifts[i + 1]
            
            if s1.employee_id != s2.employee_id:
                continue
            
            t1 = self.vakt_mgr.get_shift_type(s1.code)
            t2 = self.vakt_mgr.get_shift_type(s2.code)
            
            if t1 in type_order and t2 in type_order:
                if type_order[t1] > type_order[t2]:  # Bakover rotasjon
                    violations.append(Violation(
                        type="backward_rotation",
                        severity="info",
                        description=f"Bakover rotasjon: {t1} -> {t2}",
                        paragraph="Anbefaling: Fremover rotasjon foretrekkes",
                        shift1=s1,
                        shift2=s2
                    ))
        
        return violations
    
    def _calculate_stats(self, shifts: list[Shift]) -> dict:
        """Kalkuler turnus-statistikk"""
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        stats = {
            "total_shifts": len(shifts),
            "total_employees": len(by_employee),
            "shifts_per_employee": {},
            "hours_per_employee": {},
            "shift_type_distribution": {},
            "weekend_shifts": 0,
            "night_shifts": 0
        }
        
        for emp_id, emp_shifts in by_employee.items():
            stats["shifts_per_employee"][emp_id] = len(emp_shifts)
            total_hours = sum(
                self.vakt_mgr.get_code_info(s.code)["duration_hours"]
                for s in emp_shifts if self.vakt_mgr.get_code_info(s.code)
            )
            stats["hours_per_employee"][emp_id] = total_hours
            
            for s in emp_shifts:
                shift_type = self.vakt_mgr.get_shift_type(s.code)
                stats["shift_type_distribution"][shift_type] = \
                    stats["shift_type_distribution"].get(shift_type, 0) + 1
                
                if s.date.weekday() >= 5:  # Lørdag/søndag
                    stats["weekend_shifts"] += 1
                if shift_type == "night":
                    stats["night_shifts"] += 1
        
        return stats
    
    def _calculate_risk_score(self, violations: list[Violation], stats: dict) -> dict:
        """Kalkuler samlet risikoscore"""
        severity_weights = {"critical": 10, "warning": 5, "info": 1}
        
        total_weight = sum(severity_weights[v.severity] for v in violations)
        
        # Normaliser basert på antall vakter
        num_shifts = max(stats["total_shifts"], 1)
        normalized_score = (total_weight / num_shifts) * 100
        
        return {
            "raw_score": total_weight,
            "normalized": round(normalized_score, 2),
            "critical_count": len([v for v in violations if v.severity == "critical"]),
            "warning_count": len([v for v in violations if v.severity == "warning"]),
            "info_count": len([v for v in violations if v.severity == "info"]),
            "level": "high" if normalized_score > 50 else "medium" if normalized_score > 20 else "low"
        }
