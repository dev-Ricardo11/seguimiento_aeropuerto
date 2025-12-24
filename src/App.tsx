import { useState, useEffect, ChangeEvent } from 'react';
import { Plane, RefreshCw, HelpCircle, LogOut, Info } from 'lucide-react';
import Login from './components/login';
import ReservaCard from './components/ReservaCard';
import NotificationSystem, { Notification } from './components/NotificationSystem';
import FilterPanel, { FilterState } from './components/FilterPanel';
import StatsCards from './components/StatsCards';
import kontrolApi, { TiquetesDocumentos } from './services/kontrolApi';
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState('');
  const [userRole, setUserRole] = useState('');
  const [tiquetes, setTiquetes] = useState<TiquetesDocumentos[]>([]);
  const [filteredTiquetes, setFilteredTiquetes] = useState<TiquetesDocumentos[]>([]);
  const [notifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState>({
    busqueda: '',
    fechaDesde: '',
    fechaHasta: '',
    empresa: '',
    estado: '',
    destino: '',
    tipo_vuelo: ''
  });
  const [selectedTiquete, setSelectedTiquete] = useState<TiquetesDocumentos | null>(null);
  const [openModal, setOpenModal] = useState<boolean>(false);


  useEffect(() => {
    const savedUser = localStorage.getItem('kontrol_user');
    const savedRole = localStorage.getItem('kontrol_role');
    if (savedUser) {
      setIsAuthenticated(true);
      setCurrentUser(savedUser);
      setUserRole(savedRole || '');
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      cargarDatosIniciales();
    }
  }, [isAuthenticated, filters.tipo_vuelo]);

  useEffect(() => {
    aplicarFiltros();
  }, [tiquetes, filters]);

  const handleLogin = (correo: string, role: string) => {
    setIsAuthenticated(true);
    setCurrentUser(correo);
    setUserRole(role);
    localStorage.setItem('kontrol_user', correo);
    localStorage.setItem('kontrol_role', role);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentUser('');
    setUserRole('');
    localStorage.removeItem('kontrol_user');
    localStorage.removeItem('kontrol_role');
    setTiquetes([]);
    setFilteredTiquetes([]);
  };

  const cargarDatosIniciales = async () => {
    setLoading(true);
    try {
      const response = await kontrolApi.getTiquetesDocumentos({
        limit: 1000,
        tipo_vuelo: filters.tipo_vuelo
      });
      console.log('📊 Respuesta completa del API:', response);

      const tiquetesUnicos = response.tiquetes?.reduce((acc: TiquetesDocumentos[], current: TiquetesDocumentos) => {
        const existe = acc.find(t => t.cd_tiquete === current.cd_tiquete);
        if (!existe) {
          acc.push(current);
        }
        return acc;
      }, []) || [];

      console.log('📊 Total tiquetes recibidos:', response.tiquetes?.length);
      console.log('📊 Tiquetes únicos:', tiquetesUnicos.length);

      setTiquetes(tiquetesUnicos);
    } catch (error) {
      console.error('Error cargando datos:', error);
      setTiquetes([]);
    } finally {
      setLoading(false);
    }
  };

  const aplicarFiltros = () => {
    let filtered = [...tiquetes];

    if (filters.busqueda) {
      const searchLower = filters.busqueda.toLowerCase();
      filtered = filtered.filter(t =>
        t.cd_tiquete.toLowerCase().includes(searchLower) ||
        t.ds_paxname?.toLowerCase().includes(searchLower) ||
        t.ds_paxape?.toLowerCase().includes(searchLower) ||
        t.ds_records?.toLowerCase().includes(searchLower) ||
        t.ds_itinerario?.toLowerCase().includes(searchLower)
      );
    }

    if (filters.fechaDesde && filters.fechaDesde.trim() !== '') {
      const fechaDesde = new Date(filters.fechaDesde);
      filtered = filtered.filter(t => {
        const fechaComparar = t.dt_salida || t.dt_llegada;
        if (!fechaComparar) return false;
        return new Date(fechaComparar) >= fechaDesde;
      });
    }

    if (filters.fechaHasta && filters.fechaHasta.trim() !== '') {
      const fechaHasta = new Date(filters.fechaHasta);
      filtered = filtered.filter(t => {
        const fechaComparar = t.dt_salida || t.dt_llegada;
        if (!fechaComparar) return false;
        return new Date(fechaComparar) <= fechaHasta;
      });
    }

    if (filters.estado && filters.estado !== '') {
      filtered = filtered.filter(t => t.id_estado === filters.estado);
    }

    setFilteredTiquetes(filtered);
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
      destino: '',
      tipo_vuelo: ''
    });
  };

  const handleTiqueteClick = (tiquete: TiquetesDocumentos) => {
    console.log('🔍 DATOS COMPLETOS DEL TIQUETE:', tiquete);
    setSelectedTiquete(tiquete);
  };

  const handleMarkNotificationAsRead = async (id: string) => {
    console.log('Marcar como leída:', id);
  };

  const handleDismissNotification = async (id: string) => {
    console.log('Eliminar notificación:', id);
  };

  interface Pasajero {
    ds_records: string;
    cd_tiquete: string;
    ds_paxname: string;
    nombre_tiqueteador: string;
    ds_itinerario: string;
    dt_salida: string;
    tipo_reserva: string;
    id_asesor: string;
    id_observacion: string;
    id_silla: string;
    id_cuenta: string;
  }

  interface AdicionarPasajeroModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (nuevoPasajero: Pasajero) => void;
  }

  const AdicionarPasajeroModal: React.FC<AdicionarPasajeroModalProps> = ({
    isOpen,
    onClose,
    onSave,
  }) => {
    const [formData, setFormData] = useState<Pasajero>({
      ds_records: "",
      cd_tiquete: "",
      ds_paxname: "",
      nombre_tiqueteador: "",
      ds_itinerario: "",
      dt_salida: "",
      tipo_reserva: "",
      id_asesor: "",
      id_observacion: "",
      id_silla: "",
      id_cuenta: "",
    });

    const asesores = [
      "Jhon Alexander Silva",
      "Wendy Cantillo Maury",
      "Diana Milena Lozano",
      "Lina Paola Lopez",
    ];

    const handleChange = (
      e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
    ) => {
      const { name, value } = e.target;
      setFormData({ ...formData, [name]: value });
    };

    const handleSave = () => {
      onSave(formData);
      // onClose(); // Let parent close after async save or handle loading
    };

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
        <div className="bg-white rounded-2xl shadow-lg w-[600px] p-6 relative">
          <button
            className="absolute top-3 right-4 text-gray-500 hover:text-black"
            onClick={onClose}
          >
            ✕
          </button>

          <h2 className="text-xl font-semibold mb-4">
            🧾 Adicionar Nuevo Pasajero
          </h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium">Record</label>
              <input
                name="ds_records"
                value={formData.ds_records}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Código Tiquete</label>
              <input
                name="cd_tiquete"
                value={formData.cd_tiquete}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium">Nombre del Pasajero</label>
              <input
                name="ds_paxname"
                value={formData.ds_paxname}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium">Nombre del Tiqueteador</label>
              <input
                name="nombre_tiqueteador"
                value={formData.nombre_tiqueteador}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Itinerario</label>
              <input
                name="ds_itinerario"
                value={formData.ds_itinerario}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Fecha de Salida</label>
              <input
                type="datetime-local"
                name="dt_salida"
                value={formData.dt_salida}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Tipo de Reserva</label>
              <input
                name="tipo_reserva"
                value={formData.tipo_reserva}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              />
            </div>

            {/* 🔽 Select de Asesor */}
            <div>
              <label className="text-sm font-medium">Asesor</label>
              <select
                name="id_asesor"
                value={formData.id_asesor}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
              >
                <option value="">Seleccionar asesor...</option>
                {asesores.map((asesor) => (
                  <option key={asesor} value={asesor}>
                    {asesor}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium">Silla</label>
              <input
                name="id_silla"
                value={formData.id_silla}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
                placeholder="Ingrese número de silla"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Cuenta</label>
              <input
                name="id_cuenta"
                value={formData.id_cuenta}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
                placeholder="Ingrese cuenta"
              />
            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium">Observación</label>
              <textarea
                name="id_observacion"
                value={formData.id_observacion}
                onChange={handleChange}
                className="w-full border rounded-lg px-2 py-1"
                rows={2}
              />
            </div>
          </div>

          <div className="flex justify-end mt-5">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 rounded-lg mr-2 hover:bg-gray-400"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Guardar
            </button>
          </div>
        </div>
      </div>
    );
  };






  const exportToExcel = () => {
    if (filteredTiquetes.length === 0) {
      alert("No hay datos para exportar");
      return;
    }

    const dataToExport = filteredTiquetes.map(t => ({
      Tiquete: t.cd_tiquete,
      Record: t.ds_records,
      Nombre: `${t.ds_paxname || ''} ${t.ds_paxape || ''}`.trim(),
      Itinerario: t.ds_itinerario || '',
      FechaSalida: t.dt_salida || '',
      FechaLlegada: t.dt_llegada || '',
      Aerolinea: t.aerolinea || '',
      Telefono: t.telefono || '',
      Tiqueteador: t.nombre_tiqueteador || '',
      TipoReserva: t.tipo_reserva || '',
      Estado: t.id_estado || 'Pendiente',
      Observacion: t.id_observacion || '',
      Asesor: t.id_asesor || '',
      Silla: t.id_silla || '',
      Hora: t.id_hora || ''
    }));

    const worksheet = XLSX.utils.json_to_sheet(dataToExport);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Tiquetes");

    const excelBuffer = XLSX.write(workbook, { bookType: "xlsx", type: "array" });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });

    const fileName = `Tiquetes_${new Date().toISOString().slice(0, 10)}.xlsx`;
    saveAs(blob, fileName);
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-lg text-gray-600">Conectando con KONTROL API...</p>
          <p className="text-sm text-gray-400 mt-2">Cargando tiquetes</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
                  <p className="text-sm text-gray-500">Sistema de Gestión de Tiquetes</p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                <span className="font-medium">{currentUser}</span>
              </span>

              <button
                onClick={handleRefresh}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                title="Actualizar datos"
              >
                <RefreshCw className="w-5 h-5" />
              </button>

              {userRole.toLowerCase() === 'administrador' && (
                <button
                  onClick={() => window.open('http://localhost:8501', '_blank')}
                  className="flex items-center gap-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  <Info className="w-5 h-5" />
                  <span className="text-sm font-medium">Gestión Aeropuerto</span>
                </button>
              )}

              <NotificationSystem
                notifications={notifications}
                onMarkAsRead={handleMarkNotificationAsRead}
                onDismiss={handleDismissNotification}
              />

              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200">
                <HelpCircle className="w-5 h-5" />
              </button>

              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors duration-200"
                title="Cerrar sesión"
              >
                <LogOut className="w-5 h-5" />
                <span className="text-sm font-medium">Salir</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {userRole.toLowerCase() === 'administrador' && <StatsCards tiquetes={tiquetes} />}

        <FilterPanel
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleResetFilters}
        />

        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Tiquetes ({filteredTiquetes.length})
          </h2>

          <div className="flex items-center gap-4">
            <p className="text-sm text-gray-500">
              Última actualización: {new Date().toLocaleTimeString()}
            </p>

            {userRole.toLowerCase() === 'administrador' && (
              <>
                <button
                  onClick={exportToExcel}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-md transition-all"
                >
                  Exportar Excel
                </button>

                <button
                  onClick={() => setOpenModal(true)}
                  className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg shadow-md transition-all"
                >
                  Adicionar Pasajero
                </button>
              </>
            )}

            <AdicionarPasajeroModal
              isOpen={openModal}
              onClose={() => setOpenModal(false)}
              onSave={async (nuevoPasajero) => {
                console.log("Nuevo pasajero agregado:", nuevoPasajero);
                try {
                  const currentFilter = filters.tipo_vuelo || 'IDA'; // Default to IDA if no filter
                  await kontrolApi.createTiquete(nuevoPasajero, currentFilter);
                  setOpenModal(false);
                  alert("Pasajero creado exitosamente");
                  cargarDatosIniciales(); // Reload list
                } catch (error) {
                  console.error("Error creating ticket:", error);
                  alert("Error al crear el pasajero. Verifique los datos e intente nuevamente.");
                }
              }}
            />



          </div>
        </div>

        {filteredTiquetes.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-12 text-center">
            <Plane className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No se encontraron tiquetes
            </h3>
            <p className="text-gray-500">
              Intenta ajustar los filtros de búsqueda.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredTiquetes.map((tiquete, index) => (
              <ReservaCard
                key={`${tiquete.cd_tiquete}-${index}`}
                tiquete={tiquete}
                onClick={() => handleTiqueteClick(tiquete)}
              />
            ))}
          </div>
        )}
      </main>

      {selectedTiquete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100 sticky top-0 bg-white z-10">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Detalle de Tiquete #{selectedTiquete.cd_tiquete}
                  </h2>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${selectedTiquete.id_estado === 'Procesado'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                    }`}>
                    {selectedTiquete.id_estado || 'Pendiente'}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedTiquete(null)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Record</h3>
                  <p className="text-gray-600">{selectedTiquete.ds_records}</p>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Código Tiquete</h3>
                  <p className="text-gray-600">{selectedTiquete.cd_tiquete}</p>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Nombre del Pasajero</h3>
                  <p className="text-gray-600">
                    {selectedTiquete.ds_paxname} {selectedTiquete.ds_paxape}
                  </p>
                </div>

                {selectedTiquete.nombre_tiqueteador && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Nombre del Tiqueteador</h3>
                    <p className="text-gray-600">{selectedTiquete.nombre_tiqueteador}</p>
                  </div>
                )}

                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Itinerario</h3>
                  <p className="text-gray-600">{selectedTiquete.ds_itinerario}</p>
                </div>

                {selectedTiquete.dt_salida && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Fecha de Salida</h3>
                    <p className="text-gray-600">{selectedTiquete.dt_salida}</p>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 ml-4">
                      <span className="text-sm text-gray-600">Atención:</span>
                      <button
                        onClick={async (e) => {
                          if (userRole.toLowerCase() !== 'administrador') return;
                          e.preventDefault(); // Evitar cualquier comportamiento por defecto

                          if (!selectedTiquete) return;

                          const tipoActual = selectedTiquete.id_atencion || 'Presencial';
                          const nuevoTipo = tipoActual === 'Presencial' ? 'Virtual' : 'Presencial';

                          console.log('🔄 Cambiando de:', tipoActual, '➡️', nuevoTipo);

                          try {
                            // 1️⃣ Actualizar backend PRIMERO
                            const resultado = await kontrolApi.updateTiqueteAtencion(
                              selectedTiquete.cd_tiquete,
                              nuevoTipo
                            );

                            console.log('✅ API respondió:', resultado);

                            // 2️⃣ Actualizar el estado local con el valor del backend
                            setSelectedTiquete({
                              ...selectedTiquete,
                              id_atencion: resultado.id_atencion // Usar el valor que retorna el backend
                            });

                            // 3️⃣ Actualizar la lista de tiquetes también (si tienes el estado)
                            if (typeof setTiquetes !== 'undefined') {
                              setTiquetes(prevTiquetes =>
                                prevTiquetes.map(t =>
                                  t.cd_tiquete === selectedTiquete.cd_tiquete
                                    ? { ...t, id_atencion: resultado.id_atencion }
                                    : t
                                )
                              );
                            }

                            console.log('✅ Estado actualizado');

                          } catch (error) {
                            console.error('❌ Error:', error);
                            alert(`Error al cambiar tipo de atención: ${error instanceof Error ? error.message : 'Error desconocido'}`);
                          }
                        }}
                        disabled={userRole.toLowerCase() !== 'administrador'}
                        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${(selectedTiquete.id_atencion || 'Presencial') === 'Presencial'
                            ? 'bg-cyan-500 text-white ' + (userRole.toLowerCase() === 'administrador' ? 'hover:bg-cyan-600' : 'opacity-80')
                            : 'bg-pink-500 text-white ' + (userRole.toLowerCase() === 'administrador' ? 'hover:bg-pink-600' : 'opacity-80')
                          }`}
                      >
                        {selectedTiquete.id_atencion || 'Presencial'} {userRole.toLowerCase() === 'administrador' ? '⇄' : ''}
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedTiquete(null)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    ✕
                  </button>
                </div>




                {selectedTiquete.aerolinea && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Aerolínea</h3>
                    <p className="text-gray-600">{selectedTiquete.aerolinea}</p>
                  </div>
                )}

                {selectedTiquete.tipo_reserva && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Tipo de Reserva</h3>
                    <p className="text-gray-600">{selectedTiquete.tipo_reserva}</p>
                  </div>
                )}

                {selectedTiquete.telefono && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Teléfono</h3>
                    <p className="text-gray-600">{selectedTiquete.telefono}</p>
                  </div>
                )}

                {selectedTiquete.id_estado === 'Pendiente' && (
                  <>
                    <div className="md:col-span-2">
                      <h3 className="font-medium text-gray-900 mb-2">
                        Asesor <span className="text-red-500">*</span>
                      </h3>
                      <select
                        value={selectedTiquete.id_asesor || ''}
                        onChange={(e) => setSelectedTiquete({ ...selectedTiquete, id_asesor: e.target.value })}
                        disabled={userRole.toLowerCase() !== 'administrador'}
                        className="w-full px-3 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">Seleccionar asesor...</option>
                        <option value="Jhon Alexander Silva">Jhon Alexander Silva</option>
                        <option value="Wendy Cantillo Maury">Wendy Cantillo Maury</option>
                        <option value="Diana Milena Lozano">Diana Milena Lozano</option>
                        <option value="Lina Paola Lopez">Lina Paola Lopez</option>
                      </select>
                    </div>

                    <div className="md:col-span-2">
                      <h3 className="font-medium text-gray-900 mb-2">Observación</h3>
                      <textarea
                        value={selectedTiquete.id_observacion || ''}
                        onChange={(e) => setSelectedTiquete({ ...selectedTiquete, id_observacion: e.target.value })}
                        disabled={userRole.toLowerCase() !== 'administrador'}
                        placeholder="Ingrese observación"
                        rows={3}
                        className="w-full px-3 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      />
                    </div>



                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Silla</h3>
                      <input
                        type="text"
                        value={selectedTiquete.id_silla || ''}
                        onChange={(e) => setSelectedTiquete({ ...selectedTiquete, id_silla: e.target.value })}
                        disabled={userRole.toLowerCase() !== 'administrador'}
                        placeholder="Ingrese número de silla"
                        className="w-full px-3 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">Cuenta</h3>
                      <input
                        type="text"
                        value={selectedTiquete.id_cuenta || ''}
                        onChange={(e) => setSelectedTiquete({ ...selectedTiquete, id_cuenta: e.target.value })}
                        disabled={userRole.toLowerCase() !== 'administrador'}
                        placeholder="Ingrese cuenta"
                        className="w-full px-3 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </>
                )}

                {selectedTiquete.id_estado === 'Procesado' && (
                  <>
                    {selectedTiquete.id_asesor && (
                      <div className="md:col-span-2">
                        <h3 className="font-medium text-gray-900 mb-2">Procesado por</h3>
                        <p className="text-gray-600">{selectedTiquete.id_asesor}</p>
                        {selectedTiquete.id_hora && (
                          <p className="text-sm text-gray-500">Hora: {selectedTiquete.id_hora}</p>
                        )}
                      </div>
                    )}

                    {selectedTiquete.id_observacion && (
                      <div className="md:col-span-2">
                        <h3 className="font-medium text-gray-900 mb-2">Observación</h3>
                        <p className="text-gray-600 whitespace-pre-wrap">{selectedTiquete.id_observacion}</p>
                      </div>
                    )}

                    {selectedTiquete.id_silla && (
                      <div>
                        <h3 className="font-medium text-gray-900 mb-2">Silla</h3>
                        <p className="text-gray-600">{selectedTiquete.id_silla}</p>
                      </div>
                    )}

                    {selectedTiquete.id_cuenta && (
                      <div>
                        <h3 className="font-medium text-gray-900 mb-2">Cuenta</h3>
                        <p className="text-gray-600">{selectedTiquete.id_cuenta}</p>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="flex gap-4 mt-6 pt-6 border-t border-gray-100">
                {selectedTiquete.id_estado === 'Pendiente' && userRole.toLowerCase() === 'administrador' && (
                  <button
                    onClick={async () => {
                      if (!selectedTiquete.id_asesor?.trim()) {
                        alert('Debe seleccionar un asesor');
                        return;
                      }

                      try {
                        console.log('🚀 Actualizando tiquete:', {
                          cd_tiquete: selectedTiquete.cd_tiquete,
                          id_asesor: selectedTiquete.id_asesor,
                          id_observacion: selectedTiquete.id_observacion,
                          id_silla: selectedTiquete.id_silla,
                          id_cuenta: selectedTiquete.id_cuenta
                        });

                        const response = await kontrolApi.updateTiqueteEstado(
                          selectedTiquete.cd_tiquete,
                          selectedTiquete.id_asesor,
                          selectedTiquete.id_observacion,
                          selectedTiquete.id_silla,
                          selectedTiquete.id_cuenta
                        );

                        console.log('✅ Respuesta exitosa:', response);

                        alert('Tiquete marcado como Procesado exitosamente');
                        setSelectedTiquete(null);
                        cargarDatosIniciales();

                      } catch (error) {
                        console.error('❌ Error completo:', error);
                        alert(`Error al actualizar el tiquete: ${error instanceof Error ? error.message : 'Error desconocido'}`);
                      }
                    }}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                  >
                    Marcar como Procesado
                  </button>
                )}

                <button
                  onClick={() => setSelectedTiquete(null)}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  {selectedTiquete.id_estado === 'Procesado' ? 'Cerrar' : 'Cancelar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
