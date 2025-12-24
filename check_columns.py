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
    conn_str = f"DRIVER={{{DB_CONFIG['driver']}}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};"
    if DB_CONFIG['use_windows_auth']:
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']};"
    return conn_str

try:
    conn = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'VueloIDA'")
    columns = [row[0] for row in cursor.fetchall()]
    print("Columns in VueloIDA:", columns)
    conn.close()
except Exception as e:
    print("Error:", e)
