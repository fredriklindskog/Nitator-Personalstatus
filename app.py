import streamlit as st
import hashlib
import datetime
import sqlite3
import os

# 1. Inställningar för hemsidan (Bred layout för TV-skärm)
st.set_page_config(page_title="Veckostatus Personal", layout="wide")

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
    if cursor.fetchone()[0] == 0:
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
iso_info = idag.isocalendar()
veckonummer = iso_info[1]

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
    "Semester": "🛫 Semester",
    "ATF": "⏱️ ATF",
    "Ledig": "⚪ Ledig"
}

def kryptera_losenord(losenord):
    return hashlib.sha256(str.encode(losenord)).hexdigest()

# Personliga lösenord för varje användare
ANSTALLDA_MED_LOSENORD = {
    "Sophie Noresson Fjellsén": kryptera_losenord("Sophie2026"),
    "Fredrik Lindskog": kryptera_losenord("Fredrik2026"),
    "Stefan Christensson": kryptera_losenord("Stefan2026")
}

# Skapa en ren lista med bara namnen för rullistan
ANSTALLDA = list(ANSTALLDA_MED_LOSENORD.keys())

# Starta databasen
initiera_databas()

# --- SEPARATA FLIKAR HÖGST UPP PÅ SIDAN ---
flik_tv, flik_inloggning = st.tabs(["📺 TV-Skärm (Visa schema)", "🔐 Ändra Status (Logga in)"])

# ==========================================
# FLIK 1: TV-SKÄRMEN
# ==========================================
with flik_tv:
    if os.path.exists("logga.png"):
        st.image("logga.png", width=300)
        
    st.title("🏢 Personalens Veckoschema")
    st.subheader(f"🗓️ Vecka {veckonummer} | Dag-för-dag status")
    st.markdown("---")

    aktuell_data = hämta_alla_statusar()

    # RÄTTAT: Lagt till index [0] för den första rubrikkolumnen
    rubrik_kolumner = st.columns(6)
    with rubrik_kolumner[0]:
        st.markdown("### 👤 Anställd")
    for i, dag_text in enumerate(DAG_MED_DATUM):
        with rubrik_kolumner[i+1]:
            st.markdown(f"### {dag_text}")

    st.markdown("---")

    for namn in ANSTALLDA:
        # RÄTTAT: Lagt till index [0] för personalens första kolumn
        rad_kolumner = st.columns(6)
        with rad_kolumner[0]:
            st.markdown(f"**{namn}**")
        
        for i, dag in enumerate(VECKODAGAR):
            dag_data = aktuell_data[namn][dag]
            status_text = STATUS_VAL.get(dag_data["status"], "🟢 På jobb")
            kommentar_text = dag_data["kommentar"]
            
            with rad_kolumner[i+1]:
                if kommentar_text.strip():
                    st.markdown(f"{status_text}  \n*💬 {kommentar_text}*")
                else:
                    st.write(status_text)

# ==========================================
# FLIK 2: INLOGGNINGSSIDAN
# ==========================================
with flik_inloggning:
    if os.path.exists("logga.png"):
        st.image("logga.png", width=150)
        
    st.title("🔐 Logga in och ändra status")
    st.write("Välj ditt namn och fyll i ditt personliga lösenord.")
    
    kol_vänster, kol_mitten, kol_höger = st.columns([1, 2, 1])
    
    with kol_mitten:
        valt_namn = st.selectbox("Välj ditt namn i listan:", ANSTALLDA)
        
        aktuell_dag_index = idg_idx if (idg_idx := idag.weekday()) < 5 else 0
        valda_dagar = st.multiselect("Vilka dagar vill du ändra?", VECKODAGAR, default=[VECKODAGAR[aktuell_dag_index]])
        
        ny_status = st.radio("Välj din status för dessa dagar:", list(STATUS_VAL.keys()), horizontal=True)
        ny_kommentar = st.text_input("Lägg till en kommentar (frivilligt):", max_chars=40, placeholder="t.ex. Svarar i mobilen, Teams-möte")
        
        losenord_input = st.text_input("Ange ditt personliga lösenord:", type="password")
        
        if st.button("Spara och uppdatera schema", type="primary"):
            ratt_hash = ANSTALLDA_MED_LOSENORD[valt_namn]
            
            if kryptera_losenord(losenord_input) == ratt_hash:
                if not valda_dagar:
                    st.error("Du måste välja minst en dag!")
                else:
                    for dag in valda_dagar:
                        uppdatera_status_i_db(valt_namn, dag, ny_status, ny_kommentar)
                    
                    st.toast(f"✅ Ändringarna sparades i databasen för {valt_namn}!", icon="🎉")
                    st.success(f"Klart! Statusen har sparats permanent i databasen.")
                    st.balloons()
                    st.rerun()
            else:
                st.error("Fel lösenord för den valda personen! Statusen sparades inte.")
