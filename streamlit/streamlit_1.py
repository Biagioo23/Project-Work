import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from sqlalchemy import create_engine
import altair as alt

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
        st.rerun()

    # 👥 Governance: vista aggregata
    if role == "governance":
        st.title("📈 Dashboard Governance")
        st.markdown("### 👁️‍🗨️ Overview generale")
        st.metric("Totale Studenti", len(df_iscrizioni))
        st.metric("Stage Attivi", len(df_stage))
        st.metric("Corsi Attivi", len(df_corsi))
        # 📊 Grafico: Distribuzione esiti finali
        st.subheader("📊 Distribuzione degli esiti finali")
        esiti_count = df_iscrizioni['esitofinale'].value_counts().reset_index()
        esiti_count.columns = ['Esito Finale', 'Numero Studenti']
        grafico_esiti = alt.Chart(esiti_count).mark_bar().encode(
            x='Esito Finale:N',
            y='Numero Studenti:Q',
            color='Esito Finale:N',
            tooltip=['Esito Finale', 'Numero Studenti']
        ).properties(title='Esiti finali degli studenti')
        st.altair_chart(grafico_esiti, use_container_width=True)

        # 📊 Grafico: Stage per azienda
        st.subheader("🏢 Distribuzione degli stage per azienda")
        stage_count = df_stage['azienda'].value_counts().reset_index()
        stage_count.columns = ['Azienda', 'Numero Studenti']
        grafico_stage = alt.Chart(stage_count).mark_bar().encode(
            x='Azienda:N',
            y='Numero Studenti:Q',
            color='Azienda:N',
            tooltip=['Azienda', 'Numero Studenti']
        ).properties(title='Numero di studenti per azienda di stage')
        st.altair_chart(grafico_stage, use_container_width=True)

        # 📊 Grafico: Ore lavorate dai docenti
        st.subheader("👩‍🏫 Ore lavorate dai docenti")
        grafico_docenti = alt.Chart(df_corso_docenti).mark_bar().encode(
            x='cognome:N',
            y='ore_lavorate:Q',
            color='cognome:N',
            tooltip=['cognome', 'nome', 'materia', 'ore_lavorate']
        ).properties(title='Ore lavorate per docente')
        st.altair_chart(grafico_docenti, use_container_width=True)


    # 🛠️ Coordinamento: vista tecnica
    elif role == "coordinamento":
        st.title("🧰 Dashboard Coordinamento Didattico")
        st.markdown("### 📘 Dettagli su corsi, ore e docenti")
        
        st.subheader("Ore frequentate per studente")
        df_ore_alunno['ore_presenza'] = df_ore_alunno['minuti_presenza'] / 60
        grafico_ore = alt.Chart(df_ore_alunno).mark_bar().encode(
            x='materia:N',
            y='ore_presenza:Q',
            color='materia:N',
            tooltip=['nome', 'cognome', 'materia', 'ore_presenza']
        ).properties(title='Ore di presenza per materia')
        st.altair_chart(grafico_ore, use_container_width=True)

        st.subheader("Materie con più ore pianificate")
        grafico_pianificate = alt.Chart(df_corso_materie).mark_bar().encode(
            x='materia:N',
            y='ore_pianificate_monte_ore:Q',
            color='materia:N',
            tooltip=['materia', 'ore_pianificate_monte_ore']
        ).properties(title='Ore pianificate da piano ITS per materia')
        st.altair_chart(grafico_pianificate, use_container_width=True)

        st.subheader("Stage per mese")
        st.subheader("🗓️ Stage per mese")
        df_stage['mese_inizio'] = pd.to_datetime(df_stage['datainiziostage']).dt.to_period('M')
        stage_mese = df_stage['mese_inizio'].value_counts().sort_index().reset_index()
        stage_mese.columns = ['Mese', 'Numero Stage']
        grafico_stage_mese = alt.Chart(stage_mese).mark_bar().encode(
            x='Mese:N',
            y='Numero Stage:Q',
            tooltip=['Mese', 'Numero Stage']
        ).properties(title='Distribuzione degli stage per mese')
        st.altair_chart(grafico_stage_mese, use_container_width=True)

        st.subheader("Assegnazione Docenti - Corsi")
        st.dataframe(df_corso_docenti)

    else:
        st.error("Ruolo non riconosciuto.")