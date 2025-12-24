
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
            print(f"\n--- Checking {table} ---")
            cursor.execute(f"SELECT COUNT(*) FROM dbo.{table}")
            count = cursor.fetchone()[0]
            print(f"Total Rows: {count}")
            
            if count > 0:
                print("Sample Data:")
                cursor.execute(f"SELECT TOP 3 * FROM dbo.{table}")
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    print(dict(zip(columns, row)))

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
