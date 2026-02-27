"""
Hoved-UI for Turnus
"""
import streamlit as st
import polars as pl
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Legg til core i path
sys.path.insert(0, str(Path(__file__).parent))

from core.vaktkoder import VaktKodeManager, detect_institution_from_data
from core.simulator import TurnusSimulator, Shift
from core.analyzer import HistoricalAnalyzer
from core.parser import GatParser, WideFormatParser, auto_detect_format

st.set_page_config(page_title="Turnus", page_icon="🏥", layout="wide")

# --- Sidebar ---
st.sidebar.title("🏥 Turnus")
st.sidebar.markdown("*Turnusplanlegging & Analyse*")

page = st.sidebar.radio("Navigasjon", [
    "📊 Dashboard",
    "🔮 Simulator", 
    "📈 Historisk Analyse",
    "⚙️ Vaktkoder"
])

# --- Hjelpefunksjoner ---
def load_data(uploaded_file):
    """Last inn data fra Excel/CSV med auto-parsing"""
    # Les rådata
    if uploaded_file.name.endswith('.csv'):
        df = pl.read_csv(uploaded_file)
    else:
        df = pl.read_excel(uploaded_file)
    
    # Auto-detekter format og parse
    format_type = auto_detect_format(df)
    
    if format_type == "wide":
        # Finn ansatt-kolonnen
        emp_col = None
        for col in df.columns:
            if any(x in col.lower() for x in ["ansatt", "navn", "employee", "name"]):
                emp_col = col
                break
        if not emp_col:
            emp_col = df.columns[0]  # Bruk første kolonne
        
        parser = WideFormatParser()
        df = parser.parse(df, employee_col=emp_col)
    else:
        # Long format - bruk GAT-parser
        parser = GatParser()
        df = parser.parse_dataframe(df)
    
    return df

def parse_shift_data(df: pl.DataFrame, date_col: str, code_col: str, emp_col: str) -> list[Shift]:
    """Parse dataframe til Shift-objekter"""
    shifts = []
    for row in df.iter_rows(named=True):
        date_val = row[date_col]
        if isinstance(date_val, str):
            date_val = datetime.strptime(date_val, "%Y-%m-%d")
        shifts.append(Shift(
            date=date_val,
            code=row[code_col],
            employee_id=str(row[emp_col])
        ))
    return shifts

# --- Dashboard ---
if page == "📊 Dashboard":
    st.title("📊 Turnus Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Ansatte", "—", help="Last opp data for å se statistikk")
    with col2:
        st.metric("Vakter", "—")
    with col3:
        st.metric("Risikoscore", "—")
    
    st.info("👈 Velg **Simulator** for å teste scenarier, eller **Historisk Analyse** for å analysere eksisterende data.")

# --- Simulator ---
elif page == "🔮 Simulator":
    st.title("🔮 Turnus Simulator")
    
    st.markdown("Test turnusplaner før de settes i produksjon. Sjekk compliance med AML og HTA.")
    
    # Institusjonsvalg
    vakt_mgr = VaktKodeManager()
    institution = st.selectbox(
        "Institusjon",
        options=vakt_mgr.list_institutions(),
        format_func=lambda x: f"{vakt_mgr.get_institution_name(x)} ({x})"
    )
    
    # Input-metode
    input_method = st.radio("Input-metode", ["Last opp fil", "Manuell inntasting"])
    
    if input_method == "Last opp fil":
        uploaded = st.file_uploader("Last opp Excel/CSV", type=["xlsx", "csv"])
        
        if uploaded:
            with st.spinner("Parser fil..."):
                df = load_data(uploaded)
            
            # Vis parsing-info
            st.info(f"📄 Rader: {len(df)} | Kolonner: {list(df.columns)}")
            
            st.write("Forhåndsvisning:", df.head())
            
            # Kolonne-mapping (hvis ikke allerede standardisert)
            cols = df.columns
            date_col = st.selectbox("Datokolonne", cols, index=cols.index("dato") if "dato" in cols else 0)
            code_col = st.selectbox("Vaktkode-kolonne", cols, index=cols.index("vakt") if "vakt" in cols else 0)
            emp_col = st.selectbox("Ansatt-ID kolonne", cols, index=cols.index("ansatt_id") if "ansatt_id" in cols else 0)
            
            if st.button("Kjør simulering"):
                with st.spinner("Analyserer..."):
                    shifts = parse_shift_data(df, date_col, code_col, emp_col)
                    simulator = TurnusSimulator(institution)
                    result = simulator.simulate_schedule(shifts)
                    
                    st.session_state['last_result'] = result
                    st.success("Simulering fullført!")
    
    else:  # Manuell inntasting
        st.markdown("### Manuell inntasting")
        
        num_employees = st.number_input("Antall ansatte", 1, 50, 3)
        num_days = st.number_input("Antall dager", 1, 90, 14)
        start_date = st.date_input("Startdato", datetime.now())
        
        codes = list(vakt_mgr.get_codes(institution).keys())
        
        st.markdown("#### Vaktplan")
        shifts = []
        
        for emp_idx in range(num_employees):
            emp_id = f"Ansatt_{emp_idx + 1}"
            st.markdown(f"**{emp_id}**")
            
            cols = st.columns(min(num_days, 7))
            for day in range(num_days):
                col = cols[day % 7]
                date = datetime.combine(start_date + timedelta(days=day), datetime.min.time())
                with col:
                    code = st.selectbox(
                        f"{date.strftime('%a %d')}",
                        options=codes,
                        key=f"{emp_id}_{day}"
                    )
                    if vakt_mgr.is_working_shift(code, institution):
                        shifts.append(Shift(date=date, code=code, employee_id=emp_id))
        
        if st.button("Kjør simulering"):
            with st.spinner("Analyserer..."):
                simulator = TurnusSimulator(institution)
                result = simulator.simulate_schedule(shifts)
                
                st.session_state['last_result'] = result
                st.success("Simulering fullført!")
    
    # Vis resultater
    if 'last_result' in st.session_state:
        result = st.session_state['last_result']
        
        st.markdown("---")
        st.markdown("## Resultater")
        
        # Risikoscore
        risk = result['risk_score']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            color = "🟢" if risk['level'] == 'low' else "🟡" if risk['level'] == 'medium' else "🔴"
            st.metric(f"{color} Risikonivå", risk['level'].upper())
        with col2:
            st.metric("Kritiske brudd", risk['critical_count'])
        with col3:
            st.metric("Advarsler", risk['warning_count'])
        with col4:
            st.metric("Info", risk['info_count'])
        
        # Compliance status
        if result['compliant']:
            st.success("✅ Ingen kritiske regelbrudd funnet!")
        else:
            st.error(f"❌ {risk['critical_count']} kritiske regelbrudd må rettes")
        
        # Violations
        if result['violations']:
            st.markdown("### Regelbrudd")
            
            for v in result['violations']:
                severity_icon = "🔴" if v.severity == 'critical' else "🟡" if v.severity == 'warning' else "🔵"
                with st.expander(f"{severity_icon} {v.type}: {v.description}"):
                    st.write(f"**Paragraf:** {v.paragraph or 'N/A'}")
                    if v.shift1:
                        st.write(f"**Vakt 1:** {v.shift1.employee_id} - {v.shift1.date.strftime('%Y-%m-%d')} ({v.shift1.code})")
                    if v.shift2:
                        st.write(f"**Vakt 2:** {v.shift2.employee_id} - {v.shift2.date.strftime('%Y-%m-%d')} ({v.shift2.code})")
        
        # Statistikk
        stats = result['stats']
        st.markdown("### Statistikk")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totalt vakter", stats['total_shifts'])
        with col2:
            st.metric("Ansatte", stats['total_employees'])
        with col3:
            st.metric("Nattevakter", stats['night_shifts'])

# --- Historisk Analyse ---
elif page == "📈 Historisk Analyse":
    st.title("📈 Historisk Analyse")
    
    st.markdown("Analyser tidligere turnusdata for belastningsmønstre og trender.")
    
    uploaded = st.file_uploader("Last opp historiske data (Excel/CSV)", type=["xlsx", "csv"])
    
    if uploaded:
        with st.spinner("Parser fil..."):
            df = load_data(uploaded)
        
        st.info(f"📄 Rader: {len(df)} | Kolonner: {list(df.columns)}")
        st.write("Forhåndsvisning:", df.head())
        
        # Auto-detect institusjon
        detected = detect_institution_from_data(df)
        if detected:
            st.info(f"🔍 Detektert institusjon: **{vakt_mgr.get_institution_name(detected)}**")
        
        # Kolonne-mapping
        cols = df.columns
        date_col = st.selectbox("Datokolonne", cols, key="hist_date", index=cols.index("dato") if "dato" in cols else 0)
        code_col = st.selectbox("Vaktkode-kolonne", cols, key="hist_code", index=cols.index("vakt") if "vakt" in cols else 0)
        emp_col = st.selectbox("Ansatt-ID kolonne", cols, key="hist_emp", index=cols.index("ansatt_id") if "ansatt_id" in cols else 0)
        
        institution = st.selectbox(
            "Velg institusjon",
            options=vakt_mgr.list_institutions(),
            index=vakt_mgr.list_institutions().index(detected) if detected else 0,
            format_func=lambda x: f"{vakt_mgr.get_institution_name(x)} ({x})"
        )
        
        if st.button("Kjør analyse"):
            with st.spinner("Analyserer historiske data..."):
                analyzer = HistoricalAnalyzer(institution)
                result = analyzer.analyze_dataframe(df, date_col, code_col, emp_col)
                
                st.session_state['hist_result'] = result
                st.success("Analyse fullført!")
    
    if 'hist_result' in st.session_state:
        result = st.session_state['hist_result']
        
        st.markdown("---")
        st.markdown("## Analyseresultater")
        
        # Oppsummering
        summary = result['summary']
        
        health_color = "🟢" if summary['overall_health'] == 'good' else "🟡" if summary['overall_health'] == 'moderate' else "🔴"
        st.header(f"{health_color} Helsetilstand: {summary['overall_health'].upper()}")
        
        # Hovedproblemer
        if summary['main_concerns']:
            st.markdown("### ⚠️ Hovedproblemer")
            for concern in summary['main_concerns']:
                st.write(f"- {concern}")
        
        # Positive funn
        if summary['positive_findings']:
            st.markdown("### ✅ Positive funn")
            for positive in summary['positive_findings']:
                st.write(f"- {positive}")
        
        # Anbefalinger
        if summary['recommendations']:
            st.markdown("### 💡 Anbefalinger")
            for rec in summary['recommendations']:
                st.write(f"- {rec}")
        
        # Detaljerte analyser
        st.markdown("---")
        
        hist = result['historical']
        
        # Belastningsfordeling
        if 'workload_distribution' in hist:
            st.markdown("### Arbeidsbelastning")
            wd = hist['workload_distribution']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gj.snitt timer", wd.get('average_hours', 0))
            with col2:
                st.metric("Min timer", wd.get('min_hours', 0))
            with col3:
                st.metric("Max timer", wd.get('max_hours', 0))
            with col4:
                st.metric("Rettferdighet", f"{wd.get('equity_score', 0)}%")
        
        # Helgefordeling
        if 'weekend_equity' in hist:
            st.markdown("### Helgefordeling")
            we = hist['weekend_equity']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gj.snitt helger", we.get('average_weekends', 0))
            with col2:
                st.metric("Rettferdighet", f"{we.get('equity_score', 0)}%")
            with col3:
                st.metric("Flest helger", we.get('most_weekends', 'N/A'))
        
        # Nattefordeling
        if 'night_equity' in hist:
            st.markdown("### Nattefordeling")
            ne = hist['night_equity']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gj.snitt netter", ne.get('average_nights', 0))
            with col2:
                st.metric("Rettferdighet", f"{ne.get('equity_score', 0)}%")
            with col3:
                st.metric("Flest netter", ne.get('most_nights', 'N/A'))

# --- Vaktkoder ---
elif page == "⚙️ Vaktkoder":
    st.title("⚙️ Vaktkode-konfigurasjon")
    
    vakt_mgr = VaktKodeManager()
    
    # Vis eksisterende institusjoner
    st.markdown("### Institusjoner")
    
    for inst_id in vakt_mgr.list_institutions():
        with st.expander(f"{vakt_mgr.get_institution_name(inst_id)} ({inst_id})"):
            codes = vakt_mgr.get_codes(inst_id)
            
            data = []
            for code, info in codes.items():
                data.append({
                    "Kode": code,
                    "Navn": info['name'],
                    "Start": info['start'] or "—",
                    "Slutt": info['end'] or "—",
                    "Timer": info['duration_hours'],
                    "Type": info['type']
                })
            
            st.dataframe(data, use_container_width=True)
    
    # Legg til ny institusjon
    st.markdown("---")
    st.markdown("### Legg til ny institusjon")
    
    with st.form("new_institution"):
        new_id = st.text_input("Institusjons-ID (kun bokstaver/tall/underscore)")
        new_name = st.text_input("Institusjonsnavn")
        
        st.markdown("#### Vaktkoder (JSON-format)")
        default_codes = '''{
  "D": {"name": "Dag", "start": "07:00", "end": "15:00", "duration_hours": 8, "type": "day"},
  "N": {"name": "Natt", "start": "23:00", "end": "07:00", "duration_hours": 8, "type": "night"},
  "F": {"name": "Fri", "start": null, "end": null, "duration_hours": 0, "type": "off"}
}'''
        codes_json = st.text_area("Vaktkoder", value=default_codes, height=200)
        
        submitted = st.form_submit_button("Lagre institusjon")
        
        if submitted:
            try:
                import json
                codes = json.loads(codes_json)
                
                # Legg til i config
                vakt_mgr._config["institutions"][new_id] = {
                    "name": new_name,
                    "codes": codes
                }
                vakt_mgr.save_config()
                
                st.success(f"Institusjon '{new_name}' lagret!")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Ugyldig JSON: {e}")
