import { useState, useEffect } from 'react';
import { Plane, RefreshCw, HelpCircle } from 'lucide-react';
import ReservaCard, { Reserva } from './components/ReservaCard';
import NotificationSystem, { Notification } from './components/NotificationSystem';
import FilterPanel, { FilterState } from './components/FilterPanel';
import StatsCards from './components/StatsCards';
import { KontrolApiService } from './services/kontrolApi';

function App() {
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [filteredReservas, setFilteredReservas] = useState<Reserva[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    busqueda: '',
    fechaDesde: '',
    fechaHasta: '',
    empresa: '',
    estado: '',
    destino: ''
  });
  const [selectedReserva, setSelectedReserva] = useState<Reserva | null>(null);

  const kontrolApi = KontrolApiService.getInstance();

  useEffect(() => {
    cargarDatosIniciales();
    
    // Simular notificaciones en tiempo real
    const interval = setInterval(() => {
      if (Math.random() < 0.3) { // 30% chance cada 10 segundos
        kontrolApi.generarNotificacionAleatoria();
        cargarNotificaciones();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    aplicarFiltros();
  }, [reservas, filters]);

  const cargarDatosIniciales = async () => {
    setLoading(true);
    try {
      const [reservasData, notificationsData] = await Promise.all([
        kontrolApi.obtenerReservas(),
        kontrolApi.obtenerNotificaciones()
      ]);
      
      setReservas(reservasData);
      setNotifications(notificationsData);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const cargarNotificaciones = async () => {
    try {
      const notificationsData = await kontrolApi.obtenerNotificaciones();
      setNotifications(notificationsData);
    } catch (error) {
      console.error('Error cargando notificaciones:', error);
    }
  };

  const aplicarFiltros = async () => {
    try {
      const filtered = await kontrolApi.filtrarReservas(filters);
      setFilteredReservas(filtered);
    } catch (error) {
      console.error('Error aplicando filtros:', error);
    }
  };

  const handleRefresh = () => {
    cargarDatosIniciales();
  };

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({
      busqueda: '',
      fechaDesde: '',
      fechaHasta: '',
      empresa: '',
      estado: '',
      destino: ''
    });
  };

  const handleReservaClick = (reserva: Reserva) => {
    setSelectedReserva(reserva);
  };

  const handleMarkNotificationAsRead = async (id: string) => {
    try {
      await kontrolApi.marcarNotificacionComoLeida(id);
      cargarNotificaciones();
    } catch (error) {
      console.error('Error marcando notificación como leída:', error);
    }
  };

  const handleDismissNotification = async (id: string) => {
    try {
      await kontrolApi.eliminarNotificacion(id);
      cargarNotificaciones();
    } catch (error) {
      console.error('Error eliminando notificación:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-lg text-gray-600">Conectando con KONTROL API...</p>
          <p className="text-sm text-gray-400 mt-2">Cargando reservas y notificaciones</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Plane className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">KONTROL Dashboard</h1>
                  <p className="text-sm text-gray-500">Sistema de Gestión de Reservas</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                title="Actualizar datos"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              
              <NotificationSystem
                notifications={notifications}
                onMarkAsRead={handleMarkNotificationAsRead}
                onDismiss={handleDismissNotification}
              />
              
              
              
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200">
                <HelpCircle className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <StatsCards reservas={reservas} />
        
        {/* Filters */}
        <FilterPanel
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleResetFilters}
        />

        {/* Results Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Reservas ({filteredReservas.length})
          </h2>
          <p className="text-sm text-gray-500">
            Última actualización: {new Date().toLocaleTimeString()}
          </p>
        </div>

        {/* Reservas Grid */}
        {filteredReservas.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-12 text-center">
            <Plane className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No se encontraron reservas
            </h3>
            <p className="text-gray-500">
              Intenta ajustar los filtros de búsqueda o crear una nueva reserva.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredReservas.map((reserva) => (
              <ReservaCard
                key={reserva.id}
                reserva={reserva}
                onClick={() => handleReservaClick(reserva)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Modal de Detalle de Reserva */}
      {selectedReserva && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">
                  Detalle de Reserva #{selectedReserva.numeroReserva}
                </h2>
                <button
                  onClick={() => setSelectedReserva(null)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Información del Cliente</h3>
                  <p className="text-gray-600">{selectedReserva.cliente}</p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Destino</h3>
                  <p className="text-gray-600">{selectedReserva.destino}</p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Fechas</h3>
                  <p className="text-gray-600">
                    {selectedReserva.fechaSalida} - {selectedReserva.fechaRegreso}
                  </p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Pasajeros</h3>
                  <p className="text-gray-600">{selectedReserva.pasajeros}</p>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Empresa</h3>
                  <p className="text-gray-600">{selectedReserva.empresa}</p>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Estado</h3>
                  <p className="text-gray-600 capitalize">{selectedReserva.estado}</p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Precio</h3>
                  <p className="text-gray-600 font-semibold">
                    ${selectedReserva.precio.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;