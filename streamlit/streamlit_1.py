import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from sqlalchemy import create_engine

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



# ✅ Configura la pagina
st.set_page_config(page_title="ITS Rizzoli - Dashboard", layout="wide")

# ✅ Utenti autorizzati (email: password)
users = {
    "governance": {'password' : '1234', 'role' : 'governance'},
    "coordinamento": {'password' : '4321', 'role' : 'coordinamento'},
}

# ✅ Inizializza lo stato della sessione
if "photo" not in st.session_state: 
    st.session_state.photo = None

# ✅ Funzione di login
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        with st.form("login"):
            st.title("🔐 Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Accedi")

            if submitted:
                user = users.get(username)
                if user and user["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user["role"]
                    st.success(f"Benvenuto {username}!")
                    st.rerun()
                else:
                    st.error("Credenziali errate.")
login()

# ✅ Funzione di logout
def logout():
    st.session_state.logged_in = False
    st.session_state.photo = None
    st.rerun()

# ✅ Dashboard principale
if st.session_state.logged_in:
    role = st.session_state.role
    st.sidebar.markdown(f"👤 **Ruolo:** {role.capitalize()}")

    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    # 👥 Governance: vista aggregata
    if role == "governance":
        st.title("📈 Dashboard Governance")
        st.markdown("### 👁️‍🗨️ Overview generale")
        st.metric("Totale Studenti", len(df_iscrizioni))
        st.metric("Stage Attivi", len(df_stage))
        st.metric("Corsi Attivi", len(df_corsi))
        # Altri dati aggregati o trend generali...

    # 🛠️ Coordinamento: vista tecnica
    elif role == "coordinamento":
        st.title("🧰 Dashboard Coordinamento Didattico")
        st.markdown("### 📘 Dettagli su corsi, ore e docenti")
        
        st.subheader("Ore frequentate per studente")
        # Mostra df_ore_alunno, bar chart...

        st.subheader("Materie con più ore pianificate")
        # Mostra df_corso_materie...

        st.subheader("Stage per mese")
        # Mostra df_stage...

        st.subheader("Assegnazione Docenti - Corsi")
        st.dataframe(df_corso_docenti)

    else:
        st.error("Ruolo non riconosciuto.")
