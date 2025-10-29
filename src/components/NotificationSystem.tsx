import React, { useState } from 'react';
import { Bell, X, Info, CheckCircle, AlertTriangle } from 'lucide-react';

export interface Notification {
  id: string;
  empresa: string;
  titulo: string;
  mensaje: string;
  tipo: 'info' | 'success' | 'warning';
  timestamp: Date;
  leida: boolean;
}

interface NotificationSystemProps {
  notifications: Notification[];
  onMarkAsRead: (id: string) => void;
  onDismiss: (id: string) => void;
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({
  notifications,
  onMarkAsRead,
  onDismiss
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const unreadCount = notifications.filter(n => !n.leida).length;

  const getNotificationIcon = (tipo: Notification['tipo']) => {
    switch (tipo) {
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getNotificationBgColor = (tipo: Notification['tipo']) => {
    switch (tipo) {
      case 'info':
        return 'border-l-blue-500 bg-blue-50';
      case 'success':
        return 'border-l-green-500 bg-green-50';
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50';
    }
  };

  return (
  <div className="relative flex items-center gap-2">
      {/* Botón de notificaciones */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      
      <button
        onClick={() => window.open('http://localhost:8501', '_blank')}
        className="flex items-center gap-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
      >
        <Info className="w-5 h-5" />
        <span className="text-sm font-medium">Gestión Aeropuero</span>
      </button>

      {/* Dropdown de notificaciones */}
      {showDropdown && (
        <div className="absolute right-0 top-12 w-96 max-h-96 bg-white rounded-xl shadow-lg border border-gray-200 z-50 overflow-hidden">
          ...
        </div>
      )}
  
      
          
           

      {showDropdown && (
        <div className="absolute right-0 top-12 w-96 max-h-96 bg-white rounded-xl shadow-lg border border-gray-200 z-50 overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Notificaciones</h3>
            <p className="text-sm text-gray-600">{unreadCount} sin leer</p>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p>No hay notificaciones</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-l-4 ${getNotificationBgColor(notification.tipo)} ${
                    !notification.leida ? 'bg-opacity-100' : 'bg-opacity-50'
                  } hover:bg-opacity-80 transition-colors duration-200`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getNotificationIcon(notification.tipo)}
                        <h4 className="font-medium text-gray-900 text-sm">
                          {notification.titulo}
                        </h4>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        {notification.mensaje}
                      </p>
                      <p className="text-xs text-gray-400">
                        {notification.timestamp.toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-1 ml-2">
                      {!notification.leida && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onMarkAsRead(notification.id);
                          }}
                          className="text-blue-500 hover:text-blue-700 text-xs"
                        >
                          Marcar leída
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDismiss(notification.id);
                        }}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSystem;