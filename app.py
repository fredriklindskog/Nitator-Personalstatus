import streamlit as st
import hashlib
import datetime
import sqlite3
import os
import time

# 1. Inställningar för hemsidan (Bred layout för TV-skärm)
st.set_page_config(page_title="Veckostatus Personal", layout="wide")

# CSS-kod för tabellens utseende
st.markdown("""
<style>
    .status-tabell {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .status-tabell th {
        text-align: left;
        padding: 10px 8px;
        font-size: 1.1rem;
        border-bottom: 2px solid #ddd;
    }
    .status-tabell td {
        padding: 12px 8px;
        vertical-align: top;
        font-size: 1rem;
    }
    .status-tabell tr:nth-child(even) {
        background-color: #f4f6f7 !important;
    }
    .kommentar-text {
        font-style: italic;
        color: #555;
        font-size: 0.85rem;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# 2. Funktioner för att hantera SQL-databasen
DB_FIL = "status.db"

def initiera_databas():
    conn = sqlite3.connect(DB_FIL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veckostatus (
            namn TEXT,
            dag TEXT,
            status TEXT,
            kommentar TEXT,
            PRIMARY KEY (namn, dag)
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM veckostatus")
    if cursor.fetchone() == 0:
        for namn in ANSTALLDA:
            for dag in VECKODAGAR:
                cursor.execute(
                    "INSERT INTO veckostatus (namn, dag, status, kommentar) VALUES (?, ?, ?, ?)",
                    (namn, dag, "På jobb", "")
                )
        conn.commit()
    conn.close()

def hämta_alla_statusar():
    conn = sqlite3.connect(DB_FIL)
    cursor = conn.cursor()
    cursor.execute("SELECT namn, dag, status, kommentar FROM veckostatus")
    rader = cursor.fetchall()
    conn.close()
    
    data = {namn: {dag: {"status": "På jobb", "kommentar": ""} for dag in VECKODAGAR} for namn in ANSTALLDA}
    for namn, dag, status, kommentar in rader:
        if namn in data and dag in data[namn]:
            data[namn][dag] = {"status": status, "kommentar": kommentar}
    return data

def uppdatera_status_i_db(namn, dag, ny_status, ny_kommentar):
    conn = sqlite3.connect(DB_FIL)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO veckostatus (namn, dag, status, kommentar)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(namn, dag) DO UPDATE SET status=excluded.status, kommentar=excluded.kommentar
    ''', (namn, dag, ny_status, ny_kommentar))
    conn.commit()
    conn.close()

# 3. Kalkylera datum och vecka
idag = datetime.date.today()
veckonummer = idag.isocalendar().week

mandag = idag - datetime.timedelta(days=idag.weekday())
VECKODAGAR = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
DAG_MED_DATUM = [f"{dag} ({ (mandag + datetime.timedelta(days=i)).strftime('%d/%m') })" for i, dag in enumerate(VECKODAGAR)]

# Listan med era ikoner
STATUS_VAL = {
    "På jobb": "🟢 På jobb",
    "Arbetar hemifrån": "🟣 Arbetar hemifrån",
    "Ute": "🟠 Ute",
    "Halvdag": "🟡 Halvdag",
    "Lunch": "🥣 Lunch",
    "VAB": "🔵 VAB",
    "Föräldraledig": "👶 Föräldraledig",
    "Semester": "🌴 Semester",
    "ATF": "⏱️ ATF",
    "Ledig": "⚪ Ledig"
}

# Lista på anställda
ANSTALLDA = [
    "Sophie Noresson Fjellsén",
    "Fredrik Lindskog",
    "Stefan Christensson"
]

initiera_databas()

if "form_id" not in st.session_state:
    st.session_state.form_id = 0
if "sparade_just_nu" not in st.session_state:
    st.session_state.sparade_just_nu = False

# Meny högst upp på sidan
valda_flikar = ["📺 TV-Skärm (Visa schema)", "🔐 Ändra Status"]
val_flik = st.segmented_control(
    "Välj vy:",
    valda_flikar,
    default="📺 TV-Skärm (Visa schema)",
    label_visibility="collapsed"
)

# ==========================================
# VY 1: TV-SKÄRMEN
# ==========================================
if val_flik == "📺 TV-Skärm (Visa schema)":
    st.session_state.sparade_just_nu = True
    
    if os.path.exists("logga.png"):
        st.image("logga.png", width=300)
        
    # NYTT: Texten och tillhörande ikon har gjorts mindre (0.9rem) och mer diskret
    st.markdown(f"<p style='margin:0; font-size:0.9rem; color:#666;'><span style='font-size:1rem;'>🗓️</span> Vecka {veckonummer} | Dag-för-dag status</p>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top:5px; margin-bottom:10px; border:0; border-top:1px solid #ddd;'>", unsafe_allow_html=True)

    aktuell_data = hämta_alla_statusar()

    html_kod = "<table class='status-tabell'>"
    html_kod += "<tr><th>👤 Anställd</th>"
    for dag_text in DAG_MED_DATUM:
        html_kod += f"<th>{dag_text}</th>"
    html_kod += "</tr>"
    
    for namn in ANSTALLDA:
        html_kod += f"<tr><td><strong>{namn}</strong></td>"
        for dag in VECKODAGAR:
            dag_data = aktuell_data[namn][dag]
            status_text = STATUS_VAL.get(dag_data["status"], "🟢 På jobb")
            kommentar_text = dag_data["kommentar"]
            
            html_kod += "<td>"
            html_kod += f"<div>{status_text}</div>"
            if kommentar_text.strip():
                html_kod += f"<div class='kommentar-text'>💬 {kommentar_text}</div>"
            html_kod += "</td>"
        html_kod += "</tr>"
        
    html_kod += "</table>"
    st.markdown(html_kod, unsafe_allow_html=True)

# ==========================================
# VY 2: ÄNDRA STATUS
# ==========================================
else:
    if st.session_state.sparade_just_nu:
        st.session_state.form_id += 1
        st.session_state.sparade_just_nu = False

    if os.path.exists("logga.png"):
        st.image("logga.png", width=300)
        
    st.subheader("🔐 Logga in och ändra status")
    st.write("Välj ditt namn och bocka i vilka dagar du vill uppdatera.")
    
    kol_vänster, kol_mitten, kol_höger = st.columns(3)
    
    with kol_mitten:
        valt_namn = st.selectbox(
            "Välj ditt namn i listan:", 
            ANSTALLDA, 
            index=None, 
            placeholder="Välj ditt namn...",
            key=f"namn_box_{st.session_state.form_id}"
        )
        
        aktuell_dag_index = idag.weekday()
        if aktuell_dag_index > 4:
            aktuell_dag_index = 0
            
        valda_dagar = st.multiselect("Vilka dagar vill du ändra?", VECKODAGAR, default=[VECKODAGAR[aktuell_dag_index]])
        
        ny_status = st.radio("Välj din status för dessa dagar:", list(STATUS_VAL.keys()), horizontal=True)
        ny_kommentar = st.text_input("Lägg till en kommentar (frivilligt):", max_chars=40, placeholder="t.ex. Svarar i mobilen, Teams-möte")
        
        if st.button("Spara och uppdatera schema", type="primary"):
            if valt_namn is None:
                st.error("⚠️ Du måste välja ditt namn i listan innan du kan spara!")
            elif not valda_dagar:
                st.error("⚠️ Du måste välja minst en dag!")
            else:
                for dag in valda_dagar:
                    uppdatera_status_i_db(valt_namn, dag, ny_status, ny_kommentar)
                
                st.success(f"✅ Ändringarna sparades permanent för {valt_namn}!")
                
                st.session_state.form_id += 1
                st.session_state.sparade_just_nu = True
                
                time.sleep(2.0)
                st.rerun()
