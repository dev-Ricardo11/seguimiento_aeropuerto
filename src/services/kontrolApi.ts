const API_BASE_URL =
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
    ? import.meta.env.VITE_API_URL
    : 'http://localhost:8000';

// ==================== TIPOS DE DATOS ====================

export interface TiquetesDocumentos {
  cd_tiquete: string;
  ds_paxname: string;
  ds_paxprefix?: string;
  ds_paxape: string;
  ds_itinerario: string;
  dt_salida: string;
  dt_llegada?: string;
  ds_records: string;
  ds_PNR?: string;
  // Campos extraídos del ds_PNR
  aerolinea?: string;
  telefono?: string;
  cd_tiqueteador?: string;
  iden_gds?: number;
  ds_observaciones?: string;
  nombre_tiqueteador?: string;
  tipo_reserva?: string;
  // Campos digitables
  id_asesor?: string;
  id_observacion?: string;
  id_estado?: 'Pendiente' | 'Procesado';
  id_silla?: string;
  id_cuenta?: string;
  id_hora?: string;
  id_atencion?: string;
}

export interface TiquetesDocumentosResponse {
  total: number;
  tiquetes: TiquetesDocumentos[];
  message?: string;
}

export interface TiqueteEstadoUpdate {
  id_asesor: string;
  id_observacion?: string;
  id_silla?: string;
  id_cuenta?: string;
  id_hora: string;
}

export interface TiquetesEstadisticas {
  totalTiquetes: number;
  tiquetesPendientes: number;
  tiquetesProcesados: number;
  fechaActualizacion?: string;
}

// ==================== CLASE API ====================
class KontrolApi {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
      throw new Error(error.detail || `Error HTTP: ${response.status}`);
    }
    return response.json();
  }

  private buildQueryString(params: Record<string, any>): string {
    const validParams = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`);
    return validParams.length > 0 ? `?${validParams.join('&')}` : '';
  }

  // ==================== ENDPOINTS DE AUTENTICACIÓN ====================
  async login(username: string, password: string): Promise<{
    success: boolean;
    message: string;
    user: { username: string };
  }> {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo: username, password }),
    });
    return this.handleResponse(response);
  }

  async verifySession(username: string): Promise<{ valid: boolean; username: string }> {
    const response = await fetch(`${this.baseURL}/auth/verify?username=${encodeURIComponent(username)}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return this.handleResponse(response);
  }

  // ==================== ENDPOINTS DE TIQUETES DOCUMENTOS ====================
  async getTiquetesDocumentos(params?: {
    limit?: number;
    estado?: 'Pendiente' | 'Procesado';
    tipo_vuelo?: string;
  }): Promise<TiquetesDocumentosResponse> {
    const queryString = params ? this.buildQueryString(params) : '';
    const response = await fetch(`${this.baseURL}/TiquetesDocumentos${queryString}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return this.handleResponse<TiquetesDocumentosResponse>(response);
  }

  async updateTiqueteAtencion(
    cd_tiquete: string,
    id_atencion: string
  ): Promise<{ success: boolean; message: string; cd_tiquete: string; id_atencion: string }> {
    const cd_tiquete_clean = cd_tiquete.trim();
    const url = `${this.baseURL}/TiquetesDocumentos/${encodeURIComponent(cd_tiquete_clean)}/atencion`;

    const body = { id_atencion: id_atencion.trim() };

    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return this.handleResponse(response);
  }

  async getTiqueteDocumento(cd_tiquete: string): Promise<{ tiquete: TiquetesDocumentos }> {
    const response = await fetch(`${this.baseURL}/TiquetesDocumentos/${cd_tiquete}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return this.handleResponse<{ tiquete: TiquetesDocumentos }>(response);
  }

  async updateTiqueteEstado(
    cd_tiquete: string,
    id_asesor: string,
    id_observacion?: string,
    id_silla?: string,
    id_cuenta?: string
  ): Promise<{ success: boolean; message: string; cd_tiquete: string }> {
    if (!id_asesor.trim()) {
      throw new Error('Debe seleccionar un asesor');
    }




    const cd_tiquete_clean = cd_tiquete.trim();
    const url = `${this.baseURL}/TiquetesDocumentos/${encodeURIComponent(cd_tiquete_clean)}/estado`;

    const body: TiqueteEstadoUpdate = {
      id_asesor: id_asesor.trim(),
      id_hora: new Date().toLocaleTimeString('es-CO', {
        hour12: false,          // 👈 fuerza formato 24 horas
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    };

    if (id_observacion?.trim()) body.id_observacion = id_observacion.trim();
    if (id_silla?.trim()) body.id_silla = id_silla.trim();
    if (id_cuenta?.trim()) body.id_cuenta = id_cuenta.trim();

    console.log('📤 Enviando actualización:', body);

    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Error response:', errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const result = await this.handleResponse<{ success: boolean; message: string; cd_tiquete: string }>(response);
    console.log('✅ Respuesta del servidor:', result);
    return result;
  }


  async getTiquetesEstadisticas(): Promise<TiquetesEstadisticas> {
    const response = await fetch(`${this.baseURL}/TiquetesDocumentos/estadisticas`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return this.handleResponse<TiquetesEstadisticas>(response);
  }

  // ==================== ENDPOINTS DE SALUD ====================
  async checkHealth(): Promise<{
    status: string;
    database: string;
    name?: string;
    timestamp?: string;
    error?: string;
  }> {
    const response = await fetch(`${this.baseURL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return this.handleResponse(response);
  }
}

const kontrolApi = new KontrolApi();
export default kontrolApi;

// ==================== UTILIDADES ====================
export const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
};

export const getGDSName = (iden_gds: number): string => {
  const gdsMap: { [key: number]: string } = {
    1: 'SABRE',
    2: 'AMADEUS',
    7: 'KIU',
    8: 'KONTROL'
  };
  return gdsMap[iden_gds] || `GDS ${iden_gds}`;
};

export const getGDSColor = (iden_gds: number): string => {
  const colorMap: { [key: number]: string } = {
    1: 'bg-blue-100 text-blue-800 border-blue-200',
    2: 'bg-purple-100 text-purple-800 border-purple-200',
    7: 'bg-green-100 text-green-800 border-green-200',
    8: 'bg-orange-100 text-orange-800 border-orange-200'
  };
  return colorMap[iden_gds] || 'bg-gray-100 text-gray-800 border-gray-200';
};