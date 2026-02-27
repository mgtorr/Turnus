"""
Turnus-simulator for testing av scenarier
Integrerer både AML og HTA (Hovedtariffavtalen)
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
    """Simuler turnusplaner og sjekk compliance mot AML og HTA"""
    
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
        
        # === AML SJEKKER ===
        violations.extend(self._check_aml_daily_rest(shifts_sorted))
        violations.extend(self._check_aml_weekly_rest(shifts_sorted))
        violations.extend(self._check_aml_max_daily_hours(shifts_sorted))
        violations.extend(self._check_aml_max_weekly_hours(shifts_sorted))
        
        # === HTA SJEKKER ===
        violations.extend(self._check_hta_average_weekly_hours(shifts_sorted))
        violations.extend(self._check_hta_shift_length(shifts_sorted))
        violations.extend(self._check_hta_consecutive_nights(shifts_sorted))
        violations.extend(self._check_hta_rest_after_nights(shifts_sorted))
        violations.extend(self._check_hta_weekend_work(shifts_sorted))
        violations.extend(self._check_hta_free_weekend_after_nights(shifts_sorted))
        violations.extend(self._check_hta_rotation(shifts_sorted))
        violations.extend(self._check_hta_overtime(shifts_sorted))
        
        # Kalkuler statistikk
        stats = self._calculate_stats(shifts_sorted)
        
        # Kalkuler risikoscore
        risk_score = self._calculate_risk_score(violations, stats)
        
        # Kategoriser violations
        aml_violations = [v for v in violations if v.paragraph and "AML" in v.paragraph]
        hta_violations = [v for v in violations if v.paragraph and "HTA" in v.paragraph]
        
        return {
            "violations": violations,
            "aml_violations": aml_violations,
            "hta_violations": hta_violations,
            "stats": stats,
            "risk_score": risk_score,
            "compliant": len([v for v in violations if v.severity == "critical"]) == 0,
            "hta_compliant": len([v for v in hta_violations if v.severity == "critical"]) == 0
        }
    
    # === AML SJEKKER ===
    
    def _check_aml_daily_rest(self, shifts: list[Shift]) -> list[Violation]:
        """AML § 10-8: 11 timer daglig hvile"""
        violations = []
        rule = self.rules.get("aml_daily_rest", {})
        min_rest = rule.get("hours", 11)
        
        for i in range(len(shifts) - 1):
            shift1, shift2 = shifts[i], shifts[i + 1]
            
            if shift1.employee_id != shift2.employee_id:
                continue
                
            rest_hours = self.vakt_mgr.calculate_rest_hours(
                shift1.code, shift2.code, 
                shift1.date, shift2.date
            )
            
            if rest_hours < min_rest and rest_hours >= 0:
                violations.append(Violation(
                    type="aml_daily_rest",
                    severity="critical" if rest_hours < 8 else "warning",
                    description=f"Kun {rest_hours:.1f}t hvile (AML krever {min_rest}t)",
                    paragraph=rule.get("paragraph", "AML § 10-8"),
                    shift1=shift1,
                    shift2=shift2
                ))
        
        return violations
    
    def _check_aml_weekly_rest(self, shifts: list[Shift]) -> list[Violation]:
        """AML § 10-8: 35 timer ukentlig hvile"""
        violations = []
        rule = self.rules.get("aml_weekly_rest", {})
        min_weekly_rest = rule.get("hours", 35)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            for i, shift in enumerate(emp_shifts):
                window_start = shift.date
                window_end = window_start + timedelta(hours=168)
                
                window_shifts = [
                    s for s in emp_shifts 
                    if window_start <= s.date < window_end
                ]
                
                max_rest = self._find_max_rest_in_window(window_shifts, window_start, window_end)
                
                if max_rest < min_weekly_rest:
                    violations.append(Violation(
                        type="aml_weekly_rest",
                        severity="critical",
                        description=f"Maks {max_rest:.1f}t sammenhengende hvile i 168t periode",
                        paragraph=rule.get("paragraph", "AML § 10-8"),
                        shift1=shift
                    ))
        
        return violations
    
    def _check_aml_max_daily_hours(self, shifts: list[Shift]) -> list[Violation]:
        """AML § 10-5: Maks 13 timer per dag"""
        violations = []
        rule = self.rules.get("aml_max_daily_hours", {})
        max_hours = rule.get("hours", 13)
        
        for s in shifts:
            info = self.vakt_mgr.get_code_info(s.code)
            if info and info["duration_hours"] > max_hours:
                violations.append(Violation(
                    type="aml_max_daily_hours",
                    severity="critical",
                    description=f"Vakt på {info['duration_hours']}t (maks {max_hours}t)",
                    paragraph=rule.get("paragraph", "AML § 10-5"),
                    shift1=s
                ))
        
        return violations
    
    def _check_aml_max_weekly_hours(self, shifts: list[Shift]) -> list[Violation]:
        """AML § 10-6: Maks 48 timer per uke"""
        violations = []
        rule = self.rules.get("aml_max_weekly_hours", {})
        max_hours = rule.get("hours", 48)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            weeks = self._group_by_week(emp_shifts)
            
            for week, hours in weeks.items():
                if hours > max_hours:
                    violations.append(Violation(
                        type="aml_max_weekly_hours",
                        severity="critical",
                        description=f"{hours:.1f}t i uke {week[1]} (maks {max_hours}t)",
                        paragraph=rule.get("paragraph", "AML § 10-6"),
                        shift1=next((s for s in emp_shifts if s.date.isocalendar()[:2] == week), None)
                    ))
        
        return violations
    
    # === HTA SJEKKER ===
    
    def _check_hta_average_weekly_hours(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.1: Gjennomsnittlig 35.5t over 52 uker"""
        violations = []
        rule = self.rules.get("hta_average_weekly", {})
        target_hours = rule.get("hours", 35.5)
        averaging_weeks = rule.get("averaging_period_weeks", 52)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            if len(emp_shifts) < averaging_weeks * 3:  # Trenger nok data
                continue
            
            total_hours = sum(
                self.vakt_mgr.get_code_info(s.code)["duration_hours"]
                for s in emp_shifts if self.vakt_mgr.get_code_info(s.code)
            )
            
            # Kalkuler antall uker i datasettet
            dates = [s.date for s in emp_shifts]
            weeks_span = max((max(dates) - min(dates)).days // 7, 1)
            
            if weeks_span >= 4:  # Minimum 4 uker for meningsfull analyse
                avg_weekly = total_hours / weeks_span
                
                if avg_weekly > target_hours * 1.1:  # 10% over mål
                    violations.append(Violation(
                        type="hta_average_weekly",
                        severity="warning",
                        description=f"Gj.snitt {avg_weekly:.1f}t/uke over {weeks_span} uker (HTA: {target_hours}t)",
                        paragraph=rule.get("paragraph", "HTA kap 4 § 4.1")
                    ))
        
        return violations
    
    def _check_hta_shift_length(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.2: Maks vaktlengde (dag 12t, natt 10t)"""
        violations = []
        rule = self.rules.get("hta_max_shift_length", {})
        max_day = rule.get("day", 12)
        max_night = rule.get("night", 10)
        
        for s in shifts:
            info = self.vakt_mgr.get_code_info(s.code)
            if not info:
                continue
            
            shift_type = self.vakt_mgr.get_shift_type(s.code)
            duration = info["duration_hours"]
            
            if shift_type == "night" and duration > max_night:
                violations.append(Violation(
                    type="hta_max_shift_length_night",
                    severity="warning",
                    description=f"Nattevakt på {duration}t (HTA maks {max_night}t)",
                    paragraph=rule.get("paragraph", "HTA kap 4 § 4.2"),
                    shift1=s
                ))
            elif shift_type in ["day", "evening"] and duration > max_day:
                violations.append(Violation(
                    type="hta_max_shift_length_day",
                    severity="warning",
                    description=f"Dagvakt på {duration}t (HTA maks {max_day}t)",
                    paragraph=rule.get("paragraph", "HTA kap 4 § 4.2"),
                    shift1=s
                ))
        
        return violations
    
    def _check_hta_consecutive_nights(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.3: Maks 3 påfølgende nattevakter"""
        violations = []
        rule = self.rules.get("hta_consecutive_nights", {})
        max_nights = rule.get("max", 3)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            consecutive = 0
            night_streak_start = None
            
            for s in emp_shifts:
                if self.vakt_mgr.get_shift_type(s.code) == "night":
                    if consecutive == 0:
                        night_streak_start = s
                    consecutive += 1
                    
                    if consecutive > max_nights:
                        violations.append(Violation(
                            type="hta_consecutive_nights",
                            severity="critical" if consecutive > 4 else "warning",
                            description=f"{consecutive} påfølgende nattevakter (HTA maks {max_nights})",
                            paragraph=rule.get("paragraph", "HTA kap 4 § 4.3"),
                            shift1=night_streak_start,
                            shift2=s
                        ))
                else:
                    consecutive = 0
                    night_streak_start = None
        
        return violations
    
    def _check_hta_rest_after_nights(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.3: 46t fri etter 3 nattevakter"""
        violations = []
        rule = self.rules.get("hta_rest_after_nights", {})
        required_rest = rule.get("hours", 46)
        after_nights = rule.get("after_nights", 3)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            consecutive_nights = 0
            last_night_end = None
            
            for s in emp_shifts:
                if self.vakt_mgr.get_shift_type(s.code) == "night":
                    consecutive_nights += 1
                    info = self.vakt_mgr.get_code_info(s.code)
                    if info:
                        end_time = datetime.combine(s.date, datetime.strptime(info["end"], "%H:%M").time())
                        if info["end"] < info["start"]:
                            end_time += timedelta(days=1)
                        last_night_end = end_time
                else:
                    if consecutive_nights >= after_nights and last_night_end:
                        # Sjekk hvile etter nattevakter
                        next_shift_start = datetime.combine(s.date, datetime.min.time())
                        if self.vakt_mgr.is_working_shift(s.code):
                            info = self.vakt_mgr.get_code_info(s.code)
                            if info and info["start"]:
                                next_shift_start = datetime.combine(
                                    s.date, 
                                    datetime.strptime(info["start"], "%H:%M").time()
                                )
                        
                        rest_hours = (next_shift_start - last_night_end).total_seconds() / 3600
                        
                        if rest_hours < required_rest:
                            violations.append(Violation(
                                type="hta_rest_after_nights",
                                severity="warning",
                                description=f"Kun {rest_hours:.1f}t fri etter {consecutive_nights} netter (HTA krever {required_rest}t)",
                                paragraph=rule.get("paragraph", "HTA kap 4 § 4.3"),
                                shift1=s
                            ))
                    
                    consecutive_nights = 0
        
        return violations
    
    def _check_hta_weekend_work(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.4: Helgearbeid hver 2. eller 3. helg"""
        violations = []
        rule = self.rules.get("hta_weekend_work", {})
        max_every_nth = rule.get("max_every_nth_weekend", 2)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            # Finn alle helger med arbeid
            weekend_work = set()
            for s in emp_shifts:
                if s.date.weekday() >= 5 and self.vakt_mgr.is_working_shift(s.code):
                    week = s.date.isocalendar()[1]
                    weekend_work.add(week)
            
            if len(weekend_work) < 2:
                continue
            
            # Sjekk avstand mellom helgearbeid
            sorted_weekends = sorted(weekend_work)
            for i in range(len(sorted_weekends) - 1):
                gap = sorted_weekends[i + 1] - sorted_weekends[i]
                if gap < max_every_nth:
                    violations.append(Violation(
                        type="hta_weekend_work",
                        severity="info",
                        description=f"Helgearbeid {gap} uke(r) etter forrige (HTA anbefaler hver {max_every_nth}. helg)",
                        paragraph=rule.get("paragraph", "HTA kap 4 § 4.4")
                    ))
        
        return violations
    
    def _check_hta_free_weekend_after_nights(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.4: Fri helg etter nattevakter"""
        violations = []
        rule = self.rules.get("hta_free_weekend_after_nights", {})
        
        if not rule.get("enabled", True):
            return violations
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            emp_shifts = sorted(emp_shifts, key=lambda s: s.date)
            
            # Finn nattevakter som ender fredag/lørdag
            for i, s in enumerate(emp_shifts):
                if self.vakt_mgr.get_shift_type(s.code) != "night":
                    continue
                
                # Sjekk om nattevakten ender på en lørdag (dvs startet fredag)
                info = self.vakt_mgr.get_code_info(s.code)
                if not info:
                    continue
                
                end_date = s.date
                if info["end"] < info["start"]:
                    end_date = s.date + timedelta(days=1)
                
                # Hvis nattevakten ender lørdag morgen, sjekk at helgen er fri
                if end_date.weekday() == 5:  # Lørdag
                    # Sjekk neste 2 dager
                    weekend_dates = {end_date, end_date + timedelta(days=1)}
                    weekend_shifts = [
                        shift for shift in emp_shifts[i+1:]
                        if shift.date.date() in {d.date() for d in weekend_dates}
                        and self.vakt_mgr.is_working_shift(shift.code)
                    ]
                    
                    if weekend_shifts:
                        violations.append(Violation(
                            type="hta_free_weekend_after_nights",
                            severity="info",
                            description="Arbeid helgen etter nattevakt (HTA anbefaler fri helg)",
                            paragraph=rule.get("paragraph", "HTA kap 4 § 4.4"),
                            shift1=s
                        ))
        
        return violations
    
    def _check_hta_rotation(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 4 § 4.5: Rotasjonsprinsipper"""
        violations = []
        rule = self.rules.get("hta_rotation", {})
        
        type_order = {"night": 3, "evening": 2, "day": 1, "weekend": 1}
        
        for i in range(len(shifts) - 1):
            s1, s2 = shifts[i], shifts[i + 1]
            
            if s1.employee_id != s2.employee_id:
                continue
            
            t1 = self.vakt_mgr.get_shift_type(s1.code)
            t2 = self.vakt_mgr.get_shift_type(s2.code)
            
            if t1 not in type_order or t2 not in type_order:
                continue
            
            # Sjekk bakover rotasjon
            if type_order[t1] > type_order[t2]:
                # Sjekk hviletid
                rest = self.vakt_mgr.calculate_rest_hours(
                    s1.code, s2.code, s1.date, s2.date
                )
                
                # Bakover rotasjon krever lengre hvile
                if t1 == "night" and t2 == "day" and rest < 35:
                    violations.append(Violation(
                        type="hta_rotation_night_to_day",
                        severity="warning",
                        description=f"Natt -> Dag med kun {rest:.1f}t hvile (HTA krever 35t)",
                        paragraph=rule.get("paragraph", "HTA kap 4 § 4.5"),
                        shift1=s1,
                        shift2=s2
                    ))
                elif rest < 11:
                    violations.append(Violation(
                        type="hta_rotation_backward",
                        severity="info",
                        description=f"Bakover rotasjon ({t1} -> {t2}) med kort hvile ({rest:.1f}t)",
                        paragraph=rule.get("paragraph", "HTA kap 4 § 4.5"),
                        shift1=s1,
                        shift2=s2
                    ))
        
        return violations
    
    def _check_hta_overtime(self, shifts: list[Shift]) -> list[Violation]:
        """HTA kap 5: Overtidsgrenser"""
        violations = []
        rule = self.rules.get("hta_overtime", {})
        
        daily_threshold = rule.get("daily_threshold", 9)
        weekly_threshold = rule.get("weekly_threshold", 40)
        max_per_week = rule.get("max_per_week", 20)
        
        by_employee = self._group_by_employee(shifts)
        
        for emp_id, emp_shifts in by_employee.items():
            # Daglig overtid
            for s in emp_shifts:
                info = self.vakt_mgr.get_code_info(s.code)
                if info and info["duration_hours"] > daily_threshold:
                    overtime = info["duration_hours"] - daily_threshold
                    violations.append(Violation(
                        type="hta_overtime_daily",
                        severity="info",
                        description=f"{overtime:.1f}t daglig overtid",
                        paragraph=rule.get("paragraph", "HTA kap 5"),
                        shift1=s
                    ))
            
            # Ukentlig overtid
            weeks = self._group_by_week(emp_shifts)
            for week, hours in weeks.items():
                if hours > weekly_threshold:
                    overtime = hours - weekly_threshold
                    if overtime > max_per_week:
                        violations.append(Violation(
                            type="hta_overtime_weekly",
                            severity="warning",
                            description=f"{overtime:.1f}t overtid i uke {week[1]} (HTA maks {max_per_week}t)",
                            paragraph=rule.get("paragraph", "HTA kap 5"),
                            shift1=next((s for s in emp_shifts if s.date.isocalendar()[:2] == week), None)
                        ))
        
        return violations
    
    # === HJELPEMETODER ===
    
    def _group_by_employee(self, shifts: list[Shift]) -> dict:
        """Grupper vakter etter ansatt"""
        by_employee = {}
        for s in shifts:
            by_employee.setdefault(s.employee_id, []).append(s)
        return by_employee
    
    def _group_by_week(self, shifts: list[Shift]) -> dict:
        """Grupper timer etter uke"""
        weeks = {}
        for s in shifts:
            week_key = s.date.isocalendar()[:2]
            info = self.vakt_mgr.get_code_info(s.code)
            if info and self.vakt_mgr.is_working_shift(s.code):
                weeks.setdefault(week_key, 0)
                weeks[week_key] += info["duration_hours"]
        return weeks
    
    def _find_max_rest_in_window(self, shifts: list[Shift], window_start: datetime, 
                                  window_end: datetime) -> float:
        """Finn lengste sammenhengende hvileperiode i et tidsvindu"""
        if not shifts:
            return 168
        
        times = [window_start]
        for s in shifts:
            if self.vakt_mgr.is_working_shift(s.code):
                info = self.vakt_mgr.get_code_info(s.code)
                if info and info["start"] and info["end"]:
                    start_time = datetime.combine(s.date, datetime.strptime(info["start"], "%H:%M").time())
                    end_time = datetime.combine(s.date, datetime.strptime(info["end"], "%H:%M").time())
                    if info["end"] < info["start"]:
                        end_time += timedelta(days=1)
                    times.extend([start_time, end_time])
        times.append(window_end)
        
        times.sort()
        
        max_rest = 0
        for i in range(0, len(times) - 1, 2):
            gap = (times[i + 1] - times[i]).total_seconds() / 3600
            max_rest = max(max_rest, gap)
        
        return max_rest
    
    def _calculate_stats(self, shifts: list[Shift]) -> dict:
        """Kalkuler turnus-statistikk"""
        by_employee = self._group_by_employee(shifts)
        
        stats = {
            "total_shifts": len(shifts),
            "total_employees": len(by_employee),
            "shifts_per_employee": {},
            "hours_per_employee": {},
            "shift_type_distribution": {},
            "weekend_shifts": 0,
            "night_shifts": 0,
            "average_weekly_hours": {},
            "overtime_hours": {}
        }
        
        for emp_id, emp_shifts in by_employee.items():
            stats["shifts_per_employee"][emp_id] = len(emp_shifts)
            total_hours = sum(
                self.vakt_mgr.get_code_info(s.code)["duration_hours"]
                for s in emp_shifts if self.vakt_mgr.get_code_info(s.code)
            )
            stats["hours_per_employee"][emp_id] = total_hours
            
            # Gjennomsnittlig uketid
            dates = [s.date for s in emp_shifts]
            if dates:
                weeks_span = max((max(dates) - min(dates)).days // 7, 1)
                stats["average_weekly_hours"][emp_id] = round(total_hours / weeks_span, 2)
            
            for s in emp_shifts:
                shift_type = self.vakt_mgr.get_shift_type(s.code)
                stats["shift_type_distribution"][shift_type] = \
                    stats["shift_type_distribution"].get(shift_type, 0) + 1
                
                if s.date.weekday() >= 5:
                    stats["weekend_shifts"] += 1
                if shift_type == "night":
                    stats["night_shifts"] += 1
        
        return stats
    
    def _calculate_risk_score(self, violations: list[Violation], stats: dict) -> dict:
        """Kalkuler samlet risikoscore"""
        severity_weights = {"critical": 10, "warning": 5, "info": 1}
        
        total_weight = sum(severity_weights[v.severity] for v in violations)
        
        # HTA-spesifikk score
        hta_violations = [v for v in violations if v.paragraph and "HTA" in v.paragraph]
        hta_weight = sum(severity_weights[v.severity] for v in hta_violations)
        
        # AML-spesifikk score
        aml_violations = [v for v in violations if v.paragraph and "AML" in v.paragraph]
        aml_weight = sum(severity_weights[v.severity] for v in aml_violations)
        
        num_shifts = max(stats["total_shifts"], 1)
        
        return {
            "raw_score": total_weight,
            "normalized": round((total_weight / num_shifts) * 100, 2),
            "hta_score": round((hta_weight / num_shifts) * 100, 2),
            "aml_score": round((aml_weight / num_shifts) * 100, 2),
            "critical_count": len([v for v in violations if v.severity == "critical"]),
            "warning_count": len([v for v in violations if v.severity == "warning"]),
            "info_count": len([v for v in violations if v.severity == "info"]),
            "hta_violations": len(hta_violations),
            "aml_violations": len(aml_violations),
            "level": "high" if total_weight / num_shifts > 0.5 else "medium" if total_weight / num_shifts > 0.2 else "low"
        }
