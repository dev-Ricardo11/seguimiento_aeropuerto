import React from 'react';
import { MapPin, User, Plane, Hash, Building2 } from 'lucide-react';
import { TiquetesDocumentos, getGDSName, getGDSColor } from '../services/kontrolApi';
 
interface ReservaCardProps {
  tiquete: TiquetesDocumentos;
  onClick: () => void;
}
 
const ReservaCard: React.FC<ReservaCardProps> = ({ tiquete, onClick }) => {
  const formatFecha = (fecha: string | null | undefined) => {
    if (!fecha) return 'N/A';
    try {
      return new Date(fecha).toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return fecha;
    }
  };
 
  const getEstadoConfig = (estado: string | undefined) => {
    if (estado === 'Procesado') {
      return { texto: 'Procesado', color: 'bg-green-100 text-green-800 border-green-200' };
    }
    return { texto: 'Pendiente', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' };
  };
 
  const estadoConfig = getEstadoConfig(tiquete.id_estado);
  const gdsName = getGDSName(tiquete.iden_gds ?? 0);
  const gdsColor = getGDSColor(tiquete.iden_gds ?? 0);
 
  return (
<div
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 cursor-pointer transform hover:scale-[1.02]"
      onClick={onClick}
>
<div className="p-6">
<div className="flex justify-between items-start mb-4">
<div>
<div className="flex items-center gap-2 mb-2">
<Hash className="w-4 h-4 text-gray-500" />
<h3 className="text-lg font-semibold text-gray-900">
                {tiquete.ds_records}
</h3>
</div>
 
            <div className="flex items-center gap-2 text-gray-600">
<User className="w-4 h-4 text-blue-500" />
<p className="font-medium">
                {tiquete.ds_paxname} {tiquete.ds_paxape}
</p>
</div>
 
            {tiquete.telefono && (
<p className="text-sm text-gray-500 mt-1">Tel: {tiquete.telefono}</p>
            )}
</div>
 
          <div className="flex flex-col items-end gap-2">
<div className={`px-3 py-1 rounded-full border text-sm font-medium ${estadoConfig.color}`}>
              {estadoConfig.texto}
</div>
<div className={`px-3 py-1 rounded-full border text-xs font-medium ${gdsColor}`}>
              {gdsName}
</div>
</div>
</div>
 
        <div className="space-y-3 mb-4">
          {tiquete.ds_itinerario && (
<div className="flex items-center text-gray-600">
<MapPin className="w-4 h-4 mr-2 text-blue-500" />
<span className="text-sm font-medium">{tiquete.ds_itinerario}</span>
</div>
          )}
 
          <div className="grid grid-cols-2 gap-4">
            {tiquete.dt_salida && (
<div className="flex items-center text-gray-600">
<Plane className="w-4 h-4 mr-2 text-blue-500 transform rotate-45" />
<div className="text-sm">
<div className="font-medium">Salida</div>
<div className="text-xs">{formatFecha(tiquete.dt_salida)}</div>
                  {tiquete.dt_llegada && (
<div className="text-xs text-gray-500">{formatFecha(tiquete.dt_llegada)}</div>
                  )}
</div>
</div>
            )}
 
            {tiquete.aerolinea && (
<div className="flex items-center text-gray-600">
<Building2 className="w-4 h-4 mr-2 text-blue-500" />
<div className="text-sm">
<div className="font-medium">Aerolínea</div>
<div className="text-xs">{tiquete.aerolinea}</div>
</div>
</div>
            )}
</div>
</div>
 
        {tiquete.nombre_tiqueteador && (
<div className="mb-3 pb-3 border-b border-gray-100">
<div className="flex items-center gap-2 text-xs text-gray-500">
<User className="w-3 h-3" />
<span>Tiqueteador: <span className="font-medium">{tiquete.nombre_tiqueteador}</span></span>
</div>
</div>
        )}
 
        {tiquete.id_asesor && (
<div className="pt-4 border-t border-gray-100">
<div className="flex items-center gap-2 text-xs text-gray-500">
<User className="w-3 h-3" />
<span>Asesor: <span className="font-medium">{tiquete.id_asesor}</span></span>
              {tiquete.id_hora && (
<span className="ml-2">Hora: {tiquete.id_hora}</span>
              )}
</div>
</div>
        )}

        
  {tiquete.id_atencion && (
  <div className="flex items-center justify-between pt-2 border-t border-gray-100">
    <span className="text-sm text-gray-600">Atención:</span>
    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
      tiquete.id_atencion === 'Presencial' 
        ? 'bg-cyan-500 text-white'
        : 'bg-pink-500 text-white'
    }`}>
      {tiquete.id_atencion}
    </span>
  </div>
)}

</div>
</div>
  );
};
 
export default ReservaCard;