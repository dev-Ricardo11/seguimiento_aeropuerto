from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

app = FastAPI(title="KONTROL API", version="1.0.0")

# Permitir que React se conecte (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],  # Agregado específico para Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de base de datos PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:2025*@localhost:5432/postgres")

# Modelos Pydantic
class ReservaBase(BaseModel):
    numeroReserva: str = Field(..., description="Número único de reserva")
    cliente: str = Field(..., description="Nombre del cliente")
    email: str = Field(..., description="Email del cliente")
    telefono: str = Field(..., description="Teléfono del cliente")
    fechaSalida: str = Field(..., description="Fecha de salida")
    fechaRegreso: Optional[str] = Field(None, description="Fecha de regreso")
    destino: str = Field(..., description="Destino del viaje")
    origen: str = Field(..., description="Origen del viaje")
    tipoViaje: str = Field(..., description="Tipo de viaje")
    estado: str = Field(..., description="Estado de la reserva")
    empresa: str = Field(..., description="Empresa responsable")
    precioTotal: float = Field(..., description="Precio total")
    moneda: str = Field(default="USD", description="Moneda")
    notas: Optional[str] = Field(None, description="Notas adicionales")

class ReservaCreate(ReservaBase):
    pass

class ReservaUpdate(BaseModel):
    numeroReserva: Optional[str] = None
    cliente: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    fechaSalida: Optional[str] = None
    fechaRegreso: Optional[str] = None
    destino: Optional[str] = None
    origen: Optional[str] = None
    tipoViaje: Optional[str] = None
    estado: Optional[str] = None
    empresa: Optional[str] = None
    precioTotal: Optional[float] = None
    moneda: Optional[str] = None
    notas: Optional[str] = None

class Reserva(ReservaBase):
    id: str
    fechaCreacion: datetime
    fechaActualizacion: datetime

# Conexión a base de datos
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_db():
    """Verificar la conexión a la base de datos existente"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Solo verificamos que podemos conectar, no creamos tablas
            cursor.execute("SELECT 1")
            print("Conexión a la base de datos exitosa")
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        # No falla la aplicación, solo avisa

# Inicializar la base de datos al arrancar
init_db()

# Endpoints

@app.get("/")
def read_root():
    return {"message": "KONTROL API v1.0.0", "status": "active"}

@app.get("/reservas")
def get_reservas(
    q: Optional[str] = Query(None, description="Búsqueda por cliente/número/destino"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    destino: Optional[str] = Query(None, description="Filtrar por destino"),
    fechaDesde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fechaHasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
        SELECT id, numero_reserva, cliente, email, telefono, fecha_salida, fecha_regreso,
               destino, origen, tipo_viaje, estado, empresa, precio_total, moneda, notas,
               fecha_creacion, fecha_actualizacion
        FROM reservas WHERE 1=1
        """
        params = []
        
        # Búsqueda general
        search_query = q or busqueda
        if search_query:
            sql += """ AND (
                cliente ILIKE %s OR 
                numero_reserva ILIKE %s OR 
                destino ILIKE %s OR
                origen ILIKE %s
            )"""
            like_query = f"%{search_query}%"
            params.extend([like_query, like_query, like_query, like_query])
        
        # Filtros específicos
        if estado:
            sql += " AND estado = %s"
            params.append(estado)
        
        if empresa:
            sql += " AND empresa ILIKE %s"
            params.append(f"%{empresa}%")
            
        if destino:
            sql += " AND destino ILIKE %s"
            params.append(f"%{destino}%")
        
        if fechaDesde:
            sql += " AND fecha_salida >= %s"
            params.append(fechaDesde)
            
        if fechaHasta:
            sql += " AND fecha_salida <= %s"
            params.append(fechaHasta)
        
        sql += " ORDER BY fecha_creacion DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        reservas = []
        for row in rows:
            reserva = {
                "id": str(row["id"]),
                "numeroReserva": row["numero_reserva"],
                "cliente": row["cliente"],
                "email": row["email"],
                "telefono": row["telefono"],
                "fechaSalida": row["fecha_salida"].isoformat() if row["fecha_salida"] else None,
                "fechaRegreso": row["fecha_regreso"].isoformat() if row["fecha_regreso"] else None,
                "destino": row["destino"],
                "origen": row["origen"],
                "tipoViaje": row["tipo_viaje"],
                "estado": row["estado"],
                "empresa": row["empresa"],
                "precioTotal": float(row["precio_total"]),
                "moneda": row["moneda"],
                "notas": row["notas"],
                "fechaCreacion": row["fecha_creacion"].isoformat(),
                "fechaActualizacion": row["fecha_actualizacion"].isoformat()
            }
            reservas.append(reserva)
        
        return {"total": len(reservas), "reservas": reservas}

@app.get("/reservas/estadisticas")
def get_estadisticas():
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total_reservas,
            COUNT(CASE WHEN estado = 'activa' THEN 1 END) as reservas_activas,
            COUNT(CASE WHEN estado = 'cancelada' THEN 1 END) as reservas_canceladas,
            COUNT(CASE WHEN estado = 'completada' THEN 1 END) as reservas_completadas,
            COALESCE(SUM(precio_total), 0) as ingresos_total,
            COUNT(*) as total_pasajeros
        FROM reservas
        """)
        
        result = cursor.fetchone()
        
        return {
            "totalReservas": result["total_reservas"] or 0,
            "reservasActivas": result["reservas_activas"] or 0,
            "reservasCanceladas": result["reservas_canceladas"] or 0,
            "reservasCompletadas": result["reservas_completadas"] or 0,
            "ingresosTotal": float(result["ingresos_total"] or 0),
            "totalPasajeros": result["total_pasajeros"] or 0
        }

@app.get("/reservas/{reserva_id}")
def get_reserva(reserva_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
        SELECT id, numero_reserva, cliente, email, telefono, fecha_salida, fecha_regreso,
               destino, origen, tipo_viaje, estado, empresa, precio_total, moneda, notas,
               fecha_creacion, fecha_actualizacion
        FROM reservas WHERE id = %s
        """, (reserva_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        reserva = {
            "id": str(row["id"]),
            "numeroReserva": row["numero_reserva"],
            "cliente": row["cliente"],
            "email": row["email"],
            "telefono": row["telefono"],
            "fechaSalida": row["fecha_salida"].isoformat() if row["fecha_salida"] else None,
            "fechaRegreso": row["fecha_regreso"].isoformat() if row["fecha_regreso"] else None,
            "destino": row["destino"],
            "origen": row["origen"],
            "tipoViaje": row["tipo_viaje"],
            "estado": row["estado"],
            "empresa": row["empresa"],
            "precioTotal": float(row["precio_total"]),
            "moneda": row["moneda"],
            "notas": row["notas"],
            "fechaCreacion": row["fecha_creacion"].isoformat(),
            "fechaActualizacion": row["fecha_actualizacion"].isoformat()
        }
        
        return {"reserva": reserva}

@app.post("/reservas")
def create_reserva(reserva: ReservaCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
            INSERT INTO reservas (
                numero_reserva, cliente, email, telefono, fecha_salida, fecha_regreso,
                destino, origen, tipo_viaje, estado, empresa, precio_total, moneda, notas
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, fecha_creacion, fecha_actualizacion
            """, (
                reserva.numeroReserva, reserva.cliente, reserva.email, reserva.telefono,
                reserva.fechaSalida, reserva.fechaRegreso, reserva.destino, reserva.origen,
                reserva.tipoViaje, reserva.estado, reserva.empresa, reserva.precioTotal,
                reserva.moneda, reserva.notas
            ))
            
            result = cursor.fetchone()
            conn.commit()
            
            nueva_reserva = {
                "id": str(result["id"]),
                "numeroReserva": reserva.numeroReserva,
                "cliente": reserva.cliente,
                "email": reserva.email,
                "telefono": reserva.telefono,
                "fechaSalida": reserva.fechaSalida,
                "fechaRegreso": reserva.fechaRegreso,
                "destino": reserva.destino,
                "origen": reserva.origen,
                "tipoViaje": reserva.tipoViaje,
                "estado": reserva.estado,
                "empresa": reserva.empresa,
                "precioTotal": reserva.precioTotal,
                "moneda": reserva.moneda,
                "notas": reserva.notas,
                "fechaCreacion": result["fecha_creacion"].isoformat(),
                "fechaActualizacion": result["fecha_actualizacion"].isoformat()
            }
            
            return {"success": True, "message": "Reserva creada exitosamente", "reserva": nueva_reserva}
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if "unique constraint" in str(e).lower():
                raise HTTPException(status_code=400, detail="Ya existe una reserva con ese número")
            raise HTTPException(status_code=400, detail="Error de integridad de datos")

@app.put("/reservas/{reserva_id}")
def update_reserva(reserva_id: str, reserva: ReservaUpdate):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Construir la consulta dinámicamente con solo los campos proporcionados
        updates = []
        params = []
        
        for field, value in reserva.dict(exclude_unset=True).items():
            if field == "numeroReserva":
                updates.append("numero_reserva = %s")
            elif field == "fechaSalida":
                updates.append("fecha_salida = %s")
            elif field == "fechaRegreso":
                updates.append("fecha_regreso = %s")
            elif field == "tipoViaje":
                updates.append("tipo_viaje = %s")
            elif field == "precioTotal":
                updates.append("precio_total = %s")
            else:
                updates.append(f"{field} = %s")
            params.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        params.append(reserva_id)
        sql = f"UPDATE reservas SET {', '.join(updates)} WHERE id = %s RETURNING *"
        
        cursor.execute(sql, params)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        conn.commit()
        
        reserva_actualizada = {
            "id": str(result["id"]),
            "numeroReserva": result["numero_reserva"],
            "cliente": result["cliente"],
            "email": result["email"],
            "telefono": result["telefono"],
            "fechaSalida": result["fecha_salida"].isoformat() if result["fecha_salida"] else None,
            "fechaRegreso": result["fecha_regreso"].isoformat() if result["fecha_regreso"] else None,
            "destino": result["destino"],
            "origen": result["origen"],
            "tipoViaje": result["tipo_viaje"],
            "estado": result["estado"],
            "empresa": result["empresa"],
            "precioTotal": float(result["precio_total"]),
            "moneda": result["moneda"],
            "notas": result["notas"],
            "fechaCreacion": result["fecha_creacion"].isoformat(),
            "fechaActualizacion": result["fecha_actualizacion"].isoformat()
        }
        
        return {"success": True, "message": "Reserva actualizada exitosamente", "reserva": reserva_actualizada}

@app.delete("/reservas/{reserva_id}")
def delete_reserva(reserva_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        conn.commit()
        return {"success": True, "message": "Reserva eliminada exitosamente"}

# Endpoint de salud
@app.get("/health")
def health_check():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)