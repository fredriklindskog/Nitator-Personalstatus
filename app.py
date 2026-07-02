import streamlit as st
import hashlib
import datetime
import sqlite3
import os

# 1. Inställningar för hemsidan (Bred layout för TV-skärm)
st.set_page_config(page_title="Veckostatus Personal", layout="wide")

# NYTT & RÄTTAT: Träffsäker CSS som skuggar varannan rad perfekt inuti Streamlits egna block
st.html("""
<style>
    /* Hitta alla personrader och ge dem lite luft */
    [data-testid="stVerticalBlockBorderWithTitle"] {
        padding: 6px 12px !important;
        margin: 2px 0px !important;
        border-radius: 6px !important;
    }
    /* Färga bakgrunden till ljusgrå på varannan rad */
    [data-testid="stVerticalBlockBorderWithTitle"]:nth-of-type(even) {
        background-color: #f4f6f7 !important;
    }
</style>
""")

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
iso_info = idag.isocalendar()[1]
veckonummer = iso_info

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
        
    st.markdown(f"<h4 style='margin:0; font-weight:normal;'>🗓️ Vecka {veckonummer} | Dag-för-dag status</h4>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top:5px; margin-bottom:10px; border:0; border-top:1px solid #ddd;'>", unsafe_allow_html=True)

    aktuell_data = hämta_alla_statusar()

    # Rubrikrad
    rubrik_kolumner = st.columns(6)
    with rubrik_kolumner[0]:
        st.markdown("<h4 style='margin:0;'>👤 Anställd</h4>", unsafe_allow_html=True)
    for i, dag_text in enumerate(DAG_MED_DATUM):
        with rubrik_kolumner[i+1]:
            st.markdown(f"<h4 style='margin:0;'>{dag_text}</h4>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top:10px; margin-bottom:15px; border:0; border-top:1px solid #ddd;'>", unsafe_allow_html=True)

    # Raderna för personalen (Nu helt rena från trasig HTML-kod)
    for namn in ANSTALLDA:
        with st.container():
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
        st.image("logga.png", width=300)
        
    st.subheader("🔐 Logga in och ändra status")
    st.write("Välj ditt namn och fyll i ditt personliga lösenord.")
    
    kol_vänster, kol_mitten, kol_höger = st.columns(3)
    
    with kol_mitten:
        valt_namn = st.selectbox("Välj ditt namn i listan:", ANSTALLDA)
        
        aktuell_dag_index = idag.weekday() if idag.weekday() < 5 else 0
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
