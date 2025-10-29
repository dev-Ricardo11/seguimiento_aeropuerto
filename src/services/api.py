from fastapi import FastAPI, HTTPException, Query
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
    version="3.0.0"
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
    'username': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'port': os.getenv("DB_PORT", "1433"),
    'driver': os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
}

def get_connection_string():
    if not all([DB_CONFIG['server'], DB_CONFIG['database'], DB_CONFIG['username']]):
        raise ValueError("Faltan variables de entorno de base de datos")

    server = DB_CONFIG['server']

    if ',' in server and not server.split(',')[1].isdigit():
        parts = server.split(',')
        server_formatted = f"{parts[0]}\\{parts[1]}"
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={server_formatted};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            f"TrustServerCertificate=yes;"
        )
    elif '\\' in server:
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={server};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            f"TrustServerCertificate=yes;"
        )
    else:
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={server},{DB_CONFIG['port']};"
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

# ============================================
# FUNCIONES AUXILIARES
# ============================================

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

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
def read_root():
    return {
        "message": "KONTROL TIQUETES API v3.0.0",
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
    try:
        usuario = credentials.get('correo', '').strip()
        password = credentials.get('password', '').strip()

        if not usuario or not password:
            raise HTTPException(status_code=400, detail="Usuario y contraseña requeridos")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Email, Pass, Nombre, Login
                FROM Usuario
                WHERE Email = ? OR Login = ?
            """, (usuario, usuario))

            user = cursor.fetchone()

            if not user:
                raise HTTPException(status_code=401, detail="Usuario no encontrado")

            return {
                "success": True,
                "message": "Login exitoso",
                "user": {
                    "email": user[0],
                    "nombre": user[2],
                    "login": user[3]
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ReservasGDS")
def get_reservas(fechas: Optional[Fechas] = None):
    """
    Obtiene reservas GDS con o sin filtro de fechas.
    Si no se envían fechas, retorna todas las reservas (limitado a 10000).
    """
    try:
        usar_filtro_fechas = fechas is not None and hasattr(fechas, 'fecha_inicio')
 
        if usar_filtro_fechas:
            print(f"📅 Consultando reservas desde {fechas.fecha_inicio} hasta {fechas.fecha_fin}")
        else:
            print("📅 Consultando todas las reservas (sin filtro de fechas)")
 
        sucursales = {
            "I0W3": "Locales BOG",
            "NT3H": "NEPS",
            "MZ4C": "GRUPOS",
            "7C0A": "VACACIONAL",
            "7OMF": "Sucursal BAQ",
            "W5AA": "Sucursal CLO"
        }
 
        codigos_validos = "', '".join(sucursales.keys())
        query = f"""
            SELECT
                cd_sucursal,
                cd_codigo,
                cd_tiqueteador,
                ds_observaciones
            FROM dbo.ReservasGDS WITH (NOLOCK)
            WHERE cd_sucursal IN ('{codigos_validos}')
            ORDER BY cd_sucursal
        """
 
        print(f"🔍 Query ejecutado: {query}")
 
        with get_db_connection() as conn:
            cursor = conn.cursor()
 
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                print(f"📊 Columnas encontradas: {columns}")
                print(f"📊 Registros encontrados: {len(rows)}")
            finally:
                cursor.close()
 
        if not rows:
            print("⚠️ No se encontraron registros")
            return {"success": True, "data": [], "total": 0}
 
        result = []
        for row in rows:
            record = dict(zip(columns, row))
 
            cd = record.get("cd_sucursal", "DESCONOCIDO")
            if isinstance(cd, str):
                cd = cd.strip().upper()
 
            nombre_sucursal = sucursales.get(cd, "DESCONOCIDO")
 
            record["CodigoSucursal"] = cd
            record["NombreSucursal"] = nombre_sucursal
            record["Sucursal"] = f"{cd} - {nombre_sucursal}"
 
            result.append(record)
 
        print(f"✅ Respuesta preparada con {len(result)} registros")
        print(f"✅ Muestra de datos: {result[:3] if len(result) >= 3 else result}")
 
        return {
            "success": True,
            "data": result,
            "total": len(result),
            "filtrado_por_fechas": usar_filtro_fechas
        }
 
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR en get_reservas: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar reservas: {str(e)}"
        )


@app.get("/TiquetesDocumentos")
def get_tiquetes_documentos(limit: int = Query(1000, le=1000)):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = f"""
                SELECT TOP ({limit})
                    td.cd_tiquete,
                    td.ds_paxname,
                    td.ds_paxprefix,
                    td.ds_paxape,
                    td.ds_itinerario,
                    td.dt_salida,
                    td.dt_llegada,
                    td.ds_records,
                    td.ds_PNR,
                    rg.cd_tiqueteador,
                    rg.iden_gds,
                    rg.ds_observaciones,
                    td.id_asesor,
                    td.id_observacion,
                    td.id_estado,
                    td.id_silla,
                    td.id_cuenta,
                    td.id_hora,
                    td.id_atencion
                FROM TiquetesDocumentos td
                LEFT JOIN ReservasGDS rg ON td.ds_records = rg.cd_codigo
                ORDER BY td.dt_salida DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            tiquetes = []
            for row in rows:
                aerolinea = extraer_aerolinea_pnr(row[8])
                telefono = extraer_telefono_pnr(row[8])
                tiqueteador_pnr = extraer_tiqueteador_pnr(row[8])

                nombre_tiqueteador = None
                if row[9]:
                    cursor.execute("""
                        SELECT ds_nombre
                        FROM Tiqueteadores
                        WHERE cd_codigo = ?
                    """, (row[9],))
                    tiq_result = cursor.fetchone()
                    if tiq_result:
                        nombre_tiqueteador = tiq_result[0]

                if not nombre_tiqueteador and tiqueteador_pnr:
                    nombre_tiqueteador = tiqueteador_pnr

                tipo_reserva = determinar_tipo_gds(row[10]) if row[10] else None

                estado = 'Procesado' if row[14] == 'Procesado' or row[12] else 'Pendiente'

                paxname_limpio = limpiar_nombre_pasajero(row[1]) if row[1] else row[1]
                paxape_limpio = limpiar_nombre_pasajero(row[3]) if row[3] else row[3]

                tiquete = {
                    'cd_tiquete': row[0],
                    'ds_paxname': paxname_limpio,
                    'ds_paxprefix': row[2],
                    'ds_paxape': paxape_limpio,
                    'ds_itinerario': row[4],
                    'dt_salida': row[5].isoformat() if row[5] else None,
                    'dt_llegada': row[6].isoformat() if row[6] else None,
                    'ds_records': row[7],
                    'aerolinea': aerolinea,
                    'telefono': telefono,
                    'cd_tiqueteador': row[9],
                    'nombre_tiqueteador': nombre_tiqueteador,
                    'iden_gds': row[10],
                    'tipo_reserva': tipo_reserva,
                    'ds_observaciones': row[11],
                    'id_asesor': row[12],
                    'id_observacion': row[13],
                    'id_estado': estado,
                    'id_silla': row[15],
                    'id_cuenta': row[16],
                    'id_hora': row[17],
                    'id_atencion': row[18]
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

@app.get("/TiquetesDocumentos/{cd_tiquete}")
def get_tiquete_documento(cd_tiquete: str):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    td.cd_tiquete,
                    td.ds_paxname,
                    td.ds_paxprefix,
                    td.ds_paxape,
                    td.ds_itinerario,
                    td.dt_salida,
                    td.dt_llegada,
                    td.ds_records,
                    td.ds_PNR,
                    rg.cd_tiqueteador,
                    rg.iden_gds,
                    rg.ds_observaciones,
                    td.id_asesor,
                    td.id_observacion,
                    td.id_estado,
                    td.id_silla,
                    td.id_cuenta,
                    td.id_hora,
                    td.id_atencion
                FROM TiquetesDocumentos td
                LEFT JOIN ReservasGDS rg ON td.ds_records = rg.cd_codigo
                WHERE td.cd_tiquete = ?
            """

            cursor.execute(query, (cd_tiquete.strip(),))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Tiquete {cd_tiquete} no encontrado")

            aerolinea = extraer_aerolinea_pnr(row[8])
            telefono = extraer_telefono_pnr(row[8])
            tiqueteador_pnr = extraer_tiqueteador_pnr(row[8])

            nombre_tiqueteador = None
            if row[9]:
                cursor.execute("""
                    SELECT ds_nombre
                    FROM Tiqueteadores
                    WHERE cd_codigo = ?
                """, (row[9],))
                tiq_result = cursor.fetchone()
                if tiq_result:
                    nombre_tiqueteador = tiq_result[0]

            if not nombre_tiqueteador and tiqueteador_pnr:
                nombre_tiqueteador = tiqueteador_pnr

            tipo_reserva = determinar_tipo_gds(row[10]) if row[10] else None
            estado = 'Procesado' if row[14] == 'Procesado' or row[12] else 'Pendiente'

            paxname_limpio = limpiar_nombre_pasajero(row[1]) if row[1] else row[1]
            paxape_limpio = limpiar_nombre_pasajero(row[3]) if row[3] else row[3]

            tiquete = {
                'cd_tiquete': row[0],
                'ds_paxname': paxname_limpio,
                'ds_paxprefix': row[2],
                'ds_paxape': paxape_limpio,
                'ds_itinerario': row[4],
                'dt_salida': row[5].isoformat() if row[5] else None,
                'dt_llegada': row[6].isoformat() if row[6] else None,
                'ds_records': row[7],
                'aerolinea': aerolinea,
                'telefono': telefono,
                'cd_tiqueteador': row[9],
                'nombre_tiqueteador': nombre_tiqueteador,
                'iden_gds': row[10],
                'tipo_reserva': tipo_reserva,
                'ds_observaciones': row[11],
                'id_asesor': row[12],
                'id_observacion': row[13],
                'id_estado': estado,
                'id_silla': row[15],
                'id_cuenta': row[16],
                'id_hora': row[17],
                'id_atencion': row[18]
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
        print(f"📥 Asesor: {data.id_asesor}")
        print(f"📥 Hora: {data.id_hora}")

        if not data.id_asesor.strip():
            raise HTTPException(
                status_code=400,
                detail="El campo 'id_asesor' no puede estar vacío"
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT cd_tiquete FROM TiquetesDocumentos WHERE cd_tiquete = ?
            """, (cd_tiquete,))

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail=f"Tiquete {cd_tiquete} no encontrado"
                )

            cursor.execute("""
                UPDATE TiquetesDocumentos
                SET id_asesor = ?,
                    id_observacion = ?,
                    id_estado = 'Procesado',
                    id_silla = ?,
                    id_cuenta = ?,
                    id_hora = ?
                WHERE cd_tiquete = ?
            """, (
                data.id_asesor.strip(),
                data.id_observacion.strip() if data.id_observacion else None,
                data.id_silla.strip() if data.id_silla else None,
                data.id_cuenta.strip() if data.id_cuenta else None,
                data.id_hora,
                cd_tiquete
            ))

            rows_affected = cursor.rowcount
            print(f"🔢 Filas actualizadas: {rows_affected}")

            conn.commit()
            print("✅ Commit realizado correctamente")

            return {
                "success": True,
                "message": "Tiquete actualizado correctamente",
                "cd_tiquete": cd_tiquete
            }
    except HTTPException:
        raise
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
                FROM TiquetesDocumentos
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
    

@app.put("/TiquetesDocumentos/{cd_tiquete}/atencion")
def update_tiquete_atencion(cd_tiquete: str, data: dict):
    """
    Actualiza solo el tipo de atención (Presencial/Virtual) sin cambiar el estado
    """
    try:
        cd_tiquete = cd_tiquete.strip()
        id_atencion = data.get('id_atencion', '').strip()

        if not id_atencion or id_atencion not in ['Presencial', 'Virtual']:
            raise HTTPException(
                status_code=400,
                detail="El campo 'id_atencion' debe ser 'Presencial' o 'Virtual'"
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT cd_tiquete FROM TiquetesDocumentos WHERE cd_tiquete = ?
            """, (cd_tiquete,))

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail=f"Tiquete {cd_tiquete} no encontrado"
                )

            cursor.execute("""
                UPDATE TiquetesDocumentos
                SET id_atencion = ?
                WHERE cd_tiquete = ?
            """, (id_atencion, cd_tiquete))

            conn.commit()

            return {
                "success": True,
                "message": f"Tipo de atención actualizado a {id_atencion}",
                "cd_tiquete": cd_tiquete,
                "id_atencion": id_atencion
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)