import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from PIL import Image
import seaborn as sns

# --------------------------------------------------
# ✅ CONFIGURAZIONE PAGINA
# --------------------------------------------------
st.set_page_config(page_title="ITS Rizzoli - Dashboard", layout="wide")

# --------------------------------------------------
# ✅ UTENTI AUTORIZZATI (email: password)
# --------------------------------------------------
users = {
    "isret.jahan@itsrizzoli.it": "1234",
    "jacopo.biaggioni@itsrizzoli.it": "4321"
}

# --------------------------------------------------
# ✅ STATO SESSIONE
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = ""
if "photo" not in st.session_state:
    st.session_state.photo = None

# --------------------------------------------------
# ✅ FUNZIONE LOGIN
# --------------------------------------------------
def login():
    st.title("🔐 Login ITS Rizzoli")
    email = st.text_input("Email istituzionale", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        if email in users and users[email] == password:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success(f"✅ Accesso effettuato! Benvenutə, {email}")
            st.rerun()
        else:
            st.error("❌ Email o password errati")

# --------------------------------------------------
# ✅ FUNZIONE LOGOUT
# --------------------------------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.photo = None
    st.rerun()

# --------------------------------------------------
# ✅ CONNESSIONE AL DATABASE
# --------------------------------------------------
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        user="jacopob",
        password="BiagioJ$",
        host="databaseprojectwork.postgres.database.azure.com",
        port="5432",
        database="projectwork"
    )

conn = get_connection()

# --------------------------------------------------
# ✅ CARICA I DATI
# --------------------------------------------------
@st.cache_data
def load_data():
    query = "SELECT * FROM iscrizioni"
    return pd.read_sql_query(query, conn)

df_iscrizioni = load_data()

# --------------------------------------------------
# ✅ DASHBOARD PRINCIPALE
# --------------------------------------------------
def main_dashboard():
    st.title("Benvenuti all'ITS Rizzoli")
    st.subheader("Innovazione, Formazione, Lavoro")

    # Navigazione
    st.sidebar.title("📂 Navigazione")
    sezione = st.sidebar.radio("Vai a:", ["🏫 Chi siamo", "📊 Dashboard Dati", "📞 Contatti"], key="menu_radio")
    st.sidebar.button("🔓 Logout", on_click=logout)

    # --- Sezione: Chi siamo
    if sezione == "🏫 Chi siamo":
        st.header("Chi siamo")
        st.markdown("""
        L'ITS Rizzoli è un istituto tecnico superiore dedicato alla formazione in ambito ICT, Intelligenza Artificiale, Big Data, e altro ancora.
        
        Offriamo percorsi innovativi, strettamente connessi con le imprese del territorio e con un alto tasso di occupabilità.
        """)

    # --- Sezione: Dashboard Dati
    elif sezione == "📊 Dashboard Dati":
        st.header("📊 Dashboard dati ITS Rizzoli")
        st.info("Visualizza l'andamento degli studenti, placement e corsi.")

        # Filtri
        with st.sidebar:
            st.header("📌 Filtri")
            anni = df_iscrizioni["anno"].dropna().unique()
            anno_scelto = st.selectbox("Seleziona Anno", sorted(anni, reverse=True))

        # Applica filtro per anno
        df_filtered = df_iscrizioni[df_iscrizioni["anno"] == anno_scelto]

        # KPI
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👨‍🎓 Totale Iscritti", df_filtered["id_alunno"].nunique())
        with col2:
            perc_femminile = (df_filtered[df_filtered["genere"] == "F"].shape[0] / df_filtered.shape[0]) * 100
            st.metric("👩‍🎓 % Femminile", f"{perc_femminile:.1f}%")
        with col3:
            media_eta = df_filtered["eta"].mean()
            st.metric("📈 Età media", f"{media_eta:.1f} anni")

        # 📊 Iscritti per corso
        st.subheader("Iscritti per corso")
        query_corsi = """
        SELECT c.nome_corso, COUNT(*) as n_iscritti
        FROM iscrizioni i
        JOIN corsi c ON i.id_corso = c.id_corso
        WHERE i.anno = %s
        GROUP BY c.nome_corso
        ORDER BY n_iscritti DESC;
        """
        df_corsi = pd.read_sql_query(query_corsi, conn, params=[anno_scelto])

        fig, ax = plt.subplots()
        sns.barplot(data=df_corsi, x="n_iscritti", y="nome_corso", ax=ax, palette="Blues_d")
        ax.set_xlabel("Numero Iscritti")
        ax.set_ylabel("Corso")
        st.pyplot(fig)

        # 📈 Trend iscrizioni
        st.subheader("Andamento iscrizioni nel tempo")
        query_trend = """
        SELECT anno, COUNT(*) as totale
        FROM iscrizioni
        GROUP BY anno
        ORDER BY anno;
        """
        df_trend = pd.read_sql_query(query_trend, conn)

        fig2, ax2 = plt.subplots()
        ax2.plot(df_trend["anno"], df_trend["totale"], marker="o", color="green")
        ax2.set_ylabel("Iscrizioni")
        ax2.set_xlabel("Anno")
        ax2.set_title("Trend iscrizioni")
        st.pyplot(fig2)

    # --- Sezione: Contatti
    elif sezione == "📞 Contatti":
        st.header("Contatti")
        st.markdown("""
        - 📧 Email: info@itsrizzoli.it  
        - ☎️ Telefono: +39 02 1234567  
        - 📍 Indirizzo: Via Rizzoli 4, Milano  
        - 🌐 [Sito web ITS Rizzoli](https://www.itsrizzoli.it)
        """)

# --------------------------------------------------
# ✅ AVVIO APP
# --------------------------------------------------
if st.session_state.logged_in:
    main_dashboard()
else:
    login()
