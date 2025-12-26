import React from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';

export interface FilterState {
  busqueda: string;
  fechaDesde: string;
  fechaHasta: string;
  empresa: string;
  estado: string;
  destino: string;
  tipo_vuelo: string; // Added field
}

interface FilterPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onReset: () => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ filters, onFiltersChange, onReset }) => {
  const handleInputChange = (field: keyof FilterState, value: string) => {
    onFiltersChange({
      ...filters,
      [field]: value
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Filter className="w-5 h-5 text-blue-500" />
          Filtros de Búsqueda
        </h2>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
        >
          <RotateCcw className="w-4 h-4" />
          Limpiar
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar cliente o reserva..."
            value={filters.busqueda}
            onChange={(e) => handleInputChange('busqueda', e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          />
        </div>

        <div>
          <input
            type="date"
            placeholder="Fecha desde"
            value={filters.fechaDesde}
            onChange={(e) => handleInputChange('fechaDesde', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          />
        </div>

        <div>
          <input
            type="date"
            placeholder="Fecha hasta"
            value={filters.fechaHasta}
            onChange={(e) => handleInputChange('fechaHasta', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          />
        </div>

        <div>
          <select
            value={filters.tipo_vuelo || ""}
            onChange={(e) => handleInputChange('tipo_vuelo', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          >
            <option value="">Trayectos (Todos)</option>
            <option value="IDA">Vuelos - Ida</option>
            <option value="REG">Vuelos - Regreso</option>
          </select>
        </div>

        <div>
          <select
            value={filters.estado}
            onChange={(e) => handleInputChange('estado', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
          >
            <option value="">Todos los estados</option>
            <option value="Pendiente">Pendiente</option>
            <option value="Procesado">Procesado</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;