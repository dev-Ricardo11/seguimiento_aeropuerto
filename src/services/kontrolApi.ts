import { Reserva } from '../components/ReservaCard';
import { Notification } from '../components/NotificationSystem';

// Simulación de datos para demostración
const mockReservas: Reserva[] = [
  {
    id: '1',
    numeroReserva: 'KTL-2025-001',
    cliente: 'María García Rodríguez',
    destino: 'Cancún, México',
    fechaSalida: '2025-02-15',
    fechaRegreso: '2025-02-22',
    empresa: 'EVT',
    pasajeros: 2,
    estado: 'confirmada',
    precio: 2800000,
    tipoViaje: 'ida-vuelta'
  },
  {
    id: '2',
    numeroReserva: 'KTL-2025-002',
    cliente: 'Carlos Mendoza Silva',
    destino: 'París, Francia',
    fechaSalida: '2025-02-20',
    fechaRegreso: '2025-02-28',
    empresa: 'GBT',
    pasajeros: 4,
    estado: 'en-curso',
    precio: 4500000,
    tipoViaje: 'ida-vuelta'
  },
  {
    id: '3',
    numeroReserva: 'KTL-2025-003',
    cliente: 'Ana Lucia Herrera',
    destino: 'Dubai, Emiratos Árabes',
    fechaSalida: '2025-03-01',
    fechaRegreso: '2025-03-10',
    empresa: 'EVT',
    pasajeros: 1,
    estado: 'pendiente',
    precio: 3200000,
    tipoViaje: 'ida-vuelta'
  },
  {
    id: '4',
    numeroReserva: 'KTL-2025-004',
    cliente: 'Roberto Jiménez López',
    destino: 'Roma, Italia',
    fechaSalida: '2025-02-10',
    fechaRegreso: '2025-02-18',
    empresa: 'EVT',
    pasajeros: 3,
    estado: 'completada',
    precio: 3800000,
    tipoViaje: 'ida-vuelta'
  },
  {
    id: '5',
    numeroReserva: 'KTL-2025-005',
    cliente: 'Patricia Ruiz Morales',
    destino: 'Nueva York, Estados Unidos',
    fechaSalida: '2025-02-25',
    fechaRegreso: '2025-03-05',
    empresa: 'AMERICAN EXPRESS',
    pasajeros: 2,
    estado: 'confirmada',
    precio: 2900000,
    tipoViaje: 'ida-vuelta'
  }
];

const mockNotificaciones: Notification[] = [
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

//  API de KONTROL
export class KontrolApiService {
  private static instance: KontrolApiService;
  private reservas: Reserva[] = [...mockReservas];
  private notificaciones: Notification[] = [...mockNotificaciones];

  static getInstance(): KontrolApiService {
    if (!KontrolApiService.instance) {
      KontrolApiService.instance = new KontrolApiService();
    }
    return KontrolApiService.instance;
  }

  // Simular delay de API real
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async obtenerReservas(): Promise<Reserva[]> {
    await this.delay(800); // Simular latencia de API
    return [...this.reservas];
  }

  async obtenerReservaPorId(id: string): Promise<Reserva | null> {
    await this.delay(300);
    return this.reservas.find(r => r.id === id) || null;
  }

  async buscarReservas(query: string): Promise<Reserva[]> {
    await this.delay(500);
    const queryLower = query.toLowerCase();
    return this.reservas.filter(r => 
      r.cliente.toLowerCase().includes(queryLower) ||
      r.numeroReserva.toLowerCase().includes(queryLower) ||
      r.destino.toLowerCase().includes(queryLower)
    );
  }

  async filtrarReservas(filters: {
    fechaDesde?: string;
    fechaHasta?: string;
    estado?: string;
    empresa?: string;
    destino?: string;
    busqueda?: string;
  }): Promise<Reserva[]> {
    await this.delay(600);
    
    let filtered = [...this.reservas];

    if (filters.busqueda) {
      const query = filters.busqueda.toLowerCase();
      filtered = filtered.filter(r => 
        r.cliente.toLowerCase().includes(query) ||
        r.numeroReserva.toLowerCase().includes(query) ||
        r.destino.toLowerCase().includes(query)
      );
    }

    if (filters.estado) {
      filtered = filtered.filter(r => r.estado === filters.estado);
    }

    if (filters.destino) {
      filtered = filtered.filter(r => 
        r.destino.toLowerCase().includes(filters.destino!.toLowerCase())
      );
    }

    if (filters.fechaDesde) {
      filtered = filtered.filter(r => r.fechaSalida >= filters.fechaDesde!);
    }

    if (filters.fechaHasta) {
      filtered = filtered.filter(r => r.fechaSalida <= filters.fechaHasta!);
    }

    return filtered;
  }

  async obtenerNotificaciones(): Promise<Notification[]> {
    await this.delay(400);
    return [...this.notificaciones];
  }

  async marcarNotificacionComoLeida(id: string): Promise<void> {
    await this.delay(200);
    const notificacion = this.notificaciones.find(n => n.id === id);
    if (notificacion) {
      notificacion.leida = true;
    }
  }

  async eliminarNotificacion(id: string): Promise<void> {
    await this.delay(200);
    this.notificaciones = this.notificaciones.filter(n => n.id !== id);
  }

  // Simular generación de nuevas notificaciones (para demostrar funcionalidad en tiempo real)
  generarNotificacionAleatoria(): void {
    const tipos: Notification['tipo'][] = ['info', 'success', 'warning'];
    const titulos = {
      info: 'Nueva información de viaje',
      success: 'Operación exitosa',
      warning: 'Atención requerida'
    };
    const mensajes = {
      info: 'Se ha actualizado la información del vuelo.',
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

    this.notificaciones.unshift(nuevaNotificacion);
  }
}