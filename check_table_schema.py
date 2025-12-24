
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "1433")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    use_windows_auth = os.getenv("USE_WINDOWS_AUTH", "true").lower() == "true"

    if ',' in server and not server.split(',')[1].isdigit():
        parts = server.split(',')
        server_formatted = f"{parts[0]}\\{parts[1]}"
    elif '\\' in server:
        server_formatted = server
    else:
        server_formatted = f"{server},{port}"

    conn_str = f"DRIVER={{{driver}}};SERVER={server_formatted};DATABASE={database};"
    if use_windows_auth:
        conn_str += "Trusted_Connection=yes;TrustServerCertificate=yes;"
    else:
        conn_str += f"UID={username};PWD={password};TrustServerCertificate=yes;"
    
    return pyodbc.connect(conn_str)

try:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for table in ["VueloIDA", "VueloREG"]:
            print(f"\n--- {table} Schema ---")
            cursor.execute(f"SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
            for row in cursor.fetchall():
                print(row)

except Exception as e:
    print(f"Error: {e}")
