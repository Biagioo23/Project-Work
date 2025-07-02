import requests
import psycopg2
from psycopg2 import Error
from psycopg2.extras import execute_values
from datetime import datetime

# === 1. API Stage ===
url = "https://api-pw25-grhhckd5abhdhccd.italynorth-01.azurewebsites.net/api/stage?DataDa=01/09/2000&DataA=01/05/2030"
headers = {
    "Authorization": "Bearer key_e2op232O"  # <-- sostituisci se cambia
}

data = None  # Initialize data to None
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("✅ Dati STAGE ricevuti.")

    # Stampo le chiavi del primo record per verificare i campi
    if data and len(data) > 0:
        print("Campi disponibili nel record:", data[0].keys())
except Exception as e:
    print(f"❌ Errore nella richiesta: {e}")

# === 2. Connessione al DB ===
conn = None
cursor = None
if data is not None:
    try:
        conn = psycopg2.connect(
            host="projectworkdata.postgres.database.azure.com",
            database="projectwork",
            user="jacopob",       # <-- inserisci username
            password="Biagioj$",   # <-- inserisci password
            port="5432",       # <-- inserisci porta (es. 5432)
            sslmode="require"
        )
        cursor = conn.cursor()
        print("✅ Connessione al database.")
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")

# === 3. Funzioni utili ===
def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None

# === 4. Inserimento dati STAGE ===
if data is not None and cursor is not None and conn is not None:
    try:
        for record in data:
            cursor.execute("""
                INSERT INTO stage (
                    idAlunno,
                    Cognome,
                    Nome,
                    idCorsoAnno,
                    CodiceCorso,
                    Corso,
                    Azienda,
                    PI,
                    DataInizioStage,
                    DataFineStage,
                    CF
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (idAlunno, idCorsoAnno) DO NOTHING;
            """, (
                record.get("idAlunno"),
                record.get("Cognome"),
                record.get("Nome"),
                record.get("idCorsoAnno"),
                record.get("CodiceCorso"),
                record.get("Corso"),
                record.get("Azienda"),
                record.get("PI"),
                parse_date(record.get("DataInizioStage")),
                parse_date(record.get("DataFineStage")),
                record.get("CF")  # <-- campo Codice Fiscale
            ))
        conn.commit()
        print("✅ Dati STAGE inseriti con successo.")
    except Exception as e:
        print(f"❌ Errore durante inserimento STAGE: {e}")
        if conn is not None:
            conn.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
        print("🔒 Connessione chiusa.")
