import React from 'react';
import { TrendingUp, Users, MapPin, DollarSign } from 'lucide-react';
import { Reserva } from './ReservaCard';

interface StatsCardsProps {
  reservas: Reserva[];
}

const StatsCards: React.FC<StatsCardsProps> = ({ reservas }) => {
  const totalReservas = reservas.length;
  const reservasActivas = reservas.filter(r => r.estado === 'confirmada' || r.estado === 'en-curso').length;
  const totalPasajeros = reservas.reduce((sum, r) => sum + r.pasajeros, 0);
  const ingresoTotal = reservas.reduce((sum, r) => sum + r.precio, 0);

  const stats = [
    {
      title: 'Total Reservas',
      value: totalReservas.toString(),
      icon: TrendingUp,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Reservas Activas',
      value: reservasActivas.toString(),
      icon: MapPin,
      color: 'text-green-500',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Total Pasajeros',
      value: totalPasajeros.toString(),
      icon: Users,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'Ingresos Total',
      value: `$${ingresoTotal.toLocaleString()}`,
      icon: DollarSign,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50'
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