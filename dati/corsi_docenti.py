import requests
import psycopg2
from psycopg2 import Error
from psycopg2.extras import execute_values

# --- CONFIGURAZIONE GLOBALE ---
print("Inizio configurazione per l'ETL dell'endpoint 'corso_docenti'...")

API_KEY_VALUE = 'key_e2op232O'
AUTH_HEADER = f'Bearer {API_KEY_VALUE}'

DB_HOST = 'databaseprojectwork.postgres.database.azure.com'
DB_PORT = '5432'
DB_NAME = 'projectwork'
DB_USER = 'jacopob'
DB_PASS = 'BiagioJ$'
DB_SSLMODE = 'require'

HEADERS = {
    'Authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

BASE_API_URL = 'https://api-pw25-grhhckd5abhdhccd.italynorth-01.azurewebsites.net/api/'
CORSI_ENDPOINT = 'corsi'
CORSO_DOCENTI_ENDPOINT = 'corso_docenti'
TABLE_NAME_CORSO_DOCENTI = 'corso_docenti'

print("Configurazione completata.")
print("-" * 30)

# --- FUNZIONI ---

def extract_data_from_api(endpoint_url, headers, params=None):
    print(f"Estrazione da: {endpoint_url} con parametri {params}")
    try:
        response = requests.get(endpoint_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"   Estrazione completata: {len(data)} record.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"   ERRORE nella richiesta API: {e}")
        return None
    except ValueError as e:
        print(f"   ERRORE parsing JSON: {e}")
        return None

def get_db_connection(config):
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            dbname=config['dbname'],
            user=config['user'],
            password=config['password'],
            sslmode=config['sslmode']
        )
        return conn
    except Error as e:
        print(f"   ERRORE connessione DB: {e}")
        return None

def transform_data_for_corso_docenti(raw_data, fallback_idcorsoanno=None):
    print("Inizio trasformazione dati per 'corso_docenti'...")
    transformed = []
    seen_keys = set()

    for item in raw_data:
        if not isinstance(item, dict):
            print(f"   ⚠️ Ignorato item non valido: {item}")
            continue

        try:
            id_utente = str(item.get("idUtente"))
            cognome = item.get("Cognome", "")
            nome = item.get("Nome", "")
            idcorsoanno = item.get('idCorsoAnno')

            # Se idcorsoanno è None o vuoto, usa fallback
            if not idcorsoanno and fallback_idcorsoanno is not None:
                idcorsoanno = int(fallback_idcorsoanno)
            else:
                # Provo a convertire a int se è presente
                try:
                    idcorsoanno = int(idcorsoanno)
                except:
                    idcorsoanno = None

            materia = item.get("Materia", "")
            monte_ore = int(item.get("MonteOre", 0)) if str(item.get("MonteOre", "")).isdigit() else 0
            ore_lavorate = int(item.get("OreLavorate", 0)) if str(item.get("OreLavorate", "")).isdigit() else 0

            key = (id_utente, materia, idcorsoanno)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            transformed.append((
                id_utente, cognome, nome, materia, idcorsoanno, monte_ore, ore_lavorate
            ))
        except Exception as e:
            print(f"   ERRORE trasformazione record: {e}")
            continue

    print(f"   Trasformazione completata: {len(transformed)} record.")
    print(f"   Esempio dati: {transformed[:2]}")
    return transformed


def load_data_to_postgres_corso_docenti(data, config, table_name):
    print(f"Inizio caricamento nella tabella '{table_name}'...")
    if not data:
        print("   Nessun dato da caricare.")
        return

    conn = get_db_connection(config)
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT tablename FROM pg_tables WHERE tablename = '{table_name}';")
            exists = cur.fetchone()
            print(f"Tabella '{table_name}' esiste: {exists is not None}")
            
            if exists:
                print(f"Droppo la tabella '{table_name}'")
                cur.execute(f"DROP TABLE {table_name} CASCADE;")
                conn.commit()
                print(f"Tabella '{table_name}' eliminata.")

            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id_utente VARCHAR(255),
                    cognome VARCHAR(255),
                    nome VARCHAR(255),
                    materia VARCHAR(255),
                    idcorsoanno INTEGER NULL,
                    monte_ore INTEGER,
                    ore_lavorate INTEGER,
                    PRIMARY KEY (id_utente, materia)
                );
            """)
            conn.commit()
            print(f"   Tabella '{table_name}' pronta.")

            insert_query = f"""
                INSERT INTO {table_name} (
                    id_utente, cognome, nome, materia, idcorsoanno, monte_ore, ore_lavorate
                ) VALUES %s
                ON CONFLICT (id_utente, materia) DO UPDATE SET
                    cognome = EXCLUDED.cognome,
                    nome = EXCLUDED.nome,
                    monte_ore = EXCLUDED.monte_ore,
                    ore_lavorate = EXCLUDED.ore_lavorate,
                    idcorsoanno = EXCLUDED.idcorsoanno;
            """
            execute_values(cur, insert_query, data)
            conn.commit()
            print(f"   Caricati {len(data)} record nella tabella '{table_name}'.")
    except Error as e:
        print(f"   ERRORE durante il caricamento: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"   Connessione chiusa per '{table_name}'.")
        print("-" * 30)

# --- MAIN PROCESS ---

if __name__ == "__main__":
    db_config = {
        'host': DB_HOST,
        'port': DB_PORT,
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASS,
        'sslmode': DB_SSLMODE
    }

    all_docenti = []

    print("Recupero lista idCorsoAnno da 'corsi'...")
    corsi_data = extract_data_from_api(f"{BASE_API_URL}{CORSI_ENDPOINT}", HEADERS)

    if corsi_data:
        id_corsi = [str(item.get("idCorsoAnno")) for item in corsi_data if item.get("idCorsoAnno")]
        print(f"Trovati {len(id_corsi)} idCorsoAnno.")

        seen_keys = set()

        for i, id_corso in enumerate(id_corsi):
            print(f"Elaborazione corso {i+1}/{len(id_corsi)}: idCorsoAnno = {id_corso}")
            docenti_data = extract_data_from_api(f"{BASE_API_URL}{CORSO_DOCENTI_ENDPOINT}", HEADERS, {"idCorsoAnno": id_corso})

            if docenti_data:
                # Passo anche id_corso per fallback in trasformazione
                transformed = transform_data_for_corso_docenti(docenti_data, fallback_idcorsoanno=id_corso)

                for row in transformed:
                    key = (row[0], row[3])  # id_utente, materia
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_docenti.append(row)
            else:
                print(f"   Nessun dato per idCorsoAnno {id_corso}.")


        print(f"\nTotale record unici trasformati: {len(all_docenti)}")
        load_data_to_postgres_corso_docenti(all_docenti, db_config, TABLE_NAME_CORSO_DOCENTI)

    else:
        print("ERRORE: Nessun dato ricevuto dall'endpoint 'corsi'.")
