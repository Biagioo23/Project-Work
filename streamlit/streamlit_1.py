import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns

# Configura pagina Streamlit
st.set_page_config(page_title="Dashboard ITS Rizzoli", layout="wide")

# Utenti autorizzati (email: password)
users = {
    "isret.jahan@itsrizzoli.it": "1234",
    "jacopo.biaggioni@itsrizzoli.it": "4321"
}

# Stato sessione login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = ""

# Funzione login
def login():
    st.title("🔐 Login ITS Rizzoli")
    email = st.text_input("Email istituzionale", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if email in users and users[email] == password:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success(f"✅ Accesso effettuato! Benvenutə, {email}")
            st.rerun()
        else:
            st.error("❌ Email o password errati")

# Funzione logout
def logout():
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.rerun()

# Funzione connessione DB con gestione errori
@st.cache_resource
def get_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",          # Cambia con il tuo host
            database="nome_database",  # Cambia con il tuo database
            user="tuo_username",       # Cambia con il tuo username
            password="tua_password"    # Cambia con la tua password
        )
        return conn
    except Exception as e:
        st.error(f"Errore connessione al database: {e}")
        return None

# Funzione per caricare dati iscrizioni
@st.cache_data(ttl=600)
def load_data(conn, anno=None):
    if conn is None:
        return pd.DataFrame()
    query = "SELECT * FROM iscrizioni"
    if anno:
        query += f" WHERE anno = {anno}"
    return pd.read_sql_query(query, conn)

# Dashboard principale
def main_dashboard():
    st.title("📊 Dashboard ITS Rizzoli")
    st.sidebar.title("📂 Navigazione")
    pagina = st.sidebar.radio("Seleziona sezione:", ["🏫 Chi siamo", "📊 Dashboard Dati", "📞 Contatti"])

    st.sidebar.button("🔓 Logout", on_click=logout)

    if pagina == "🏫 Chi siamo":
        st.header("Chi siamo")
        st.markdown("""
        L'ITS Rizzoli è un istituto tecnico superiore dedicato alla formazione in ambito ICT, Intelligenza Artificiale, Big Data, e altro ancora.

        Offriamo percorsi innovativi, strettamente connessi con le imprese del territorio e con un alto tasso di occupabilità.
        """)

    elif pagina == "📊 Dashboard Dati":
        st.header("Dashboard dati iscrizioni")

        conn = get_connection()
        if conn is None:
            st.stop()

        df_iscrizioni = load_data(conn)

        if df_iscrizioni.empty:
            st.warning("Nessun dato disponibile.")
            return

        anni = sorted(df_iscrizioni["anno"].dropna().unique(), reverse=True)
        anno_scelto = st.sidebar.selectbox("Seleziona Anno", anni)

        df_filtered = df_iscrizioni[df_iscrizioni["anno"] == anno_scelto]

        # KPI
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👨‍🎓 Totale Iscritti", df_filtered["id_alunno"].nunique())
        with col2:
            perc_fem = (df_filtered[df_filtered["genere"] == "F"].shape[0] / df_filtered.shape[0]) * 100 if df_filtered.shape[0] > 0 else 0
            st.metric("👩‍🎓 % Femminile", f"{perc_fem:.1f}%")
        with col3:
            eta_media = df_filtered["eta"].mean()
            st.metric("📈 Età media", f"{eta_media:.1f} anni")

        # Grafico iscritti per corso
        query_corsi = """
        SELECT c.nome_corso, COUNT(*) as n_iscritti
        FROM iscrizioni i
        JOIN corsi c ON i.id_corso = c.id_corso
        WHERE i.anno = %s
        GROUP BY c.nome_corso
        ORDER BY n_iscritti DESC;
        """
        df_corsi = pd.read_sql_query(query_corsi, conn, params=[anno_scelto])

        st.subheader("Iscritti per corso")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=df_corsi, y="nome_corso", x="n_iscritti", ax=ax, palette="Blues_d")
        ax.set_xlabel("Numero Iscritti")
        ax.set_ylabel("Corso")
        st.pyplot(fig)

        # Grafico andamento iscrizioni nel tempo
        query_trend = """
        SELECT anno, COUNT(*) as totale
        FROM iscrizioni
        GROUP BY anno
        ORDER BY anno;
        """
        df_trend = pd.read_sql_query(query_trend, conn)

        st.subheader("Andamento iscrizioni nel tempo")
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(df_trend["anno"], df_trend["totale"], marker="o", color="green")
        ax2.set_xlabel("Anno")
        ax2.set_ylabel("Iscrizioni")
        ax2.set_title("Trend iscrizioni")
        st.pyplot(fig2)

    elif pagina == "📞 Contatti":
        st.header("Contatti")
        st.markdown("""
        - Email: info@itsrizzoli.it  
        - Telefono: +39 123 456 7890  
        - Indirizzo: Via Rizzoli 20, Milano
        """)

# Avvio app
if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
