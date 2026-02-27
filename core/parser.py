"""
Parser for Norwegian shift data exports (Excel/GAT)
Håndterer merged cells, norske tegn, ulike kolonnenavn
"""
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import polars as pl

class GatParser:
    """Parser for GAT/Excel turnus-eksport"""
    
    # Standard kolonnenavn-variasjoner
    DATE_COLUMNS = [
        "dato", "date", "dag", "day", "arbeidsdato", "vaktdato",
        "Dato", "Date", "Dag", "Day"
    ]
    
    EMPLOYEE_COLUMNS = [
        "ansatt", "ansatt_id", "ansattnr", "pers.nr", "personnr",
        "employee", "emp_id", "ansatt_id", "id", "initialer", "navn",
        "Ansatt", "AnsattID", "PersNr", "PersonNr", "Name"
    ]
    
    SHIFT_COLUMNS = [
        "vakt", "vaktkode", "skift", "turnus", "vakttype",
        "shift", "code", "duty", "vakt_type",
        "Vakt", "Vaktkode", "Skift", "Turnus"
    ]
    
    DEPARTMENT_COLUMNS = [
        "avdeling", "dept", "department", "enhet", "sted",
        "Avdeling", "Department", "Enhet"
    ]
    
    # Mønstre for "human noise" som må renses
    NOISE_PATTERNS = [
        r"syk.*", r"perm.*", r"ferie.*", r"kurs.*", r"utdanning.*",
        r"møte.*", r"admin.*", r"kontor.*", r"ring.*",
        r"SYK.*", r"PERM.*", r"FERIE.*"
    ]
    
    def __init__(self):
        self.mapping = {}
        self.noise_rows = []
    
    def parse_file(self, filepath: Path, sheet_name: Optional[str] = None) -> pl.DataFrame:
        """
        Parse Excel eller CSV fil
        
        Args:
            filepath: Path til filen
            sheet_name: Navn på sheet (for Excel med flere sheets)
        
        Returns:
            Polars DataFrame med standardiserte kolonner
        """
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.csv':
            df = pl.read_csv(filepath, encoding='utf-8')
        else:
            df = pl.read_excel(filepath, sheet_name=sheet_name)
        
        return self.parse_dataframe(df)
    
    def parse_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Parse en eksisterende dataframe
        
        Håndterer:
        - Fuzzy kolonnenavn-matching
        - Merged cells (forward-fill)
        - Norske tegn
        - Dato-parsing
        """
        # Finn og standardiser kolonner
        df = self._standardize_columns(df)
        
        # Håndter merged cells (forward fill for ansatt/avdeling)
        df = self._handle_merged_cells(df)
        
        # Rens vaktkoder
        df = self._clean_shift_codes(df)
        
        # Parse datoer
        df = self._parse_dates(df)
        
        # Filtrer ut støy-rader
        df = self._filter_noise(df)
        
        return df
    
    def _standardize_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Finn og standardiser kolonnenavn"""
        col_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower().strip()
            
            # Sjekk dato-kolonner
            if any(dc.lower() in col_lower for dc in self.DATE_COLUMNS):
                col_mapping[col] = "dato"
            # Sjekk ansatt-kolonner
            elif any(ec.lower() in col_lower for ec in self.EMPLOYEE_COLUMNS):
                col_mapping[col] = "ansatt_id"
            # Sjekk vakt-kolonner
            elif any(sc.lower() in col_lower for sc in self.SHIFT_COLUMNS):
                col_mapping[col] = "vakt"
            # Sjekk avdeling-kolonner
            elif any(dc.lower() in col_lower for dc in self.DEPARTMENT_COLUMNS):
                col_mapping[col] = "avdeling"
        
        # Rename kolonner
        if col_mapping:
            df = df.rename(col_mapping)
        
        # Sjekk at vi har minimum påkrevde kolonner
        required = ["dato", "vakt"]
        missing = [r for r in required if r not in df.columns]
        if missing:
            raise ValueError(f"Mangler påkrevde kolonner: {missing}. Fant: {df.columns}")
        
        # Hvis ansatt_id mangler, prøv å finn en passende kolonne
        if "ansatt_id" not in df.columns:
            # Bruk første tekst-kolonne som ansatt_id
            for col in df.columns:
                if df[col].dtype == pl.Utf8 and col not in ["dato", "vakt", "avdeling"]:
                    df = df.with_columns(pl.col(col).alias("ansatt_id"))
                    break
            else:
                # Lag en dummy ansatt_id
                df = df.with_columns(pl.lit("UNKNOWN").alias("ansatt_id"))
        
        return df
    
    def _handle_merged_cells(self, df: pl.DataFrame) -> pl.DataFrame:
        """Håndter merged cells med forward fill"""
        # Forward fill for ansatt_id og avdeling
        for col in ["ansatt_id", "avdeling"]:
            if col in df.columns:
                df = df.with_columns(
                    pl.col(col).forward_fill()
                )
        
        return df
    
    def _clean_shift_codes(self, df: pl.DataFrame) -> pl.DataFrame:
        """Rens vaktkoder for whitespace og normaliser"""
        if "vakt" not in df.columns:
            return df
        
        df = df.with_columns(
            pl.col("vakt")
            .str.strip_chars()
            .str.to_uppercase()
            .alias("vakt")
        )
        
        return df
    
    def _parse_dates(self, df: pl.DataFrame) -> pl.DataFrame:
        """Parse dato-kolonne til datetime"""
        if "dato" not in df.columns:
            return df
        
        # Prøv ulike dato-formater
        date_formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y%m%d",
            "%d.%m.%y",
        ]
        
        # Sjekk om allerede datetime/date
        if df["dato"].dtype in [pl.Date, pl.Datetime]:
            return df
        
        # Prøv å parse som string
        parsed = None
        for fmt in date_formats:
            try:
                parsed = df.with_columns(
                    pl.col("dato").str.to_datetime(fmt, strict=False).alias("dato_parsed")
                )
                # Sjekk om vi fikk noen gyldige datoer
                if parsed["dato_parsed"].null_count() < len(parsed):
                    break
            except:
                continue
        
        if parsed is not None and "dato_parsed" in parsed.columns:
            df = parsed.with_columns(
                pl.col("dato_parsed").alias("dato")
            ).drop("dato_parsed")
        
        return df
    
    def _filter_noise(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filtrer ut rader med 'human noise'"""
        if "vakt" not in df.columns:
            return df
        
        self.noise_rows = []
        
        # Finn rader med støy
        for pattern in self.NOISE_PATTERNS:
            mask = df["vakt"].str.contains(pattern)
            noise = df.filter(mask)
            if len(noise) > 0:
                self.noise_rows.extend(noise.to_dicts())
        
        # Filtrer ut støy (men behold rader som matcher vaktkoder)
        # Dette er en placeholder - i praksis vil vi beholde alt
        # og markere mistenkelige rader for manuell gjennomgang
        
        return df
    
    def get_parsing_report(self) -> dict:
        """Generer rapport om parsing"""
        return {
            "kolonner_mappet": self.mapping,
            "antall_støy_rader": len(self.noise_rows),
            "støy_eksempler": self.noise_rows[:5] if self.noise_rows else []
        }


class WideFormatParser:
    """
    Parser for 'wide format' turnus (en rad per ansatt, en kolonne per dag)
    Vanlig i norske turnusplaner
    """
    
    def __init__(self):
        self.date_columns = []
    
    def parse(self, df: pl.DataFrame, employee_col: str = "ansatt") -> pl.DataFrame:
        """
        Konverter wide format til long format
        
        Input:  ansatt | 01.01 | 02.01 | 03.01 | ...
        Output: ansatt_id | dato | vakt
        """
        # Identifiser dato-kolonner
        date_cols = []
        for col in df.columns:
            if col == employee_col:
                continue
            # Prøv å parse som dato
            try:
                # Sjekk om kolonnenavn ser ut som dato
                if self._looks_like_date(col):
                    date_cols.append(col)
            except:
                pass
        
        if not date_cols:
            raise ValueError(f"Fant ingen dato-kolonner. Kolonner: {df.columns}")
        
        # Melt til long format
        df_long = df.melt(
            id_vars=[employee_col],
            value_vars=date_cols,
            variable_name="dato_str",
            value_name="vakt"
        )
        
        # Parse datoer fra kolonnenavn
        df_long = df_long.with_columns(
            pl.col("dato_str").map_elements(self._parse_date_from_header, return_dtype=pl.Date).alias("dato")
        )
        
        # Rens og standardiser
        df_long = df_long.rename({employee_col: "ansatt_id"})
        df_long = df_long.with_columns(
            pl.col("vakt").str.strip_chars().str.to_uppercase()
        )
        
        # Fjern null-rader
        df_long = df_long.filter(pl.col("vakt").is_not_null())
        
        return df_long.select(["ansatt_id", "dato", "vakt"])
    
    def _looks_like_date(self, s: str) -> bool:
        """Sjekk om streng ser ut som dato"""
        date_patterns = [
            r"\d{2}\.\d{2}",  # 01.01
            r"\d{2}/\d{2}",   # 01/01
            r"\d{4}-\d{2}-\d{2}",  # 2024-01-01
            r"\d{2}-\d{2}",   # 01-01
        ]
        return any(re.match(p, s) for p in date_patterns)
    
    def _parse_date_from_header(self, s: str) -> Optional[datetime]:
        """Parse dato fra kolonne-header"""
        # Prøv ulike formater
        formats = ["%d.%m", "%d/%m", "%d-%m", "%Y-%m-%d"]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt)
                # Hvis ikke år spesifisert, anta inneværende år
                if dt.year == 1900:
                    dt = dt.replace(year=datetime.now().year)
                return dt.date()
            except:
                continue
        
        return None


def auto_detect_format(df: pl.DataFrame) -> str:
    """Auto-detekter format (long vs wide)"""
    # Hvis vi har kolonner som ser ut som datoer, anta wide format
    wide_parser = WideFormatParser()
    date_like_cols = sum(1 for col in df.columns if wide_parser._looks_like_date(col))
    
    if date_like_cols >= 3:  # 3 eller flere dato-kolonner = wide format
        return "wide"
    else:
        return "long"
