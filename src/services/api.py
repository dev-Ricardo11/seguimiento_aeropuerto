from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import pyodbc
import os
import re
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="KONTROL TIQUETES API",
    version="3.1.0"
)

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class TiqueteEstadoUpdate(BaseModel):
    id_asesor: str
    
    id_observacion: Optional[str] = None
    id_silla: Optional[str] = None
    id_cuenta: Optional[str] = None
    id_hora: str

class Fechas(BaseModel):
    fecha_inicio: str
    fecha_fin: str


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
    # Para Windows Auth no se requiere username
    if not all([DB_CONFIG['server'], DB_CONFIG['database']]):
        raise ValueError("Faltan variables de entorno de base de datos")

    server = DB_CONFIG['server']
    use_windows_auth = DB_CONFIG['use_windows_auth']

    # Formatear el servidor según la sintaxis
    if ',' in server and not server.split(',')[1].isdigit():
        # Formato: IP,instancia -> IP\instancia
        parts = server.split(',')
        server_formatted = f"{parts[0]}\\{parts[1]}"
    elif '\\' in server:
        # Ya tiene el formato correcto IP\instancia
        server_formatted = server
    else:
        # Solo IP o nombre del servidor
        server_formatted = f"{server},{DB_CONFIG['port']}"

    # Construir la cadena de conexión
    if use_windows_auth:
        # Windows Authentication (Trusted Connection)
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={server_formatted};"
            f"DATABASE={DB_CONFIG['database']};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
    else:
        # SQL Server Authentication
        if not all([DB_CONFIG['username'], DB_CONFIG['password']]):
            raise ValueError("Se requiere usuario y contraseña para SQL Authentication")
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={server_formatted};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            f"TrustServerCertificate=yes;"
        )


@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones a la base de datos"""
    conn = None
    try:
        conn_str = get_connection_string()
        
        import re
        # Mask password for logging
        # log_conn_str = re.sub(r'PWD=.*?;', 'PWD=******;', conn_str)
            
        conn = pyodbc.connect(conn_str)
        yield conn
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Error de configuración: {str(e)}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
    finally:
        if conn:
            conn.close()


def extraer_aerolinea_pnr(ds_pnr: str) -> Optional[str]:
    if not ds_pnr:
        return None

    match_operated = re.search(r'OPERATED BY[:/\s]+/?([A-Z][A-Z0-9\s]+?)(?:\s{2,}|$)', ds_pnr, re.IGNORECASE)
    if match_operated:
        aerolinea = match_operated.group(1).strip()
        aerolinea = re.sub(r'\s+', ' ', aerolinea)
        return aerolinea

    match_a = re.search(r'A-([A-Z][A-Z0-9]+)', ds_pnr)
    if match_a:
        return match_a.group(1).strip()

    match_amadeus = re.search(r';([A-Z]{2})\s+\d{4}\s+[A-Z]\s+[A-Z]', ds_pnr)
    if match_amadeus:
        return match_amadeus.group(1).strip()

    match_sabre_airline = re.search(r';([A-Z]{2})\s+\d+[A-Z]\s+', ds_pnr)
    if match_sabre_airline:
        return match_sabre_airline.group(1).strip()

    try:
        root = ET.fromstring(ds_pnr)
        ds_aero_code = root.find('.//ds_aero_code')
        if ds_aero_code is not None and ds_aero_code.text:
            return ds_aero_code.text.strip()
    except:
        pass

    return None

def extraer_telefono_pnr(ds_pnr: str) -> Optional[str]:
    if not ds_pnr:
        return None

    match_telepax = re.search(r'Telepax[:/\s]+(\d+)', ds_pnr, re.IGNORECASE)
    if match_telepax:
        return match_telepax.group(1).strip()

    match_digits_m = re.search(r'(\d{10,12})\s*-\s*M', ds_pnr, re.IGNORECASE)
    if match_digits_m:
        return match_digits_m.group(1).strip()

    match_phone = re.search(r'(\d{10,12})\s+-B', ds_pnr)
    if match_phone:
        return match_phone.group(1).strip()

    match_ssrctcm = re.search(r'SSR\s+CTCM\s+[A-Z]{2}\s+HK\d+/(\d+)', ds_pnr)
    if match_ssrctcm:
        return match_ssrctcm.group(1).strip()

    match_amadeus_phone = re.search(r'M-(\d{10,12})', ds_pnr)
    if match_amadeus_phone:
        return match_amadeus_phone.group(1).strip()

    try:
        root = ET.fromstring(ds_pnr)
        ds_pax_telefono = root.find('.//ds_pax_telefono')
        if ds_pax_telefono is not None and ds_pax_telefono.text:
            return ds_pax_telefono.text.strip()
    except:
        pass

    return None

def extraer_tiqueteador_pnr(ds_pnr: str) -> Optional[str]:
    if not ds_pnr:
        return None

    match_rm_asesor = re.search(r'RM\s+ASESOR/([A-Z\s]+?)(?:\s+RM|\n|$)', ds_pnr, re.IGNORECASE)
    if match_rm_asesor:
        return match_rm_asesor.group(1).strip()

    match_emisor = re.search(r'RM\s+XNET-EMISOR/([A-Z\s]+?)(?:\s+RM|\n|$)', ds_pnr, re.IGNORECASE)
    if match_emisor:
        return match_emisor.group(1).strip()

    match_aitan = re.search(r'AITAN([A-Z0-9]+)', ds_pnr)
    if match_aitan:
        return match_aitan.group(1).strip()

    return None

def limpiar_nombre_pasajero(nombre: str) -> str:
    if not nombre:
        return nombre

    prefijos = ['MR', 'MRS', 'MS', 'MISS', 'DR', 'MSTR', 'CHD', 'INF', 'ADT']
    nombre_limpio = nombre

    for prefijo in prefijos:
        nombre_limpio = re.sub(rf'\b{prefijo}\b', '', nombre_limpio, flags=re.IGNORECASE)

    nombre_limpio = ' '.join(nombre_limpio.split())

    return nombre_limpio.strip()

def determinar_tipo_gds(iden_gds: int) -> str:
    gds_map = {
        1: 'SABRE',
        2: 'AMADEUS',
        8: 'KONTROL'
    }
    return gds_map.get(iden_gds, f'GDS {iden_gds}')

def normalize_date(date_val):
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val.isoformat()
    # Try parsing custom format "Sep 30 2025 12:55PM"
    try:
        # Check if matches standard ISO first
        try:
             return datetime.fromisoformat(str(date_val)).isoformat()
        except:
             pass
        
        # Parse custom format
        # Example: Sep 30 2025 12:55PM
        dt = datetime.strptime(str(date_val).strip(), "%b %d %Y %I:%M%p")
        return dt.isoformat()
    except Exception:
        # Return original if parsing fails (fallback)
        return date_val

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
def read_root():
    return {
        "message": "KONTROL TIQUETES API v3.1.0",
        "status": "active",
        "database": DB_CONFIG['database']
    }

@app.get("/health")
def health_check():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return {
                "status": "healthy",
                "database": "connected",
                "name": DB_CONFIG['database'],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/auth/login")
def login(credentials: dict):
    usuario = credentials.get('correo', '').strip()
    password = credentials.get('password', '').strip()

    print(f"\n🔐 Intento de login para: {usuario}")
    
    if not usuario or not password:
        return JSONResponse(status_code=400, content={"detail": "Usuario y contraseña requeridos"})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Consultar usuario y validar contraseña en una sola query
        cursor.execute("""
            SELECT id, email, nombre_completo, rol
            FROM dbo.usuarios
            WHERE email = ? 
            AND [contraseña] = HASHBYTES('SHA2_256', CAST(? AS VARCHAR))
        """, (usuario, password))

        user = cursor.fetchone()

        if not user:
            print(f"❌ Login fallido para: {usuario}")
            return JSONResponse(status_code=401, content={"detail": "Usuario o contraseña incorrectos"})
        
        print(f"✓ Login exitoso para: {user[1]}")

        return {
            "success": True,
            "message": "Login exitoso",
            "user": {
                "id": user[0],
                "email": user[1],
                "nombre": user[2],
                "rol": user[3]
            }
        }

@app.post("/ReservasGDS")
def get_reservas(fechas: Optional[Fechas] = None):
    """
    Obtiene registros de VueloIDA y VueloREG para el dashboard administrativo.
    """
    try:
        usar_filtro_fechas = fechas is not None and fechas.fecha_inicio and fechas.fecha_fin
        
        sucursales = {
            "I0W3": "Locales BOG",
            "NT3H": "NEPS",
            "MZ4C": "GRUPOS",
            "7C0A": "VACACIONAL",
            "7OMF": "Sucursal BAQ",
            "W5AA": "Sucursal CLO",
            "MANUAL": "REGISTRO MANUAL"
        }

        # Query base para IDA
        query_ida = """
            SELECT 
                cd_sucursal,
                id_documento as cd_codigo,
                id_tiqueteador as cd_tiqueteador,
                id_observacion as ds_observaciones,
                id_cuenta,
                id_hora,
                dt_salida as fecha_vuelo
            FROM dbo.VueloIDA
        """
        
        # Query base para REG
        query_reg = """
            SELECT 
                cd_sucursal,
                id_documento as cd_codigo,
                id_tiqueteador as cd_tiqueteador,
                id_observacion as ds_observaciones,
                id_cuenta,
                id_hora,
                dt_llegada as fecha_vuelo
            FROM dbo.VueloREG
        """

        full_query = f"""
            SELECT * FROM (
                ({query_ida})
                UNION ALL
                ({query_reg})
            ) as Combined
        """

        if usar_filtro_fechas:
            full_query += f" WHERE fecha_vuelo >= '{fechas.fecha_inicio}' AND fecha_vuelo <= '{fechas.fecha_fin} 23:59:59'"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(full_query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        result = []
        for row in rows:
            record = dict(zip(columns, row))
            
            # Map Sucursal
            cd = str(record.get("cd_sucursal", "")).strip().upper()
            nombre_sucursal = sucursales.get(cd, "OTRAS SUCURSALES")
            record["CodigoSucursal"] = cd
            record["NombreSucursal"] = nombre_sucursal
            record["Sucursal"] = f"{cd} - {nombre_sucursal}"
            
            # Map id_cuenta_str for the chart
            record["id_cuenta_str"] = str(record.get("id_cuenta") or "SIN CUENTA")
            
            result.append(record)

        return {
            "success": True,
            "data": result,
            "total": len(result),
            "filtrado_por_fechas": usar_filtro_fechas
        }

    except Exception as e:
        import traceback
        print(f"❌ ERROR en ReservasGDS: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al consultar reservas: {str(e)}")



class TiqueteCreate(BaseModel):
    ds_records: str
    cd_tiquete: str
    ds_paxname: str
    nombre_tiqueteador: Optional[str] = None
    ds_itinerario: Optional[str] = None
    dt_salida: Optional[str] = None
    tipo_reserva: Optional[str] = None
    id_asesor: Optional[str] = None
    id_observacion: Optional[str] = None
    id_silla: Optional[str] = None
    id_cuenta: Optional[str] = None
    tipo_vuelo: Optional[str] = "IDA"  # Default to IDA if not specified

@app.post("/TiquetesDocumentos")
def create_tiquete(tiquete: TiqueteCreate):
    try:
        if not tiquete.cd_tiquete:
            raise HTTPException(status_code=400, detail="El código de tiquete es obligatorio")

        target_table = "VueloIDA"
        if tiquete.tipo_vuelo and (tiquete.tipo_vuelo.upper() == 'REG' or 'DEVUELTA' in tiquete.tipo_vuelo.upper()):
            target_table = "VueloREG"

        # Separate Name Logic if needed, for now using ds_paxname for all
        # columns in DB: ds_paxname, ds_paxprefix, ds_paxape
        # We will split simply by space for now or put all in ds_paxname
        
        col_date = "dt_salida" if target_table == "VueloIDA" else "dt_llegada"
        
        # Prepare date - normalize for SQL Server (no 'T' separator)
        date_val = None
        if tiquete.dt_salida:
             try:
                 # Ensure we have YYYY-MM-DD HH:MM:SS format
                 dt_temp = tiquete.dt_salida.replace('T', ' ')
                 if len(dt_temp) == 16: # handles YYYY-MM-DD HH:MM
                     dt_temp += ":00"
                 date_val = dt_temp
             except:
                 date_val = tiquete.dt_salida

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute(f"SELECT id_documento FROM dbo.{target_table} WHERE id_documento = ?", (tiquete.cd_tiquete,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"El tiquete {tiquete.cd_tiquete} ya existe en {target_table}")

            # Mandatory columns for manual entries:
            # ds_paxprefix, ds_paxape, iden_gds, ds_PNR, cd_sucursal
            
            query = f"""
                INSERT INTO dbo.{target_table} (
                    id_documento,
                    ds_records,
                    ds_paxname,
                    ds_paxprefix,
                    ds_paxape,
                    iden_gds,
                    ds_PNR,
                    cd_sucursal,
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, 'Presencial')
            """
            
            cursor.execute(query, (
                tiquete.cd_tiquete,
                tiquete.ds_records,
                tiquete.ds_paxname,
                '', # ds_paxprefix
                '', # ds_paxape
                '8', # iden_gds (KONTROL para manual)
                '', # ds_PNR
                'MANUAL', # cd_sucursal
                tiquete.nombre_tiqueteador,
                tiquete.ds_itinerario,
                date_val,
                tiquete.id_asesor,
                tiquete.id_observacion,
                tiquete.id_silla,
                tiquete.id_cuenta,
                datetime.now().strftime("%H:%M:%S")
            ))
            conn.commit()
            
            return {"success": True, "message": f"Tiquete creado en {target_table}", "cd_tiquete": tiquete.cd_tiquete}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creando tiquete: {str(e)}")

@app.get("/TiquetesDocumentos")
def get_tiquetes_documentos(
    limit: int = Query(1000, le=1000),
    tipo_vuelo: Optional[str] = Query(None, description="Filtro por tipo de vuelo: 'IDA' o 'REG'")
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Base Sub-Queries
            select_ida = """
                SELECT 
                    id_documento as cd_tiquete,
                    ds_paxname,
                    ds_paxprefix,
                    ds_paxape,
                    ds_itinerario,
                    dt_salida,
                    NULL as dt_llegada,
                    'IDA' as tipo_vuelo,
                    ds_records,
                    ds_PNR,
                    id_tiqueteador as nombre_tiqueteador, -- Maps to name directly based on user input
                    id_asesor as cd_tiqueteador,
                    iden_gds,
                    id_observacion as ds_observaciones,
                    id_asesor,
                    id_observacion,
                    id_estado,
                    id_silla,
                    id_cuenta,
                    id_hora,
                    id_atencion
                FROM dbo.VueloIDA
            """

            select_reg = """
                SELECT 
                    id_documento as cd_tiquete,
                    ds_paxname,
                    ds_paxprefix,
                    ds_paxape,
                    ds_itinerario,
                    NULL as dt_salida,
                    dt_llegada,
                    'REG' as tipo_vuelo,
                    ds_records,
                    ds_PNR,
                    id_tiqueteador as nombre_tiqueteador,
                    id_asesor as cd_tiqueteador,
                    iden_gds,
                    id_observacion as ds_observaciones,
                    id_asesor,
                    id_observacion,
                    id_estado,
                    id_silla,
                    id_cuenta,
                    id_hora,
                    id_atencion
                FROM dbo.VueloREG
            """

            # Determine query based on filter
            inner_query = ""
            if tipo_vuelo:
                val = tipo_vuelo.upper()
                if val == 'IDA':
                    inner_query = select_ida
                elif val == 'REG' or 'DEVUELTA' in val:
                    inner_query = select_reg
                else:
                    inner_query = f"{select_ida} UNION ALL {select_reg}"
            else:
                inner_query = f"{select_ida} UNION ALL {select_reg}"

            query = f"""
                SELECT TOP ({limit}) * FROM (
                    {inner_query}
                ) AS TiquetesUnificados
                ORDER BY COALESCE(dt_salida, dt_llegada) DESC
            """


            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Verify columns from description to map correctly if needed
            # col_names = [column[0] for column in cursor.description]

            tiquetes = []
            for row in rows:
                # row indexes based on SELECT list above:
                # 0: cd_tiquete
                # 1: ds_paxname
                # 2: ds_paxprefix
                # 3: ds_paxape
                # 4: ds_itinerario
                # 5: fecha_vuelo
                # 6: tipo_vuelo
                # 7: ds_records
                # 8: ds_PNR
                # 9: nombre_tiqueteador (id_tiqueteador)
                # 10: cd_tiqueteador (id_asesor)
                # 11: iden_gds
                # 12: ds_observaciones (id_observacion)
                # 13: id_asesor
                # 14: id_observacion
                # 15: id_estado
                # 16: id_silla
                # 17: id_cuenta
                # 18: id_hora
                # 19: id_atencion

                ds_pnr_text = row[9]
                aerolinea = extraer_aerolinea_pnr(ds_pnr_text)
                telefono = extraer_telefono_pnr(ds_pnr_text)
                tiqueteador_pnr = extraer_tiqueteador_pnr(ds_pnr_text)

                # Get name directly from the table column `id_tiqueteador`
                nombre_tiqueteador = row[10]

                # Fallback logic (optional, keeping for robustness if column is empty)
                if not nombre_tiqueteador:
                     # Try looking up by id_asesor (row[10])
                    if row[10]:
                        try:
                            cursor.execute("SELECT ds_nombre FROM Tiqueteadores WHERE cd_codigo = ?", (row[10],))
                            tiq_result = cursor.fetchone()
                            if tiq_result:
                                nombre_tiqueteador = tiq_result[0]
                        except:
                            pass
                
                if not nombre_tiqueteador and tiqueteador_pnr:
                    nombre_tiqueteador = tiqueteador_pnr

                tipo_reserva = determinar_tipo_gds(int(row[11])) if row[11] and str(row[11]).isdigit() else None

                # Logic for status
                estado_bd = row[15]
                id_asesor_val = row[13]
                estado = 'Procesado' if (estado_bd == 'Procesado' or id_asesor_val) else 'Pendiente'

                paxname_limpio = limpiar_nombre_pasajero(row[1]) if row[1] else row[1]
                paxape_limpio = limpiar_nombre_pasajero(row[3]) if row[3] else row[3]

                tiquete = {
                    'cd_tiquete': row[0],
                    'ds_paxname': paxname_limpio,
                    'ds_paxprefix': row[2],
                    'ds_paxape': paxape_limpio,
                    'ds_itinerario': row[4],
                    'dt_salida': normalize_date(row[5]),
                    'dt_llegada': normalize_date(row[6]),
                    'tipo_vuelo': row[7],
                    'ds_records': row[8],
                    'aerolinea': aerolinea,
                    'telefono': telefono,
                    'cd_tiqueteador': row[11],
                    'nombre_tiqueteador': nombre_tiqueteador,
                    'iden_gds': row[12],
                    'tipo_reserva': tipo_reserva,
                    'ds_observaciones': row[13],
                    'id_asesor': row[14],
                    'id_observacion': row[15],
                    'id_estado': estado,
                    'id_silla': row[17],
                    'id_cuenta': row[18],
                    'id_hora': row[19],
                    'id_atencion': row[20]
                }
                tiquetes.append(tiquete)

            return {
                "total": len(tiquetes),
                "tiquetes": tiquetes
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/TiquetesDocumentos/estadisticas")
def get_estadisticas():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN id_asesor IS NULL THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN id_asesor IS NOT NULL THEN 1 ELSE 0 END) as procesados
                FROM (
                    SELECT id_asesor FROM dbo.VueloIDA
                    UNION ALL
                    SELECT id_asesor FROM dbo.VueloREG
                ) as Combined
            """)

            row = cursor.fetchone()

            return {
                "totalTiquetes": row[0] or 0,
                "tiquetesPendientes": row[1] or 0,
                "tiquetesProcesados": row[2] or 0,
                "fechaActualizacion": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/TiquetesDocumentos/{cd_tiquete}")
def get_tiquete_documento(cd_tiquete: str):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Helper to query a table
            def query_table(table_name):
                # Determinar columnas de fecha según la tabla
                col_salida = "dt_salida" if table_name == "VueloIDA" else "NULL as dt_salida"
                col_llegada = "dt_llegada" if table_name == "VueloREG" else "NULL as dt_llegada"

                query = f"""
                    SELECT
                        id_documento as cd_tiquete,
                        ds_paxname,
                        ds_paxprefix,
                        ds_paxape,
                        ds_itinerario,
                        {col_salida},
                        {col_llegada},
                        ds_records,
                        ds_PNR,
                        id_tiqueteador as nombre_tiqueteador,
                        id_asesor as cd_tiqueteador,
                        iden_gds,
                        id_observacion as ds_observaciones,
                        id_asesor,
                        id_observacion,
                        id_estado,
                        id_silla,
                        id_cuenta,
                        id_hora,
                        id_atencion
                    FROM dbo.{table_name}
                    WHERE id_documento = ?
                """
                cursor.execute(query, (cd_tiquete.strip(),))
                return cursor.fetchone()

            # Try IDA
            row = query_table("VueloIDA")
            table_source = "IDA"
            
            # If not found, try REG
            if not row:
                row = query_table("VueloREG")
                table_source = "REG"

            if not row:
                raise HTTPException(status_code=404, detail=f"Tiquete {cd_tiquete} no encontrado")

            ds_pnr_text = row[9]
            aerolinea = extraer_aerolinea_pnr(ds_pnr_text)
            telefono = extraer_telefono_pnr(ds_pnr_text)
            tiqueteador_pnr = extraer_tiqueteador_pnr(ds_pnr_text)

            nombre_tiqueteador = row[10]
            
            # Fallback logic
            if not nombre_tiqueteador:
                if row[10] and len(row) > 10: # Check just in case
                    try:
                        cursor.execute("SELECT ds_nombre FROM Tiqueteadores WHERE cd_codigo = ?", (row[10],))
                        tiq_result = cursor.fetchone()
                        if tiq_result:
                            nombre_tiqueteador = tiq_result[0]
                    except:
                        pass

            if not nombre_tiqueteador and tiqueteador_pnr:
                nombre_tiqueteador = tiqueteador_pnr

            tipo_reserva = determinar_tipo_gds(int(row[12])) if row[12] and str(row[12]).isdigit() else None
            
            estado_bd = row[16]
            id_asesor_val = row[14]
            estado = 'Procesado' if (estado_bd == 'Procesado' or id_asesor_val) else 'Pendiente'

            paxname_limpio = limpiar_nombre_pasajero(row[1]) if row[1] else row[1]
            paxape_limpio = limpiar_nombre_pasajero(row[3]) if row[3] else row[3]

            tiquete = {
                'cd_tiquete': row[0],
                'ds_paxname': paxname_limpio,
                'ds_paxprefix': row[2],
                'ds_paxape': paxape_limpio,
                'ds_itinerario': row[4],
                'dt_salida': normalize_date(row[5]),
                'dt_llegada': normalize_date(row[6]),
                'tipo_vuelo': table_source,
                'ds_records': row[7],
                'ds_pnr_text': row[9],
                'aerolinea': aerolinea,
                'telefono': telefono,
                'cd_tiqueteador': row[11],
                'nombre_tiqueteador': nombre_tiqueteador,
                'iden_gds': row[12],
                'tipo_reserva': tipo_reserva,
                'ds_observaciones': row[13],
                'id_asesor': row[14],
                'id_observacion': row[15],
                'id_estado': estado,
                'id_silla': row[17],
                'id_cuenta': row[18],
                'id_hora': row[19],
                'id_atencion': row[20]
            }

            return {"tiquete": tiquete}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/TiquetesDocumentos/{cd_tiquete}/estado")
def update_tiquete_estado(cd_tiquete: str, data: TiqueteEstadoUpdate):
    try:
        cd_tiquete = cd_tiquete.strip()

        print(f"\n📥 Actualizando tiquete: {cd_tiquete}")
        
        if not data.id_asesor.strip():
            return JSONResponse(status_code=400, content={"detail": "El campo 'id_asesor' no puede estar vacío"})

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Try updating VueloIDA first
            cursor.execute("""
                UPDATE dbo.VueloIDA
                SET id_asesor = ?,
                    id_observacion = ?,
                    id_estado = 'Procesado',
                    id_silla = ?,
                    id_cuenta = ?,
                    id_hora = ?
                WHERE id_documento = ?
            """, (
                data.id_asesor.strip(),
                data.id_observacion.strip() if data.id_observacion else None,
                data.id_silla.strip() if data.id_silla else None,
                data.id_cuenta.strip() if data.id_cuenta else None,
                data.id_hora,
                cd_tiquete
            ))
            
            rows_affected = cursor.rowcount
            
            # If not found in IDA, try REG
            if rows_affected == 0:
                cursor.execute("""
                    UPDATE dbo.VueloREG
                    SET id_asesor = ?,
                        id_observacion = ?,
                        id_estado = 'Procesado',
                        id_silla = ?,
                        id_cuenta = ?,
                        id_hora = ?
                    WHERE id_documento = ?
                """, (
                    data.id_asesor.strip(),
                    data.id_observacion.strip() if data.id_observacion else None,
                    data.id_silla.strip() if data.id_silla else None,
                    data.id_cuenta.strip() if data.id_cuenta else None,
                    data.id_hora,
                    cd_tiquete
                ))
                rows_affected = cursor.rowcount

            if rows_affected == 0:
                return JSONResponse(status_code=404, content={"detail": f"Tiquete {cd_tiquete} no encontrado"})

            print(f"🔢 Filas actualizadas: {rows_affected}")
            conn.commit()
            print("✅ Commit realizado correctamente")

            return {
                "success": True,
                "message": "Tiquete actualizado correctamente",
                "cd_tiquete": cd_tiquete
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.put("/TiquetesDocumentos/{cd_tiquete}/atencion")
def update_tiquete_atencion(cd_tiquete: str, data: dict):
    """
    Actualiza solo el tipo de atención (Presencial/Virtual) sin cambiar el estado
    """
    try:
        cd_tiquete = cd_tiquete.strip()
        id_atencion = data.get('id_atencion', '').strip()

        if not id_atencion or id_atencion not in ['Presencial', 'Virtual']:
            return JSONResponse(status_code=400, content={"detail": "El campo 'id_atencion' debe ser 'Presencial' o 'Virtual'"})

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Try IDA
            cursor.execute("""
                UPDATE dbo.VueloIDA
                SET id_atencion = ?
                WHERE id_documento = ?
            """, (id_atencion, cd_tiquete))
            
            rows_affected = cursor.rowcount
            
            # Try REG if not found
            if rows_affected == 0:
                cursor.execute("""
                    UPDATE dbo.VueloREG
                    SET id_atencion = ?
                    WHERE id_documento = ?
                """, (id_atencion, cd_tiquete))
                rows_affected = cursor.rowcount

            if rows_affected == 0:
                return JSONResponse(status_code=404, content={"detail": f"Tiquete {cd_tiquete} no encontrado"})

            conn.commit()

            return {
                "success": True,
                "message": f"Tipo de atención actualizado a {id_atencion}",
                "cd_tiquete": cd_tiquete,
                "id_atencion": id_atencion
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)