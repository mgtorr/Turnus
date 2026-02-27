"""
Historisk analyse av turnusdata
"""
from datetime import datetime, timedelta
from typing import Optional
import polars as pl
from .vaktkoder import VaktKodeManager
from .simulator import Shift, TurnusSimulator

class HistoricalAnalyzer:
    """Analyser historiske turnusdata for belastning og mønstre"""
    
    def __init__(self, institution_id: str = "default"):
        self.vakt_mgr = VaktKodeManager()
        self.vakt_mgr.set_institution(institution_id)
        self.simulator = TurnusSimulator(institution_id)
    
    def analyze_dataframe(self, df: pl.DataFrame, date_col: str = "dato",
                         code_col: str = "vakt", emp_col: str = "ansatt_id") -> dict:
        """
        Analyser en dataframe med historiske turnusdata
        
        Forventet format:
        - dato: datetime eller date
        - vakt: vaktkode (D1, N1, etc.)
        - ansatt_id: ansatt-identifikator
        """
        # Konverter til Shift-objekter
        shifts = []
        for row in df.iter_rows(named=True):
            date_val = row[date_col]
            if isinstance(date_val, str):
                date_val = datetime.strptime(date_val, "%Y-%m-%d")
            elif hasattr(date_val, 'date') and callable(getattr(date_val, 'date')):
                # Already datetime
                pass
            else:
                # Convert date to datetime
                date_val = datetime.combine(date_val, datetime.min.time())
            shifts.append(Shift(
                date=date_val,
                code=row[code_col],
                employee_id=str(row[emp_col])
            ))
        
        # Kjør simulering for compliance
        compliance = self.simulator.simulate_schedule(shifts)
        
        # Ekstra historiske analyser
        historical = {
            "fatigue_trends": self._analyze_fatigue_trends(shifts),
            "workload_distribution": self._analyze_workload_distribution(shifts),
            "rotation_patterns": self._analyze_rotation_patterns(shifts),
            "weekend_equity": self._analyze_weekend_equity(shifts),
            "night_equity": self._analyze_night_equity(shifts),
            "seasonal_patterns": self._analyze_seasonal_patterns(shifts)
        }
        
        return {
            "compliance": compliance,
            "historical": historical,
            "summary": self._generate_summary(compliance, historical)
        }
    
    def _analyze_fatigue_trends(self, shifts: list[Shift]) -> dict:
        """Analyser trender i belastning over tid"""
        if not shifts:
            return {}
        
        # Grupper etter måned
        by_month = {}
        for s in shifts:
            month_key = s.date.strftime("%Y-%m")
            by_month.setdefault(month_key, []).append(s)
        
        trends = {}
        for month, month_shifts in sorted(by_month.items()):
            result = self.simulator.simulate_schedule(month_shifts)
            trends[month] = {
                "risk_score": result["risk_score"]["normalized"],
                "critical_violations": result["risk_score"]["critical_count"],
                "avg_hours_per_employee": sum(result["stats"]["hours_per_employee"].values()) / 
                                          max(len(result["stats"]["hours_per_employee"]), 1)
            }
        
        return trends
    
    def _analyze_workload_distribution(self, shifts: list[Shift]) -> dict:
        """Analyser fordeling av arbeidsbelastning"""
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        hours = []
        for emp_id, emp_shifts in by_employee.items():
            total = sum(
                self.vakt_mgr.get_code_info(s.code)["duration_hours"]
                for s in emp_shifts if self.vakt_mgr.get_code_info(s.code)
            )
            hours.append({"employee": emp_id, "hours": total})
        
        if not hours:
            return {}
        
        hours_list = [h["hours"] for h in hours]
        avg_hours = sum(hours_list) / len(hours_list)
        
        return {
            "average_hours": round(avg_hours, 2),
            "min_hours": round(min(hours_list), 2),
            "max_hours": round(max(hours_list), 2),
            "std_deviation": round(self._std_dev(hours_list), 2),
            "equity_score": self._calculate_equity_score(hours_list),
            "overloaded_employees": [h["employee"] for h in hours if h["hours"] > avg_hours * 1.2],
            "underloaded_employees": [h["employee"] for h in hours if h["hours"] < avg_hours * 0.8]
        }
    
    def _analyze_rotation_patterns(self, shifts: list[Shift]) -> dict:
        """Analyser rotasjonsmønstre"""
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        patterns = {
            "forward_rotations": 0,  # dag -> kveld -> natt
            "backward_rotations": 0,  # natt -> dag
            "quick_returns": 0,  # Kort tid mellom vakter
            "long_breaks": 0  # Lange friperioder
        }
        
        type_order = {"day": 1, "evening": 2, "night": 3}
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            for i in range(len(emp_shifts) - 1):
                s1, s2 = emp_shifts[i], emp_shifts[i + 1]
                t1 = self.vakt_mgr.get_shift_type(s1.code)
                t2 = self.vakt_mgr.get_shift_type(s2.code)
                
                if t1 in type_order and t2 in type_order:
                    if type_order[t2] > type_order[t1]:
                        patterns["forward_rotations"] += 1
                    elif type_order[t2] < type_order[t1]:
                        patterns["backward_rotations"] += 1
                
                # Sjekk quick returns (< 11t)
                rest = self.vakt_mgr.calculate_rest_hours(
                    s1.code, s2.code, s1.date, s2.date
                )
                if 0 < rest < 11:
                    patterns["quick_returns"] += 1
                elif rest > 48:
                    patterns["long_breaks"] += 1
        
        total = sum(patterns.values())
        if total > 0:
            patterns["forward_ratio"] = round(patterns["forward_rotations"] / total, 2)
        
        return patterns
    
    def _analyze_weekend_equity(self, shifts: list[Shift]) -> dict:
        """Analyser rettferdig fordeling av helgevakter"""
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        weekend_counts = {}
        for emp_id, emp_shifts in by_employee.items():
            weekend_counts[emp_id] = sum(
                1 for s in emp_shifts 
                if s.date.weekday() >= 5 and self.vakt_mgr.is_working_shift(s.code)
            )
        
        if not weekend_counts:
            return {}
        
        counts = list(weekend_counts.values())
        return {
            "average_weekends": round(sum(counts) / len(counts), 2),
            "min_weekends": min(counts),
            "max_weekends": max(counts),
            "std_deviation": round(self._std_dev(counts), 2),
            "equity_score": self._calculate_equity_score(counts),
            "most_weekends": max(weekend_counts, key=weekend_counts.get),
            "least_weekends": min(weekend_counts, key=weekend_counts.get)
        }
    
    def _analyze_night_equity(self, shifts: list[Shift]) -> dict:
        """Analyser rettferdig fordeling av nattevakter"""
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        
        night_counts = {}
        for emp_id, emp_shifts in by_employee.items():
            night_counts[emp_id] = sum(
                1 for s in emp_shifts 
                if self.vakt_mgr.get_shift_type(s.code) == "night"
            )
        
        if not night_counts:
            return {}
        
        counts = list(night_counts.values())
        return {
            "average_nights": round(sum(counts) / len(counts), 2),
            "min_nights": min(counts),
            "max_nights": max(counts),
            "std_deviation": round(self._std_dev(counts), 2),
            "equity_score": self._calculate_equity_score(counts),
            "most_nights": max(night_counts, key=night_counts.get),
            "least_nights": min(night_counts, key=night_counts.get)
        }
    
    def _analyze_seasonal_patterns(self, shifts: list[Shift]) -> dict:
        """Analyser sesongvariasjoner"""
        by_month = {}
        for s in shifts:
            month = s.date.month
            by_month.setdefault(month, []).append(s)
        
        seasonal = {}
        for month, month_shifts in sorted(by_month.items()):
            total_shifts = len(month_shifts)
            night_shifts = sum(
                1 for s in month_shifts 
                if self.vakt_mgr.get_shift_type(s.code) == "night"
            )
            weekend_shifts = sum(
                1 for s in month_shifts 
                if s.date.weekday() >= 5 and self.vakt_mgr.is_working_shift(s.code)
            )
            
            month_name = datetime(2024, month, 1).strftime("%B")
            seasonal[month_name] = {
                "total_shifts": total_shifts,
                "night_shifts": night_shifts,
                "weekend_shifts": weekend_shifts,
                "night_percentage": round(night_shifts / max(total_shifts, 1) * 100, 1),
                "weekend_percentage": round(weekend_shifts / max(total_shifts, 1) * 100, 1)
            }
        
        return seasonal
    
    def _generate_summary(self, compliance: dict, historical: dict) -> dict:
        """Generer oppsummering av analysen"""
        risk = compliance["risk_score"]
        workload = historical.get("workload_distribution", {})
        
        return {
            "overall_health": "good" if risk["level"] == "low" else "moderate" if risk["level"] == "medium" else "poor",
            "main_concerns": self._identify_main_concerns(compliance, historical),
            "positive_findings": self._identify_positives(compliance, historical),
            "recommendations": self._generate_recommendations(compliance, historical)
        }
    
    def _identify_main_concerns(self, compliance: dict, historical: dict) -> list:
        """Identifiser hovedproblemer"""
        concerns = []
        
        if compliance["risk_score"]["critical_count"] > 0:
            concerns.append(f"{compliance['risk_score']['critical_count']} kritiske regelbrudd funnet")
        
        workload = historical.get("workload_distribution", {})
        if workload.get("equity_score", 100) < 70:
            concerns.append("Ujevn arbeidsbelastning mellom ansatte")
        
        weekend = historical.get("weekend_equity", {})
        if weekend.get("equity_score", 100) < 70:
            concerns.append("Urettferdig fordeling av helgevakter")
        
        night = historical.get("night_equity", {})
        if night.get("equity_score", 100) < 70:
            concerns.append("Urettferdig fordeling av nattevakter")
        
        return concerns
    
    def _identify_positives(self, compliance: dict, historical: dict) -> list:
        """Identifiser positive funn"""
        positives = []
        
        if compliance["risk_score"]["critical_count"] == 0:
            positives.append("Ingen kritiske regelbrudd")
        
        patterns = historical.get("rotation_patterns", {})
        if patterns.get("forward_ratio", 0) > 0.7:
            positives.append("God rotasjonspraksis (fremoverrotasjon)")
        
        return positives
    
    def _generate_recommendations(self, compliance: dict, historical: dict) -> list:
        """Generer anbefalinger"""
        recs = []
        
        violations = compliance.get("violations", [])
        daily_rest_violations = [v for v in violations if v.type == "daily_rest"]
        if len(daily_rest_violations) > 3:
            recs.append("Vurder å justere vaktlag for å unngå korte hvileperioder")
        
        workload = historical.get("workload_distribution", {})
        if workload.get("overloaded_employees"):
            recs.append(f"Reduser belastning for: {', '.join(workload['overloaded_employees'][:3])}")
        
        weekend = historical.get("weekend_equity", {})
        if weekend.get("equity_score", 100) < 70:
            recs.append("Gjennomgå fordeling av helgevakter for mer rettferdighet")
        
        return recs
    
    @staticmethod
    def _std_dev(values: list) -> float:
        """Kalkuler standardavvik"""
        if len(values) < 2:
            return 0
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    @staticmethod
    def _calculate_equity_score(values: list) -> float:
        """Kalkuler rettferdighetsscore (0-100)"""
        if not values or len(values) < 2:
            return 100
        
        avg = sum(values) / len(values)
        if avg == 0:
            return 100
        
        # Kalkuler gjennomsnittlig prosentvis avvik fra snitt
        deviations = [abs(v - avg) / avg for v in values]
        avg_deviation = sum(deviations) / len(deviations)
        
        # Konverter til score (lavere avvik = høyere score)
        score = max(0, 100 - (avg_deviation * 100))
        return round(score, 1)
