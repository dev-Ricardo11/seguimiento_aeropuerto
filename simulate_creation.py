
import pyodbc
import os
from datetime import datetime
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

# Data from screenshot
data = {
    "cd_tiquete": "Prueba2",
    "ds_records": "Prueba2",
    "ds_paxname": "Ricardo Ramirez",
    "nombre_tiqueteador": "Prueba2",
    "ds_itinerario": "BOG - MDE",
    "dt_salida": "2025-12-27T07:52",
    "id_asesor": "Wendy Cantillo Maury",
    "id_observacion": "Prueba2",
    "id_silla": "Prueba 2",
    "id_cuenta": "Prueba 2",
    "tipo_vuelo": "IDA"
}

try:
    print(f"Simulating creation for {data['cd_tiquete']}...")
    target_table = "VueloIDA"
    col_date = "dt_salida"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute(f"SELECT id_documento FROM dbo.{target_table} WHERE id_documento = ?", (data["cd_tiquete"],))
        if cursor.fetchone():
            print(f"ERROR: El tiquete {data['cd_tiquete']} ya existe en {target_table}")
        else:
            query = f"""
                INSERT INTO dbo.{target_table} (
                    id_documento,
                    ds_records,
                    ds_paxname,
                    id_tiqueteador,
                    ds_itinerario,
                    {col_date},
                    id_asesor,
                    id_observacion,
                    id_silla,
                    id_cuenta,
                    id_estado,
                    id_hora,
                    id_atencion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, 'Presencial')
            """
            
            params = (
                data["cd_tiquete"],
                data["ds_records"],
                data["ds_paxname"],
                data["nombre_tiqueteador"],
                data["ds_itinerario"],
                data["dt_salida"],
                data["id_asesor"],
                data["id_observacion"],
                data["id_silla"],
                data["id_cuenta"],
                datetime.now().strftime("%H:%M:%S")
            )
            
            print(f"Executing query with params: {params}")
            cursor.execute(query, params)
            conn.commit()
            print("SUCCESS: Tiquete creado exitosamente")

except Exception as e:
    import traceback
    print("--- TRACEBACK ---")
    traceback.print_exc()
    print(f"--- ERROR: {str(e)} ---")
