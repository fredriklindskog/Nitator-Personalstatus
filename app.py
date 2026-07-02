import streamlit as st
import hashlib
import datetime

# 1. Inställningar för hemsidan (Bred layout för TV-skärm)
st.set_page_config(page_title="Veckostatus Personal", layout="wide")

# 2. Kalkylera datum och vecka
idag = datetime.date.today()
iso_info = idag.isocalendar()
veckonummer = iso_info[1]  # Hämtar det exakta veckonumret

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

if "veckodb" not in st.session_state:
    st.session_state.veckodb = {
        namn: {dag: {"status": "Ledig", "kommentar": ""} for dag in VECKODAGAR} for namn in ANSTALLDA
    }

# --- SEPARATA FLIKAR HÖGST UPP PÅ SIDAN ---
flik_tv, flik_inloggning = st.tabs(["📺 TV-Skärm (Visa schema)", "🔐 Ändra Status (Logga in)"])

# ==========================================
# FLIK 1: TV-SKÄRMEN
# ==========================================
with flik_tv:
    st.title("🏢 Personalens Veckoschema")
    st.subheader(f"🗓️ Vecka {veckonummer} | Dag-för-dag status")
    st.markdown("---")

    # RÄTTAT: Skapa 6 kolumner och lägg till index [0] för första kolumnen
    rubrik_kolumner = st.columns(6)
    rubrik_kolumner[0].markdown("### 👤 Anställd")
    for i, dag_text in enumerate(DAG_MED_DATUM):
        rubrik_kolumner[i+1].markdown(f"### {dag_text}")

    st.markdown("---")

    # Visa rader för anställda
    for namn in ANSTALLDA:
        # RÄTTAT: Skapa 6 kolumner även för personalen och lägg till index [0]
        rad_kolumner = st.columns(6)
        rad_kolumner[0].markdown(f"**{namn}**")
        
        for i, dag in enumerate(VECKODAGAR):
            dag_data = st.session_state.veckodb[namn][dag]
            status_text = STATUS_VAL.get(dag_data["status"], "⚪ Ledig")
            kommentar_text = dag_data["kommentar"]
            
            if kommentar_text.strip():
                rad_kolumner[i+1].markdown(f"{status_text}  \n*💬 {kommentar_text}*")
            else:
                rad_kolumner[i+1].write(status_text)

# ==========================================
# FLIK 2: INLOGGNINGSSIDAN
# ==========================================
with flik_inloggning:
    st.title("🔐 Logga in och ändra status")
    st.write("Välj ditt namn och fyll i ditt personliga lösenord.")
    
    infofalt, indatafalt = st.columns([1, 4]) # Justerad för snyggare bredd på mobilen
    
    with indatafalt:
        valt_namn = st.selectbox("Välj ditt namn i listan:", ANSTALLDA)
        
        aktuell_dag_index = idag.weekday()
        default_dag = [VECKODAGAR[aktuell_dag_index]] if aktuell_dag_index < 5 else [VECKODAGAR[0]]
        valda_dagar = st.multiselect("Vilka dagar vill du ändra?", VECKODAGAR, default=default_dag)
        
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
                        st.session_state.veckodb[valt_namn][dag]["status"] = ny_status
                        st.session_state.veckodb[valt_namn][dag]["kommentar"] = ny_kommentar
                    st.success(f"Klart! Statusen har uppdaterats för {valt_namn}.")
                    st.balloons()
                    st.rerun()
            else:
                st.error("Fel lösenord för den valda personen! Statusen sparades inte.")
