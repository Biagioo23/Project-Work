import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from PIL import Image

# ✅ Configura la pagina
st.set_page_config(page_title="ITS Rizzoli - Dashboard", layout="wide")

# ✅ Utenti autorizzati (email: password)
users = {
    "isret.jahan@itsrizzoli.it": "1234",
    "jacopo.biaggioni@itsrizzoli.it": "4321"
}

# ✅ Inizializza lo stato della sessione
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = ""
if "photo" not in st.session_state:
    st.session_state.photo = None

# ✅ Funzione di login
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

# ✅ Funzione di logout
def logout():
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.photo = None
    st.rerun()

# ✅ Dashboard principale
def main_dashboard():
    st.title("Benvenuti all'ITS Rizzoli")
    st.subheader("Innovazione, Formazione, Lavoro")


    # Sidebar: navigazione
    st.sidebar.title("📂 Navigazione")
    sezione = st.sidebar.radio("Vai a:", ["🏫 Chi siamo", "📊 Dashboard Dati", "📞 Contatti"], key="menu_radio")

    # Pulsante Logout
    st.sidebar.button("🔓 Logout", on_click=logout)

    # Sezioni
    if sezione == "🏫 Chi siamo":
        st.header("Chi siamo")
        st.markdown("""
        L'ITS Rizzoli è un istituto tecnico superiore dedicato alla formazione in ambito ICT, Intelligenza Artificiale, Big Data, e altro ancora.
        
        Offriamo percorsi innovativi, strettamente connessi con le imprese del territorio e con un alto tasso di occupabilità.
        """)

    elif sezione == "📊 Dashboard Dati":
        st.header("Dashboard dati ITS Rizzoli")
        st.info("Qui puoi visualizzare l'andamento degli studenti, placement e corsi.")

        # Dati esempio
        df = pd.DataFrame({
            "Anno": [2022, 2023, 2024],
            "Studenti Iscritti": [250, 300, 340],
            "Placement (%)": [85, 88, 90]
        })

        st.dataframe(df)

        fig, ax = plt.subplots()
        ax.plot(df["Anno"], df["Placement (%)"], marker='o', color='green')
        ax.set_title("Tasso di Placement")
        ax.set_xlabel("Anno")
        ax.set_ylabel("Placement (%)")
        st.pyplot(fig)

    elif sezione == "📞 Contatti":
        st.header("Contatti ITS Rizzoli")
        st.markdown("""
        📍 Sede: Milano  
        📧 Email: info@itsrizzoli.it  
        📞 Telefono: 02 1234567  
        🌐 [Sito ufficiale](https://www.itsrizzoli.it)
        """)

# ✅ Avvia login o dashboard
if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
# ✅ Fine del codice