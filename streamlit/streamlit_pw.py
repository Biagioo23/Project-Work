import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import altair as alt
# -------------------- LOGIN --------------------

# Dizionario utenti
users = {
    "admin": "1234",
    "jacopo": "biagio"
}

# Inizializza lo stato se non esiste
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# Se l'utente NON è loggato, mostra il form di login
if not st.session_state.logged_in:
    st.title("🔐 Login Dashboard")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button and username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login riuscito!")
            st.stop()  # 🔒 interrompe il rendering fino al prossimo run
        elif login_button:
            st.error("❌ Credenziali non valide.")
    
    st.stop()

st.sidebar.success(f"Sei loggato come: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.experimental_rerun()
# ------------------------ CONFIGURAZIONE DATABASE ------------------------
# Sostituisci questi valori con quelli del tuo Azure PostgreSQL
DB_USER = "jacopob"
DB_PASS = "BiagioJ$"
DB_HOST = "databaseprojectwork.postgres.database.azure.com"
DB_PORT = "5432"
DB_NAME = "projectwork"

# Stringa di connessione SQLAlchemy
conn_string = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)
engine = create_engine(conn_string)

@st.cache_data
def load_table(table_name: str) -> pd.DataFrame:
    """
    Carica una tabella dal database e la restituisce come DataFrame.
    """
    query = f"SELECT * FROM {table_name};"
    return pd.read_sql(query, engine)

# Caricamento dati
with st.spinner("Caricamento dati dal database..."):
    df_iscrizioni = load_table("iscrizioni")
    df_stage = load_table("stage")
    df_corso_docenti = load_table("corso_docenti")
    df_corsi = load_table('corsi')
    df_corso_materie = load_table('corso_materie_its')  
    df_docenti = load_table('docenti')
    df_ore_alunno = load_table('ore_alunno')


# -------------------------------------------------------------------------

st.markdown("## 📊 Analisi Avanzata Dati Scolastici")

# -------------------------------
# 1. Ore frequentate per studente
# -------------------------------
st.subheader("📘 Ore frequentate dagli studenti")

if not df_ore_alunno.empty:
    top_ore = (
        df_ore_alunno.groupby(["id_alunno", "nome", "cognome"])["minuti_presenza"]
        .sum()
        .reset_index()
        .sort_values("minuti_presenza", ascending=False)
        .head(10)
    )
    top_ore["ore_totali"] = (top_ore["minuti_presenza"] / 60).round(1)

    st.bar_chart(
        top_ore.set_index("nome")["ore_totali"],
        use_container_width=True
    )
else:
    st.warning("Dati sulle ore non disponibili.")

# -------------------------------
# 2. Stage distribuiti per mese
# -------------------------------
st.subheader("🏢 Stage avviati per mese")

if not df_stage.empty and "datainiziostage" in df_stage.columns:
    df_stage["mese_inizio"] = pd.to_datetime(df_stage["datainiziostage"]).dt.to_period("M").astype(str)
    stage_per_mese = df_stage["mese_inizio"].value_counts().sort_index()

    st.line_chart(stage_per_mese)
else:
    st.warning("Dati stage non disponibili o colonna 'datainiziostage' mancante.")

# -------------------------------
# 3. Materie con più ore pianificate
# -------------------------------
st.subheader("📚 Materie con più ore pianificate")

if not df_corso_materie.empty:
    df_materie_ore = (
        df_corso_materie.groupby("materia")["ore_pianificate_monte_ore"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    st.bar_chart(df_materie_ore)
else:
    st.warning("Dati materie non disponibili.")


# -------------------------------------------------------------------------

# Titolo
st.title("Dashboard Dati Scolastici")

# Metriche chiave
col1, col2, col3 = st.columns(3)
col1.metric("Numero Studenti Iscritti", len(df_iscrizioni))
col2.metric("Numero Stage Registrati", len(df_stage))
# Corso più popolare
if "corso" in df_iscrizioni.columns:
    top_corso = df_iscrizioni["corso"].value_counts().idxmax()
    top_count = df_iscrizioni["corso"].value_counts().max()
    col3.metric("Corso più frequentato", top_corso, f"{top_count} iscrizioni")

st.markdown("---")

# Tabella Stage (ultimi 10 record)
st.subheader("Ultimi Stage Registrati")
st.dataframe(df_stage.sort_values(by="datainiziostage", ascending=False).head(10))

# Tabella Corsi-Docenti
st.subheader("Assegnazioni Corso - Docente")
st.dataframe(df_corso_docenti)

# Footer
st.markdown("---")
st.caption("Dashboard generata con Streamlit e dati PostgreSQL su Azure")
