import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from sqlalchemy import create_engine
import altair as alt

# --- Configurazione Iniziale e Funzioni di Base ---

# 📥 Carica il logo solo nella login
def mostra_logo():
    logo_path = "logo_itsar.png" # Assicurati che questo percorso sia corretto e il file esista
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=200)
    except FileNotFoundError:
        st.warning(f"⚠️ Immagine logo non trovata: {logo_path}. Assicurati sia nella stessa directory del tuo script Streamlit.")

# 🔐 Connessione database
DB_USER = "jacopob"
DB_PASS = "BiagioJ$"
DB_HOST = "databaseprojectwork.postgres.database.azure.com"
DB_PORT = "5432"
DB_NAME = "projectwork"

conn_string = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)
# Aumenta il timeout per connessioni lente o query complesse
engine = create_engine(conn_string, connect_args={'options': '-c statement_timeout=5000'}) # 5 secondi di timeout

# Decoratore per il caching dei dati con una durata di vita di 1 ora (3600 secondi)
# Questo aiuta a non sovraccaricare il DB e a velocizzare, ma si aggiorna ogni ora.
# Per un aggiornamento forzato, puoi pulire la cache di Streamlit manualmente.
@st.cache_data(ttl=3600)
def load_table(table_name: str) -> pd.DataFrame:
    query = f"SELECT * FROM {table_name};"
    try:
        df = pd.read_sql(query, engine)
        # Rimosso il messaggio di successo per non intasare la dashboard
        # st.success(f"Tabella '{table_name}' caricata con successo.")
        return df
    except Exception as e:
        st.error(f"Errore durante il caricamento della tabella '{table_name}': {e}")
        return pd.DataFrame() # Ritorna un DataFrame vuoto in caso di errore

# Caricamento dati
with st.spinner("Caricamento dati dal database..."):
    df_iscrizioni = load_table("iscrizioni")
    df_stage = load_table("stage")
    df_corso_docenti = load_table("corso_docenti")
    df_corsi = load_table('corsi')
    df_corso_materie = load_table('corso_materie_its')  
    df_docenti = load_table('docenti')
    df_ore_alunno = load_table('ore_alunno')


# Configura la pagina
st.set_page_config(page_title="ITS Rizzoli - Dashboard", layout="wide")

# Utenti autorizzati (email: password)
# ✅ Utenti autorizzati
users = {
    "governance": {'password': '1234', 'role': 'governance'},
    "coordinamento": {'password': '4321', 'role': 'coordinamento'},
}

# Inizializza lo stato della sessione
if "photo" not in st.session_state: 
    st.session_state.photo = None

# Funzione di login
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        mostra_logo()
        with st.form("login"):
            st.title("Login")
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

# Funzione di logout
def logout():
    st.session_state.logged_in = False
    st.session_state.photo = None
    st.rerun()

login()

# Dashboard principale
if st.session_state.logged_in:
    role = st.session_state.role
    st.sidebar.markdown(f"👤 **Ruolo:** {role.capitalize()}")

    if st.sidebar.button("**Logout**"):
        logout()

    # Governance: vista aggregata
    if role == "governance":
        st.title("Dashboard Governance")
        st.markdown("### 👁️‍🗨️ Overview generale")

        # Metriche generali
        st.metric("Totale Studenti", len(df_iscrizioni) if not df_iscrizioni.empty else 0)
        st.metric("Stage Attivi", len(df_stage) if not df_stage.empty else 0)
        st.metric("Corsi Attivi", len(df_corsi) if not df_corsi.empty else 0)

        st.markdown("---")

        # 📊 Distribuzione degli esiti finali
        st.subheader("Distribuzione degli esiti finali")
        if 'esitofinale' in df_iscrizioni.columns and not df_iscrizioni.empty:
            # Pulizia e normalizzazione dei dati 'esitofinale'
            df_iscrizioni['esitofinale_pulito'] = df_iscrizioni['esitofinale'].astype(str).str.strip()
            df_iscrizioni['esitofinale_pulito'].replace('', 'Non definito', inplace=True)
            df_iscrizioni['esitofinale_pulito'].fillna('Non definito', inplace=True)

            esiti_count = df_iscrizioni['esitofinale_pulito'].value_counts().reset_index()
            esiti_count.columns = ['Esito Finale', 'Numero Studenti']
            esiti_count = esiti_count[esiti_count['Esito Finale'] != 'Non definito']
            esiti_count = esiti_count.sort_values('Numero Studenti', ascending=False)


            grafico_esiti = alt.Chart(esiti_count).mark_bar().encode(
                y=alt.Y('Esito Finale:N', sort='-x', title="Esito Finale"),
                x=alt.X('Numero Studenti:Q', title="Numero di Studenti"),
                color=alt.Color('Esito Finale:N', title="Esito Finale"),
                tooltip=['Esito Finale', 'Numero Studenti']
            ).properties(title='Distribuzione degli esiti finali degli studenti', height=300)
            st.altair_chart(grafico_esiti, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'esitofinale' non è presente o la tabella iscrizioni è vuota.")

        st.markdown("---")

        # 🏢 Distribuzione degli stage per azienda
        st.subheader("Distribuzione degli stage per azienda")

        if 'azienda' in df_stage.columns and not df_stage.empty:
            stage_count = df_stage['azienda'].value_counts().reset_index()
            stage_count.columns = ['Azienda', 'Numero Studenti']

            # Mostra solo le prime 15 aziende
            top_aziende = stage_count.head(20)

            grafico_stage = alt.Chart(top_aziende).mark_bar().encode(
                x=alt.X('Azienda:N', sort=alt.EncodingSortField(field='Numero Studenti', order='descending')),
                y='Numero Studenti:Q',
                color=alt.Color('Azienda:N', legend=None),
                tooltip=['Azienda', 'Numero Studenti']
            ).properties(title='Top 20 aziende per numero di studenti in stage').interactive()

            st.altair_chart(grafico_stage, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'azienda' non è presente o la tabella stage è vuota.")


        st.markdown("---")

        # 👩‍🏫 Ore totali lavorate dai docenti (CORRETTO NOME COLONNA 'ore lavoro')
        st.subheader("Ore totali lavorate dai docenti")
        # Attenzione allo spazio nel nome della colonna 'ore lavoro'
        if 'ore_lavorate' in df_corso_docenti.columns and not df_corso_docenti.empty:
            # Assicurati che 'ore lavoro' sia numerico
            df_corso_docenti['ore_lavorate'] = pd.to_numeric(df_corso_docenti['ore_lavorate'], errors='coerce')
            df_docenti_pulito = df_corso_docenti.dropna(subset=['ore_lavorate'])

            if not df_docenti_pulito.empty:
                df_docenti_ore_totali = df_docenti_pulito.groupby(['cognome', 'nome'])['ore_lavorate'].sum().reset_index().sort_values(by='ore_lavorate', ascending=False).head(20)
                df_docenti_ore_totali.columns = ['Cognome', 'Nome', 'Ore Totali Lavorate']

                grafico_docenti = alt.Chart(df_docenti_ore_totali).mark_bar().encode(
                    x=alt.X('Cognome:N', sort='-y', title="Docente"),
                    y=alt.Y('Ore Totali Lavorate:Q', title="Ore Lavorate"),
                    color=alt.Color('Cognome:N', legend=None),
                    tooltip=['Cognome', 'Nome', alt.Tooltip('Ore Totali Lavorate', format='.1f')]
                ).properties(title='Ore totali lavorate per docente (Top 20)').interactive()
                st.altair_chart(grafico_docenti, use_container_width=True)
            else:
                st.warning("⚠️ Nessun dato numerico valido per le 'ore_lavorate' nella tabella 'corso_docenti'.")
        else:
            st.warning("⚠️ La colonna 'ore_lavorate' non è presente in 'corso_docenti' o la tabella è vuota.")

        st.markdown("---")

        # 🥧 Distribuzione studenti per sesso (CORRETTO PULIZIA DATI)
        st.subheader("Distribuzione studenti per sesso")

        if 'sesso' in df_iscrizioni.columns and not df_iscrizioni.empty:
            # Pulizia e normalizzazione della colonna 'sesso'
            df_iscrizioni['sesso_pulito'] = df_iscrizioni['sesso'].astype(str).str.upper().str.strip()
            
            # Considera solo M e F, escludi tutto il resto
            valid_genders = ['M', 'F']
            df_filtrato = df_iscrizioni[df_iscrizioni['sesso_pulito'].isin(valid_genders)]

            sesso_counts = df_filtrato['sesso_pulito'].value_counts()

            if not sesso_counts.empty:
                labels = sesso_counts.index.tolist()
                sizes = sesso_counts.values
                colors = plt.get_cmap('Set2').colors[:len(labels)]

                fig, ax = plt.subplots(figsize=(6, 6))
                wedges, texts, autotexts = ax.pie(
                    sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                    colors=colors, textprops={'fontsize': 12, 'color': 'black'}
                )
                ax.axis('equal')
                plt.setp(autotexts, size=10, weight="bold")
                plt.setp(texts, size=10)
                st.pyplot(fig)
            else:
                st.info("ℹ️ Nessun dato valido per 'M' o 'F' nella colonna 'sesso'.")
        else:
            st.warning("⚠️ La colonna 'sesso' non è presente nella tabella iscrizioni o la tabella è vuota.")


        st.markdown("---")

        # 📚 Studenti iscritti per Corso
        st.subheader("Studenti iscritti per Corso")
        if 'corso' in df_iscrizioni.columns and not df_iscrizioni.empty:
            studenti_per_corso = df_iscrizioni['corso'].value_counts().reset_index()
            studenti_per_corso.columns = ['Corso', 'Numero Studenti']
            grafico_studenti_corso = alt.Chart(studenti_per_corso).mark_bar().encode(
                x=alt.X('Corso:N', sort='-y', title="Corso"),
                y=alt.Y('Numero Studenti:Q', title="Numero di Studenti"),
                color=alt.Color('Corso:N', legend=None),
                tooltip=['Corso', 'Numero Studenti']
            ).properties(title='Numero di studenti iscritti per corso').interactive()
            st.altair_chart(grafico_studenti_corso, use_container_width=True)
        else:
            st.warning("⚠️ La colonna 'corso' non è presente nella tabella iscrizioni o la tabella è vuota.")

        st.markdown("---")

        # 📉 Percentuale di Studenti Ritirati
        st.subheader("Percentuale di Studenti Ritirati")
        if 'ritiratocorso' in df_iscrizioni.columns and not df_iscrizioni.empty:
            # Converti in booleano e poi a stringa per chiarezza
            df_iscrizioni['ritiratocorso_pulito'] = df_iscrizioni['ritiratocorso'].astype(bool).map({True: 'Ritirati', False: 'Non Ritirati'})
            ritirati_counts = df_iscrizioni['ritiratocorso_pulito'].value_counts()

            if not ritirati_counts.empty:
                labels_ritirati = ritirati_counts.index.tolist()
                sizes_ritirati = ritirati_counts.values
                colors_ritirati = ['#FF9999', '#66B2FF'] # Colori per Ritirati e Non Ritirati

                fig_ritirati, ax_ritirati = plt.subplots(figsize=(6, 6))
                wedges_ritirati, texts_ritirati, autotexts_ritirati = ax_ritirati.pie(
                    sizes_ritirati, labels=labels_ritirati, autopct='%1.1f%%', startangle=90,
                    colors=colors_ritirati, textprops={'fontsize': 12, 'color': 'black'}
                )
                ax_ritirati.axis('equal')
                plt.setp(autotexts_ritirati, size=10, weight="bold")
                plt.setp(texts_ritirati, size=10)
                st.pyplot(fig_ritirati)
            else:
                st.info("ℹ️ Nessun dato sui ritiri degli studenti disponibile o valori inattesi nella colonna 'ritiratocorso'.")
        else:
            st.warning("⚠️ La colonna 'ritiratocorso' non è presente nella tabella iscrizioni o la tabella è vuota.")

    # --- Dashboard Coordinamento Didattico ---
    elif role == "coordinamento":
        st.title("**Dashboard Coordinamento Didattico**")
        st.markdown("### Dettagli su corsi, ore e docenti")

        st.markdown("---")

        # 📚 Dettaglio Ore di Presenza per Materia per studente selezionato
        st.subheader("Dettaglio Ore di Presenza per Materia (seleziona uno studente)")
        if 'nome' in df_ore_alunno.columns and 'cognome' in df_ore_alunno.columns and 'materia' in df_ore_alunno.columns and not df_ore_alunno.empty:
            df_ore_alunno_temp = df_ore_alunno.copy()
            df_ore_alunno_temp['Alunno'] = df_ore_alunno_temp['nome'] + ' ' + df_ore_alunno_temp['cognome']
            studenti_list = df_ore_alunno_temp['Alunno'].unique().tolist()

            selected_student = st.selectbox("Seleziona uno studente per vedere il dettaglio delle ore per materia:", [''] + sorted(studenti_list))

            if selected_student:
                df_selected_student = df_ore_alunno_temp[df_ore_alunno_temp['Alunno'] == selected_student].copy()
                df_selected_student['minuti_presenza'] = pd.to_numeric(df_selected_student['minuti_presenza'], errors='coerce')
                df_selected_student = df_selected_student.dropna(subset=['minuti_presenza'])

                if not df_selected_student.empty:
                    df_selected_student['ore_presenza'] = df_selected_student['minuti_presenza'] / 60

                    grafico_ore_materia_singolo = alt.Chart(df_selected_student).mark_bar().encode(
                        x=alt.X('materia:N', title="Materia", sort='-y'),
                        y=alt.Y('ore_presenza:Q', title="Ore di Presenza"),
                        color=alt.Color('materia:N', legend=None),
                        tooltip=['materia', alt.Tooltip('ore_presenza', format='.2f')]
                    ).properties(title=f'Ore di Presenza di {selected_student} per Materia').interactive()
                    st.altair_chart(grafico_ore_materia_singolo, use_container_width=True)
                else:
                    st.info(f"ℹ️ Nessun dato valido per le ore di presenza di {selected_student}.")
        else:
            st.warning("⚠️ Dati insufficienti in 'ore_alunno' per visualizzare il dettaglio delle ore per materia o la tabella è vuota.")

        st.markdown("---")

        # Materie con più ore pianificate
        st.subheader("Materie con più ore pianificate")
        if 'materia' in df_corso_materie.columns and 'ore_pianificate_monte_ore' in df_corso_materie.columns and not df_corso_materie.empty:
            df_corso_materie['ore_pianificate_monte_ore'] = pd.to_numeric(df_corso_materie['ore_pianificate_monte_ore'], errors='coerce')
            df_corso_materie_pulito = df_corso_materie.dropna(subset=['ore_pianificate_monte_ore'])

            if not df_corso_materie_pulito.empty:
                ore_pianificate_per_materia = df_corso_materie_pulito.groupby('materia')['ore_pianificate_monte_ore'].sum().reset_index().sort_values(by='ore_pianificate_monte_ore', ascending=False).head(20)

                grafico_pianificate = alt.Chart(ore_pianificate_per_materia).mark_bar().encode(
                    x=alt.X('materia:N', sort='-y', title="Materia"),
                    y=alt.Y('ore_pianificate_monte_ore:Q', title="Ore pianificate"),
                    color=alt.Color('materia:N', legend=None),
                    tooltip=['materia', alt.Tooltip('ore_pianificate_monte_ore', format='.1f')]
                ).properties(title='Ore pianificate da piano ITS per materia (Top 20)').interactive()
                st.altair_chart(grafico_pianificate, use_container_width=True)
            else:
                st.warning("⚠️ Nessun dato numerico valido per le ore pianificate in 'corso_materie_its'.")
        else:
            st.warning("⚠️ Colonne necessarie (materia, ore_pianificate_monte_ore) non trovate in corso_materie_its o la tabella è vuota.")

        st.markdown("---")

        # 🗓️ Distribuzione degli stage per mese di inizio
        st.subheader("Distribuzione degli stage per mese di inizio")
        if 'datainiziostage' in df_stage.columns and not df_stage.empty:
            df_stage['datainiziostage'] = pd.to_datetime(df_stage['datainiziostage'], errors='coerce')
            df_stage_pulito = df_stage.dropna(subset=['datainiziostage'])

            if not df_stage_pulito.empty:
                df_stage_pulito['mese_inizio_nome'] = df_stage_pulito['datainiziostage'].dt.strftime('%Y-%m') # Formato 'YYYY-MM' per ordinamento corretto
                stage_mese = df_stage_pulito['mese_inizio_nome'].value_counts().sort_index().reset_index()
                stage_mese.columns = ['Mese', 'Numero Stage']
                grafico_stage_mese = alt.Chart(stage_mese).mark_bar().encode(
                    x=alt.X('Mese:N', sort='x', title="Mese di Inizio Stage"),
                    y=alt.Y('Numero Stage:Q', title="Numero di Stage"),
                    tooltip=['Mese', 'Numero Stage']
                ).properties(title='Distribuzione degli stage per mese di inizio').interactive()
                st.altair_chart(grafico_stage_mese, use_container_width=True)
            else:
                st.warning("⚠️ Nessun dato valido per le date di inizio stage nella tabella stage.")
        else:
            st.warning("⚠️ La colonna 'datainiziostage' non è presente nella tabella stage o la tabella è vuota.")

        st.markdown("---")

        # Assegnazione Docenti - Corsi (DataFrame)
        df_unito = pd.merge(df_corso_docenti, df_corsi, on='idcorsoanno', how='inner')
        print(df_unito.columns.tolist())
        df_selezionato = df_unito['id_utente', 'cognome', 'nome', 'materia', 'corsi', 'monte_ore', 'ore_lavorate']
        st.subheader("Assegnazione Docenti - Materia")
        if not df_corso_docenti.empty:
            st.dataframe(df_corso_docenti)
        else:
            st.info("ℹ️ La tabella 'corso_docenti' è vuota.")

        st.markdown("---")

        st.subheader("Voto Medio per Materia per Corso (seleziona un corso)")

        # Verifica colonne necessarie in entrambe le tabelle
        if all(col in df_ore_alunno.columns for col in ['id_alunno', 'materia', 'voto_medio']) and \
        all(col in df_iscrizioni.columns for col in ['idalunno', 'corso']) and \
        not df_ore_alunno.empty and not df_iscrizioni.empty:
            
            # Merge tra le due tabelle sul campo idalunno
            df_merge = pd.merge(df_ore_alunno, df_iscrizioni, left_on='id_alunno', right_on='idalunno', how='inner')

            # Pulizia valori
            df_merge['voto_medio'] = pd.to_numeric(df_merge['voto_medio'], errors='coerce')
            df_merge = df_merge.dropna(subset=['voto_medio', 'materia', 'corso'])

            # Selezione corso
            corsi_list = sorted(df_merge['corso'].dropna().unique().tolist())
            selected_corso = st.selectbox("Seleziona un corso:", [''] + corsi_list)

            if selected_corso:
                df_filtered = df_merge[df_merge['corso'] == selected_corso]

                # Calcolo media per materia
                df_media = df_filtered.groupby('materia', as_index=False)['voto_medio'].mean()

                if not df_media.empty:
                    chart = alt.Chart(df_media).mark_bar().encode(
                        x=alt.X('materia:N', title="Materia", sort='-y'),
                        y=alt.Y('voto_medio:Q', title="Voto Medio"),
                        color=alt.Color('materia:N', legend=None),
                        tooltip=['materia', alt.Tooltip('voto_medio', format='.2f')]
                    ).properties(title=f'Voto Medio per Materia - Corso {selected_corso}').interactive()

                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info(f"ℹ️ Nessun voto disponibile per il corso '{selected_corso}'.")
        else:
            st.warning("⚠️ Colonne richieste assenti o dati insufficienti in 'ore_alunno' e 'iscrizioni'.")

