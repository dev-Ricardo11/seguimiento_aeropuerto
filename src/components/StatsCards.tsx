import React from 'react';
import { FileText, Users, Clock, CheckCircle } from 'lucide-react';
import { TiquetesDocumentos } from '../services/kontrolApi';
 
interface StatsCardsProps {
  tiquetes: TiquetesDocumentos[];
}
 
const StatsCards: React.FC<StatsCardsProps> = ({ tiquetes }) => {
  const totalTiquetes = tiquetes.length;
  const tiquetesPendientes = tiquetes.filter(t => t.id_estado === 'Pendiente').length;
  const tiquetesProcesados = tiquetes.filter(t => t.id_estado === 'Procesado').length;
 
  const pasajerosUnicos = new Set(
    tiquetes
      .filter(t => t.ds_paxname && t.ds_paxape)
      .map(t => `${t.ds_paxname} ${t.ds_paxape}`)
  ).size;
 
  const stats = [
    {
      title: 'Total Tiquetes',
      value: totalTiquetes.toString(),
      icon: FileText,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Pasajeros',
      value: pasajerosUnicos.toString(),
      icon: Users,
      color: 'text-green-500',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Pendientes',
      value: tiquetesPendientes.toString(),
      icon: Clock,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50'
    },
    {
      title: 'Procesados',
      value: tiquetesProcesados.toString(),
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-50'
    }
  ];
 
  return (
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      {stats.map((stat, index) => (
<div key={index} className="bg-white rounded-xl shadow-md border border-gray-100 p-6 hover:shadow-lg transition-shadow duration-300">
<div className="flex items-center justify-between">
<div>
<p className="text-sm font-medium text-gray-600 mb-1">{stat.title}</p>
<p className="text-2xl font-bold text-gray-900">{stat.value}</p>
</div>
<div className={`p-3 rounded-lg ${stat.bgColor}`}>
<stat.icon className={`w-6 h-6 ${stat.color}`} />
</div>
</div>
</div>
      ))}
</div>
  );
};
 
export default StatsCards;