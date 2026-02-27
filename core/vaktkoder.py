"""
Vaktkode-håndtering for Turnus
Støtter flere institusjoner og tilpassbare koder
"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import polars as pl

class VaktKodeManager:
    """Håndterer vaktkoder for ulike institusjoner"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "vaktkoder.json"
        self._config = None
        self._current_institution = "default"
        self._load_config()
    
    def _load_config(self):
        """Last inn vaktkode-konfigurasjon"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
    
    def save_config(self):
        """Lagre endringer til config"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def list_institutions(self) -> list[str]:
        """List alle tilgjengelige institusjoner"""
        return list(self._config["institutions"].keys())
    
    def get_institution_name(self, institution_id: str) -> str:
        """Hent navn på institusjon"""
        return self._config["institutions"][institution_id]["name"]
    
    def set_institution(self, institution_id: str):
        """Sett aktiv institusjon"""
        if institution_id not in self._config["institutions"]:
            raise ValueError(f"Ukjent institusjon: {institution_id}")
        self._current_institution = institution_id
    
    def get_codes(self, institution_id: Optional[str] = None) -> dict:
        """Hent alle vaktkoder for en institusjon"""
        inst = institution_id or self._current_institution
        return self._config["institutions"][inst]["codes"]
    
    def get_code_info(self, code: str, institution_id: Optional[str] = None) -> Optional[dict]:
        """Hent informasjon om en spesifikk vaktkode"""
        codes = self.get_codes(institution_id)
        return codes.get(code)
    
    def add_code(self, code: str, name: str, start: Optional[str], end: Optional[str], 
                 duration: float, type_: str, institution_id: Optional[str] = None):
        """Legg til ny vaktkode"""
        inst = institution_id or self._current_institution
        self._config["institutions"][inst]["codes"][code] = {
            "name": name,
            "start": start,
            "end": end,
            "duration_hours": duration,
            "type": type_
        }
        self.save_config()
    
    def remove_code(self, code: str, institution_id: Optional[str] = None):
        """Fjern en vaktkode"""
        inst = institution_id or self._current_institution
        if code in self._config["institutions"][inst]["codes"]:
            del self._config["institutions"][inst]["codes"][code]
            self.save_config()
    
    def get_rules(self) -> dict:
        """Hent compliance-regler"""
        return self._config["rules"]
    
    def is_working_shift(self, code: str, institution_id: Optional[str] = None) -> bool:
        """Sjekk om koden er en arbeidsvakt (ikke fri/syk/perm)"""
        info = self.get_code_info(code, institution_id)
        if not info:
            return False
        return info["type"] not in ["off", "sick", "leave", "training"]
    
    def get_shift_type(self, code: str, institution_id: Optional[str] = None) -> Optional[str]:
        """Hent vakttype (day/evening/night/weekend/off)"""
        info = self.get_code_info(code, institution_id)
        return info["type"] if info else None
    
    def calculate_rest_hours(self, code1: str, code2: str, date1: datetime, date2: datetime,
                            institution_id: Optional[str] = None) -> float:
        """Kalkuler timer mellom to vakter (hviletid)"""
        info1 = self.get_code_info(code1, institution_id)
        info2 = self.get_code_info(code2, institution_id)
        
        if not info1 or not info2:
            return float('inf')  # Ukjent kode = anta nok hvile
        
        # Hvis en av vaktene er fri, er hviletid uendelig
        if not self.is_working_shift(code1, institution_id) or not self.is_working_shift(code2, institution_id):
            return float('inf')
        
        # Parse tider
        end1 = datetime.strptime(info1["end"], "%H:%M").time()
        start2 = datetime.strptime(info2["start"], "%H:%M").time()
        
        # Slutt første vakt
        end_datetime = datetime.combine(date1, end1)
        if info1["end"] < info1["start"]:  # Nattvakt
            end_datetime += timedelta(days=1)
        
        # Start andre vakt
        start_datetime = datetime.combine(date2, start2)
        
        # Kalkuler differanse
        diff = start_datetime - end_datetime
        return diff.total_seconds() / 3600


def detect_institution_from_data(df: pl.DataFrame) -> Optional[str]:
    """Prøv å gjette institusjon basert på vaktkoder i data"""
    manager = VaktKodeManager()
    
    # Finn unike koder i datasettet
    unique_codes = set()
    for col in df.columns:
        if df[col].dtype == pl.Utf8:
            unique_codes.update(df[col].drop_nulls().unique().to_list())
    
    # Sjekk hvilken institusjon som matcher best
    best_match = None
    best_score = 0
    
    for inst_id in manager.list_institutions():
        inst_codes = set(manager.get_codes(inst_id).keys())
        overlap = len(unique_codes & inst_codes)
        if overlap > best_score:
            best_score = overlap
            best_match = inst_id
    
    return best_match
