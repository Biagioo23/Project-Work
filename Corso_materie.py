import requests
import psycopg2
from psycopg2 import Error
from psycopg2.extras import execute_values

# --- CONFIGURAZIONE ---
API_KEY_VALUE = 'key_e2op232O'
AUTH_HEADER = f'Bearer {API_KEY_VALUE}'

DB_CONFIG = {
    'host': 'databaseprojectwork.postgres.database.azure.com',
    'port': '5432',
    'dbname': 'projectwork',
    'user': 'jacopob',
    'password': 'BiagioJ$',
    'sslmode': 'require'
}

HEADERS = {
    'Authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

BASE_API_URL = 'https://api-pw25-grhhckd5abhdhccd.italynorth-01.azurewebsites.net/api/'
CORSI_ENDPOINT = 'corsi'
ORE_ALUNNO_ENDPOINT = 'ore_alunno'
TABLE_NAME = 'ore_alunno'

# --- FUNZIONI ---

def extract_data_from_api(endpoint_url, headers, params=None):
    try:
        response = requests.get(endpoint_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ERRORE richiesta API: {e}")
        return None

def get_db_connection(config):
    try:
        return psycopg2.connect(
            host=config['host'],
            port=config['port'],
            dbname=config['dbname'],
            user=config['user'],
            password=config['password'],
            sslmode=config['sslmode']
        )
    except Error as e:
        print(f"   ERRORE connessione DB: {e}")
        return None

def transform_data_ore_alunno(raw_data):
    print("   Trasformazione dati ore_alunno...")
    transformed = []
    seen_keys = set()

    for item in raw_data:
        try:
            id_alunno = str(item.get("idAlunno"))
            cognome = item.get("Cognome", "")
            nome = item.get("Nome", "")
            cf = item.get("CF", "")
            materia = item.get("Materia", "")
            ore_previste = int(item.get("OrePreviste", 0)) if str(item.get("OrePreviste", "")).isdigit() else 0
            ore_assenza_iniziali = int(item.get("OreAssenzaIniziali", 0)) if str(item.get("OreAssenzaIniziali", "")).isdigit() else 0
            ore_presenza_iniziali = int(item.get("OrePresenzaIniziali", 0)) if str(item.get("OrePresenzaIniziali", "")).isdigit() else 0
            minuti_presenza = int(item.get("MinutiPresenza", 0)) if str(item.get("MinutiPresenza", "")).isdigit() else 0
            minuti_lezione = int(item.get("MinutiLezione", 0)) if str(item.get("MinutiLezione", "")).isdigit() else 0
            voto_medio = float(item.get("VotoMedio", 0)) if str(item.get("VotoMedio", "")).replace('.', '', 1).isdigit() else 0.0

            key = (id_alunno, materia)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            transformed.append((
                id_alunno, cognome, nome, cf, materia,
                ore_previste, ore_assenza_iniziali, ore_presenza_iniziali,
                minuti_presenza, minuti_lezione, voto_medio
            ))

        except Exception as e:
            print(f"   ERRORE trasformazione record: {e}")
            continue

    print(f"   Totale trasformati: {len(transformed)}")
    return transformed

def load_data_to_postgres(data, config, table_name):
    print(f"Inizio caricamento nella tabella '{table_name}'...")
    if not data:
        print("   Nessun dato da caricare.")
        return

    conn = get_db_connection(config)
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id_alunno VARCHAR(255),
                    cognome VARCHAR(255),
                    nome VARCHAR(255),
                    cf VARCHAR(255),
                    materia VARCHAR(255),
                    ore_previste INTEGER,
                    ore_assenza_iniziali INTEGER,
                    ore_presenza_iniziali INTEGER,
                    minuti_presenza INTEGER,
                    minuti_lezione INTEGER,
                    voto_medio FLOAT,
                    PRIMARY KEY (id_alunno, materia)
                );
            """)
            conn.commit()
            print("   Tabella creata o già esistente.")

            insert_query = f"""
                INSERT INTO {table_name} (
                    id_alunno, cognome, nome, cf, materia,
                    ore_previste, ore_assenza_iniziali, ore_presenza_iniziali,
                    minuti_presenza, minuti_lezione, voto_medio
                ) VALUES %s
                ON CONFLICT (id_alunno, materia) DO UPDATE SET
                    cognome = EXCLUDED.cognome,
                    nome = EXCLUDED.nome,
                    cf = EXCLUDED.cf,
                    ore_previste = EXCLUDED.ore_previste,
                    ore_assenza_iniziali = EXCLUDED.ore_assenza_iniziali,
                    ore_presenza_iniziali = EXCLUDED.ore_presenza_iniziali,
                    minuti_presenza = EXCLUDED.minuti_presenza,
                    minuti_lezione = EXCLUDED.minuti_lezione,
                    voto_medio = EXCLUDED.voto_medio;
            """
            execute_values(cur, insert_query, data)
            conn.commit()
            print(f"   Caricati {len(data)} record nella tabella '{table_name}'.")
    except Error as e:
        print(f"   ERRORE durante il caricamento: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("   Connessione chiusa.\n")

# --- MAIN ---

if __name__ == "__main__":
    print("Estrazione idCorsoAnno da 'corsi'...")
    corsi_data = extract_data_from_api(f"{BASE_API_URL}{CORSI_ENDPOINT}", HEADERS)

    if not corsi_data:
        print("ERRORE: Impossibile ottenere idCorsoAnno.")
        exit()

    id_corsi = [str(corso["idCorsoAnno"]) for corso in corsi_data if corso.get("idCorsoAnno")]
    print(f"Trovati {len(id_corsi)} idCorsoAnno.")

    all_ore_alunno = []
    seen_keys = set()

    for i, id_corso in enumerate(id_corsi):
        print(f"Elaborazione corso {i+1}/{len(id_corsi)} - id: {id_corso}")
        alunno_data = extract_data_from_api(f"{BASE_API_URL}{ORE_ALUNNO_ENDPOINT}", HEADERS, {"idCorsoAnno": id_corso})
        if alunno_data:
            transformed = transform_data_ore_alunno(alunno_data)
            for row in transformed:
                key = (row[0], row[4])  # id_alunno + materia
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_ore_alunno.append(row)

    print(f"\nTotale record unici trasformati: {len(all_ore_alunno)}")
    load_data_to_postgres(all_ore_alunno, DB_CONFIG, TABLE_NAME)