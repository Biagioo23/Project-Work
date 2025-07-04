import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

print("Inizio esecuzione dello script per l'inserimento dei dati STAGE...")

API_KEY_VALUE = "key_e2op232O"
AUTH_HEADER = f'Bearer {API_KEY_VALUE}'

DB_CONFIG = {
    'host': 'databaseprojectwork.postgres.database.azure.com',
    'port': '5432',
    'database': 'projectwork',
    'user': 'jacopob',
    'password': 'BiagioJ$',
    'sslmode': 'require'
}

HEADERS = {
    'Authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

BASE_URL = "https://api-pw25-grhhckd5abhdhccd.italynorth-01.azurewebsites.net/api/stage?DataDa=01/09/2000&DataA=01/05/2030"

anni_accademici = ['2020/2021', '2021/2022', '2022/2023', '2023/2024']

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date() if date_str else None
    except Exception:
        return None

def get_db_connection(cfg):
    try:
        return psycopg2.connect(**cfg)
    except Exception as e:
        print(f"Errore nella connessione al DB: {e}")
        return None

def get_stage_data(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Errore nella richiesta: {e}")
        return []

def get_stage_data_by_year(year):
    url = f"{BASE_URL}&AnnoAccademico={year}"
    return get_stage_data(url)

def etl_stage(data):
    processed = []
    seen_keys = set()
    for item in data:
        idAlunno = item.get("idAlunno")
        idCorsoAnno = item.get("idCorsoAnno")
        if not idAlunno or not idCorsoAnno:
            continue
        key = (idAlunno, idCorsoAnno)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        processed.append((
            idAlunno,
            item.get("Cognome"),
            item.get("Nome"),
            idCorsoAnno,
            item.get("CodiceCorso"),
            item.get("Corso"),
            item.get("Azienda"),
            item.get("PI"),
            parse_date(item.get("DataInizioStage")),
            parse_date(item.get("DataFineStage"))
        ))
    return processed

def crea_tabella_stage(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS public.stage (
        idAlunno VARCHAR(50) NOT NULL,
        Cognome VARCHAR(255),
        Nome VARCHAR(255),
        idCorsoAnno VARCHAR(50) NOT NULL,
        CodiceCorso VARCHAR(50),
        Corso VARCHAR(255),
        Azienda VARCHAR(255),
        PI VARCHAR(50),
        DataInizioStage DATE,
        DataFineStage DATE,
        PRIMARY KEY (idAlunno, idCorsoAnno)
    );
    """)

def main():
    all_data = []
    for anno in anni_accademici:
        print(f"Recupero dati per {anno}...")
        data = get_stage_data_by_year(anno)
        all_data.extend(data)
    
    print(f"✅ Dati STAGE totali recuperati: {len(all_data)} record.")
    
    processed_data = etl_stage(all_data)
    print(f"✅ Dati STAGE elaborati e pronti: {len(processed_data)} record.")
    
    if not processed_data:
        print("❌ Nessun dato STAGE da inserire.")
        return
    
    con = get_db_connection(DB_CONFIG)
    if con is None:
        return
    
    try:
        with con:
            with con.cursor() as cur:
                crea_tabella_stage(cur)
                insert_query = """
                    INSERT INTO public.stage (
                        idAlunno, Cognome, Nome, idCorsoAnno,
                        CodiceCorso, Corso, Azienda, PI,
                        DataInizioStage, DataFineStage
                    ) VALUES %s
                    ON CONFLICT (idAlunno, idCorsoAnno) DO NOTHING;
                """
                execute_values(cur, insert_query, processed_data)
                print(f"✅ Inseriti {len(processed_data)} record nel DB.")
    except Exception as e:
        print(f"❌ Errore durante l'inserimento nel DB: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    main()
