
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'server': os.getenv("DB_SERVER"),
    'database': os.getenv("DB_DATABASE"),
    'username': os.getenv("DB_USER", ""),
    'password': os.getenv("DB_PASSWORD", ""),
    'port': os.getenv("DB_PORT", "1433"),
    'driver': os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    'use_windows_auth': os.getenv("USE_WINDOWS_AUTH", "true").lower() == "true"
}

def get_connection_string():
    server = DB_CONFIG['server']
    if ',' in server and not server.split(',')[1].isdigit():
        parts = server.split(',')
        server_formatted = f"{parts[0]}\\{parts[1]}"
    elif '\\' in server:
        server_formatted = server
    else:
        server_formatted = f"{server},{DB_CONFIG['port']}"

    conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={server_formatted};DATABASE={DB_CONFIG['database']};"
    if DB_CONFIG['use_windows_auth']:
        conn_str += "Trusted_Connection=yes;TrustServerCertificate=yes;"
    else:
        conn_str += f"UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};TrustServerCertificate=yes;"
    return conn_str

try:
    conn = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()

    print("--- All Users and Roles ---")
    cursor.execute("SELECT email, rol FROM dbo.usuarios")
    for row in cursor.fetchall():
        print(f"Email: '{row[0]}', Role: '{row[1]}'")
    
    conn.close()

except Exception as e:
    print(f"Error: {e}")
