import React from 'react';
import { Calendar, MapPin, Users, Clock, CheckCircle, XCircle } from 'lucide-react';

export interface Reserva {
  id: string;
  numeroReserva: string;
  cliente: string;
  email: string;
  telefono: string;
  fechaSalida: string;
  fechaRegreso: string | null;
  destino: string;
  origen: string;
  tipoViaje: string;
  estado: string;
  empresa: string;
  precioTotal: number;
  moneda: string;
  notas: string | null;
  fechaCreacion: string;
  fechaActualizacion: string;
}

interface ReservaCardProps {
  reserva: Reserva;
  onClick: () => void;
}

const ReservaCard: React.FC<ReservaCardProps> = ({ reserva, onClick }) => {
  const getEstadoColor = (estado: string) => {
    switch (estado.toLowerCase()) {
      case 'pendiente':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'confirmada':
      case 'activa':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'en-curso':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'completada':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'cancelada':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getEstadoIcon = (estado: string) => {
    switch (estado.toLowerCase()) {
      case 'pendiente':
        return <Clock className="w-4 h-4" />;
      case 'confirmada':
      case 'activa':
      case 'en-curso':
      case 'completada':
        return <CheckCircle className="w-4 h-4" />;
      case 'cancelada':
        return <XCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const formatFecha = (fecha: string) => {
    if (!fecha) return '';
    try {
      return new Date(fecha).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return fecha;
    }
  };

  return (
    <div 
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 cursor-pointer transform hover:scale-[1.02]"
      onClick={onClick}
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              #{reserva.numeroReserva}
            </h3>
            <p className="text-gray-600">{reserva.cliente}</p>
            <p className="text-gray-600">{reserva.empresa}</p>
          </div>
          <div className={`px-3 py-1 rounded-full border text-sm font-medium flex items-center gap-1 ${getEstadoColor(reserva.estado)}`}>
            {getEstadoIcon(reserva.estado)}
            {reserva.estado}
          </div>
        </div>

        <div className="space-y-3 mb-4">
          <div className="flex items-center text-gray-600">
            <MapPin className="w-4 h-4 mr-2 text-blue-500" />
            <span className="text-sm">{reserva.origen} → {reserva.destino}</span>
          </div>
          
          <div className="flex items-center text-gray-600">
            <Calendar className="w-4 h-4 mr-2 text-blue-500" />
            <span className="text-sm">
              {formatFecha(reserva.fechaSalida)}
              {reserva.fechaRegreso && ` - ${formatFecha(reserva.fechaRegreso)}`}
            </span>
          </div>
          
          <div className="flex items-center text-gray-600">
            <Users className="w-4 h-4 mr-2 text-blue-500" />
            <span className="text-sm">{reserva.tipoViaje}</span>
          </div>
        </div>

        <div className="flex justify-between items-center pt-4 border-t border-gray-100">
          <span className="text-2xl font-bold text-gray-900">
            {(reserva.precioTotal || 0).toLocaleString()} {reserva.moneda || 'USD'}
          </span>
          <span className="text-sm text-gray-500">
            {reserva.email}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ReservaCard;