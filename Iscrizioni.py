import requests
import psycopg2
from psycopg2 import Error
from psycopg2.extras import execute_values
from datetime import datetime
#ciao
# --- CONFIGURAZIONE GLOBALE ---
print("Inizio configurazione per l'ETL dell'endpoint 'iscrizioni'...")

API_KEY_VALUE = 'key_e2op232O' # Assicurati che questa key sia valida
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
ISCRIZIONI_ENDPOINT = 'iscrizioni' # Endpoint specifico per iscrizioni
TABLE_NAME_ISCRIZIONI = 'iscrizioni' # Nome della tabella nel tuo DB

# Anni accademici da cui prendere i dati - Aggiornato con il 2024
ANNI_ACCADEMICI = [2020, 2021, 2022, 2023, 2024] # Già includeva 2024

print("Configurazione completata.")
print("-" * 30)

# --- FUNZIONI UTILI ---

def parse_date(date_str):
    """Converte una stringa data in oggetto date, gestendo vari formati."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

def parse_boolean(value):
    """Converte un valore in booleano."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'y', 'yes')
    if isinstance(value, int):
        return value == 1
    return False # Default a False per valori non riconosciuti o None

def parse_int_with_none(value):
    """Converte un valore in intero, restituendo None se None o non numerico."""
    if value is None or (isinstance(value, str) and value.strip() == ''):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def extract_data_from_api(endpoint_url, headers, params=None):
    """Estrae i dati dall'API specificata, gestendo errori HTTP e JSON."""
    print(f"Estrazione da: {endpoint_url} con parametri {params}")
    try:
        response = requests.get(endpoint_url, headers=headers, params=params)
        response.raise_for_status() # Solleva un'eccezione per codici di stato HTTP 4xx/5xx
        raw_data = response.json()

        if isinstance(raw_data, dict) and 'data' in raw_data:
            data_list = raw_data['data']
        elif isinstance(raw_data, list):
            data_list = raw_data
        else:
            print(f"   Avviso: Struttura inattesa della risposta API per {endpoint_url}. Trovato tipo: {type(raw_data)}. Contenuto: {raw_data}")
            return []
        
        print(f"   Estrazione completata: {len(data_list)} record.")
        return data_list
    except requests.exceptions.RequestException as e:
        print(f"   ERRORE nella richiesta API: {e}")
        return None
    except ValueError as e:
        print(f"   ERRORE parsing JSON: {e}")
        print(f"   Contenuto della risposta non JSON (primi 200 caratteri): {response.text[:200]}...")
        return None

def get_db_connection(config):
    """Restituisce una connessione al database PostgreSQL."""
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

# --- FUNZIONI ETL SPECIFICHE PER ISCRIZIONI ---

def transform_data_for_iscrizioni(raw_api_data):
    """
    Trasforma i dati grezzi dell'API 'iscrizioni' nel formato adatto per la tabella 'iscrizioni'.
    Mappa i nomi dei campi API ai nomi delle colonne del DB.
    """
    print("Inizio trasformazione dati per 'iscrizioni'...")
    transformed_records = []
    seen_keys_local = set() 

    for item in raw_api_data:
        if not isinstance(item, dict):
            print(f"   Avviso: Trovato elemento non dizionario ({type(item)}) durante la trasformazione 'iscrizioni'. Valore: '{item}'. Saltando.")
            continue
        try:
            id_alunno = str(item.get("idAlunno")) if item.get("idAlunno") is not None else ''
            cognome = item.get("Cognome", "")
            nome = item.get("Nome", "")
            cf = item.get("CodiceFiscale", "") # Assumo "CodiceFiscale" dall'API per "cf"
            data_nascita = parse_date(item.get("DataNascita"))
            sesso = item.get("Sesso", "") 
            email = item.get("Email", "")
            voto_diploma = str(item.get("VotoDiploma", "")) 
            alunno_attivo = parse_boolean(item.get("AlunnoAttivo"))
            ritirato_corso = parse_boolean(item.get("RitiratoCorso")) 
            
            id_corso_anno = parse_int_with_none(item.get("idCorsoAnno")) 
            
            codice_corso = item.get("CodiceCorso", "")
            corso = item.get("Corso", "")
            voto_pagella = str(item.get("VotoPagella", ""))
            credito = str(item.get("Credito", ""))
            voto_ammissione_esame = str(item.get("VotoAmmissioneEsame", ""))
            esito_finale = str(item.get("EsitoFinale", ""))

            pk_key = (id_alunno, id_corso_anno) 
            if pk_key in seen_keys_local:
                continue 
            seen_keys_local.add(pk_key)

            transformed_records.append((
                id_alunno,
                cognome,
                nome,
                cf,
                data_nascita,
                sesso,        
                email,
                voto_diploma,
                alunno_attivo,
                ritirato_corso, 
                id_corso_anno,
                codice_corso,
                corso,
                voto_pagella,
                credito,
                voto_ammissione_esame,
                esito_finale
            ))
        except Exception as e:
            print(f"   ERRORE durante la trasformazione di un record 'iscrizioni' (idAlunno: {item.get('idAlunno', 'N/A')}, idCorsoAnno: {item.get('idCorsoAnno', 'N/A')}): {e}")
            continue

    print(f"   Trasformazione completata: {len(transformed_records)} record per 'iscrizioni'.")
    return transformed_records

def load_data_to_postgres_iscrizioni(data_to_load, db_config, table_name):
    """
    Carica i dati trasformati nella tabella 'iscrizioni' del database PostgreSQL.
    Crea la tabella se non esiste e gestisce l'UPSERT.
    """
    print(f"Inizio caricamento dati nella tabella '{table_name}'...")
    if not data_to_load:
        print(f"   Nessun dato da caricare nella tabella '{table_name}'.")
        return

    conn = get_db_connection(db_config)
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            # Crea la tabella se non esiste, con la chiave primaria composita (idalunno, idcorsoanno)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    idalunno VARCHAR(255),
                    cognome VARCHAR(255),
                    nome VARCHAR(255),
                    cf VARCHAR(255),
                    datanascita DATE,
                    sesso VARCHAR(10), 
                    email VARCHAR(255),
                    votodiploma VARCHAR(255),
                    alunnoattivo BOOLEAN,
                    ritiratocorso BOOLEAN, 
                    idcorsoanno INTEGER,
                    codicecorso VARCHAR(255),
                    corso TEXT,
                    votopagella VARCHAR(255),
                    credito VARCHAR(255),
                    votoammissioneesame VARCHAR(255),
                    esitofinale VARCHAR(255),
                    PRIMARY KEY (idalunno, idcorsoanno) -- Chiave primaria composita
                );
            """)
            conn.commit()
            print(f"   Tabella '{table_name}' creata o già esistente.")

            # Query INSERT/UPSERT
            insert_query = f"""
                INSERT INTO {table_name} (
                    idalunno, cognome, nome, cf, datanascita, sesso, email, votodiploma,
                    alunnoattivo, ritiratocorso, idcorsoanno, codicecorso, corso, votopagella,
                    credito, votoammissioneesame, esitofinale
                )
                VALUES %s
                ON CONFLICT (idalunno, idcorsoanno) DO UPDATE SET 
                    cognome = EXCLUDED.cognome,
                    nome = EXCLUDED.nome,
                    cf = EXCLUDED.cf,
                    datanascita = EXCLUDED.datanascita,
                    sesso = EXCLUDED.sesso, 
                    email = EXCLUDED.email,
                    votodiploma = EXCLUDED.votodiploma,
                    alunnoattivo = EXCLUDED.alunnoattivo,
                    ritiratocorso = EXCLUDED.ritiratocorso, 
                    codicecorso = EXCLUDED.codicecorso,
                    corso = EXCLUDED.corso,
                    votopagella = EXCLUDED.votopagella,
                    credito = EXCLUDED.credito,
                    votoammissioneesame = EXCLUDED.votoammissioneesame,
                    esitofinale = EXCLUDED.esitofinale;
            """
            execute_values(cur, insert_query, data_to_load)
            conn.commit()
            print(f"   Caricamento/Aggiornamento completato: {len(data_to_load)} record in '{table_name}'.")

    except Error as e:
        print(f"   ERRORE durante il caricamento nel database per '{table_name}': {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print(f"   Connessione al database per '{table_name}' chiusa.")
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

    all_iscrizioni_records = []
    final_deduplicated_keys = set() 

    print("Inizio recupero dati iscrizioni per anni accademici specifici...")

    for anno_accademico in ANNI_ACCADEMICI:
        print(f"\nElaborazione iscrizioni per Anno Accademico: {anno_accademico}")
        
        params = {"AnnoAccademico": anno_accademico}
        # Chiamata diretta all'endpoint ISCRIZIONI con il parametro AnnoAccademico
        iscrizioni_data = extract_data_from_api(f"{BASE_API_URL}{ISCRIZIONI_ENDPOINT}", HEADERS, params)

        if iscrizioni_data:
            transformed_for_year = transform_data_for_iscrizioni(iscrizioni_data)
            
            for record in transformed_for_year:
                # idalunno è indice 0, idcorsoanno è indice 10 nella tupla 'record'
                current_pk = (record[0], record[10]) 
                
                if current_pk not in final_deduplicated_keys:
                    final_deduplicated_keys.add(current_pk)
                    all_iscrizioni_records.append(record)
            
        else:
            print(f"   Nessun dato ricevuto per 'iscrizioni' per l'Anno Accademico: {anno_accademico}.")
    
    print(f"\nTotale record unici trasformati e deduplicati da tutti gli anni accademici: {len(all_iscrizioni_records)}")
    load_data_to_postgres_iscrizioni(all_iscrizioni_records, db_config, TABLE_NAME_ISCRIZIONI)

    print("\nProcesso ETL complessivo per 'iscrizioni' completato.")

