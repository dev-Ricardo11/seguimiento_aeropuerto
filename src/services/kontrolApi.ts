import { Reserva } from '../components/ReservaCard';
import { Notification } from '../components/NotificationSystem';

// Configuración de la API
const API_BASE_URL = 'http://localhost:8000';

// API de KONTROL con PostgreSQL
export class KontrolApiService {
  private static instance: KontrolApiService;
  private notificacionesLocal: Notification[] = [
    {
      id: '1',
      tipo: 'info',
      titulo: 'Nuevo viaje programado',
      mensaje: 'El viaje KTL-2025-002 a París iniciará en 2 días. Verificar documentación.',
      empresa: 'EVT',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      leida: false
    },
    {
      id: '2',
      tipo: 'warning',
      titulo: 'Documentación pendiente',
      mensaje: 'La reserva KTL-2025-003 requiere verificación de documentos del cliente.',
      empresa: 'EVT',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
      leida: false
    },
    {
      id: '3',
      tipo: 'success',
      titulo: 'Viaje completado',
      mensaje: 'El viaje KTL-2025-004 a Roma se completó exitosamente.',
      empresa: 'AMERICAN EXPRESS',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
      leida: true
    }
  ];

  static getInstance(): KontrolApiService {
    if (!KontrolApiService.instance) {
      KontrolApiService.instance = new KontrolApiService();
    }
    return KontrolApiService.instance;
  }

  // Método helper para realizar peticiones HTTP
  private async fetchAPI(endpoint: string, options: RequestInit = {}): Promise<any> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`Error en la API: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // MÉTODOS PARA RESERVAS (conectados a PostgreSQL)
  async obtenerReservas(): Promise<Reserva[]> {
    try {
      const data = await this.fetchAPI('/reservas');
      return data.reservas || [];
    } catch (error) {
      console.error('Error al obtener reservas:', error);
      return [];
    }
  }

  async obtenerReservaPorId(id: string): Promise<Reserva | null> {
    try {
      const data = await this.fetchAPI(`/reservas/${id}`);
      return data.reserva || null;
    } catch (error) {
      console.error('Error al obtener reserva por ID:', error);
      return null;
    }
  }

  async buscarReservas(query: string): Promise<Reserva[]> {
    try {
      const data = await this.fetchAPI(`/reservas?q=${encodeURIComponent(query)}`);
      return data.reservas || [];
    } catch (error) {
      console.error('Error al buscar reservas:', error);
      return [];
    }
  }

  async filtrarReservas(filters: {
    fechaDesde?: string;
    fechaHasta?: string;
    estado?: string;
    empresa?: string;
    destino?: string;
    precio_total:string
    id?:string;
    busqueda?: string;
  }): Promise<Reserva[]> {
    try {
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });

      const queryString = params.toString();
      const endpoint = `/reservas${queryString ? `?${queryString}` : ''}`;
      
      const data = await this.fetchAPI(endpoint);
      return data.reservas || [];
    } catch (error) {
      console.error('Error al filtrar reservas:', error);
      return [];
    }
  }

  async crearReserva(reserva: Omit<Reserva, 'id'>): Promise<Reserva | null> {
    try {
      const data = await this.fetchAPI('/reservas', {
        method: 'POST',
        body: JSON.stringify(reserva),
      });
      return data.reserva || null;
    } catch (error) {
      console.error('Error al crear reserva:', error);
      return null;
    }
  }

  async actualizarReserva(id: string, reserva: Partial<Reserva>): Promise<Reserva | null> {
    try {
      const data = await this.fetchAPI(`/reservas/${id}`, {
        method: 'PUT',
        body: JSON.stringify(reserva),
      });
      return data.reserva || null;
    } catch (error) {
      console.error('Error al actualizar reserva:', error);
      return null;
    }
  }

  async eliminarReserva(id: string): Promise<boolean> {
    try {
      await this.fetchAPI(`/reservas/${id}`, {
        method: 'DELETE',
      });
      return true;
    } catch (error) {
      console.error('Error al eliminar reserva:', error);
      return false;
    }
  }

  // MÉTODOS PARA NOTIFICACIONES (mantenidos locales por ahora)
  async obtenerNotificaciones(): Promise<Notification[]> {
    // Simular delay de API
    await new Promise(resolve => setTimeout(resolve, 400));
    return [...this.notificacionesLocal];
  }

  async marcarNotificacionComoLeida(id: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 200));
    const notificacion = this.notificacionesLocal.find(n => n.id === id);
    if (notificacion) {
      notificacion.leida = true;
    }
  }

  async eliminarNotificacion(id: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 200));
    this.notificacionesLocal = this.notificacionesLocal.filter(n => n.id !== id);
  }

  // Simular generación de nuevas notificaciones
  generarNotificacionAleatoria(): void {
    const tipos: Notification['tipo'][] = ['info', 'success', 'warning'];
    const titulos = {
      info: 'Nueva información de viaje',
      success: 'Operación exitosa',
      warning: 'Atención requerida'
    };
    const mensajes = {
      info: 'Se ha actualizado la información del viaje.',
      success: 'El proceso se completó correctamente.',
      warning: 'Se requiere verificación adicional.'
    };

    const tipo = tipos[Math.floor(Math.random() * tipos.length)];
    const nuevaNotificacion: Notification = {
      id: Date.now().toString(),
      tipo,
      titulo: titulos[tipo],
      mensaje: mensajes[tipo],
      empresa: '',
      timestamp: new Date(),
      leida: false
    };

    this.notificacionesLocal.unshift(nuevaNotificacion);
  }

  // MÉTODOS ADICIONALES PARA ESTADÍSTICAS
  async obtenerEstadisticas(): Promise<{
    totalReservas: number;
    reservasActivas: number;
    reservasCanceladas: number;
    reservasCompletadas: number;
    ingresosTotal: number;
    totalPasajeros: number;
  }> {
    try {
      const data = await this.fetchAPI('/reservas/estadisticas');
      return {
        totalReservas: data.totalReservas || 0,
        reservasActivas: data.reservasActivas || 0,
        reservasCanceladas: data.reservasCanceladas || 0,
        reservasCompletadas: data.reservasCompletadas || 0,
        ingresosTotal: data.ingresosTotal || 0,
        totalPasajeros: data.totalPasajeros || 0
      };
    } catch (error) {
      console.error('Error al obtener estadísticas:', error);
      return {
        totalReservas: 0,
        reservasActivas: 0,
        reservasCanceladas: 0,
        reservasCompletadas: 0,
        ingresosTotal: 0,
        totalPasajeros: 0
      };
    }
  }
}