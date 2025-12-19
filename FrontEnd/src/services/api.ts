/**
 * Cliente API para comunicarse con FastAPI Backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { isTokenExpired } from '../utils/jwt';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id_usuario: number;
    rol: string;
  };
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  document_id?: number;
  filename: string;
  original_filename?: string;
  classification?: 'FACTURA' | 'INFORMACIÓN' | null;
  s3_key?: string;
  s3_bucket?: string;
  extracted_data?: InvoiceData | InformationData | null;
  processing_time_ms?: number;
}

export interface InvoiceData {
  tipo: 'FACTURA';
  cliente?: {
    nombre?: string;
    direccion?: string;
  };
  proveedor?: {
    nombre?: string;
    direccion?: string;
  };
  numero_factura?: string;
  fecha?: string;
  productos?: Array<{
    cantidad?: string;
    nombre?: string;
    precio_unitario?: string;
    total?: string;
  }>;
  subtotal?: string;
  iva?: string;
  total?: string;  // Backend puede devolver 'total' o 'total_factura'
  total_factura?: string;
}

export interface InformationData {
  tipo: 'INFORMACIÓN';
  descripcion?: string;
  resumen?: string;
  sentimiento?: 'positivo' | 'negativo' | 'neutral';
}

export interface Document {
  id: number;
  filename: string;
  original_filename?: string;
  file_type: string;
  classification?: 'FACTURA' | 'INFORMACIÓN' | null;
  uploaded_at: string;
  processed_at?: string | null;
  extracted_data?: InvoiceData | InformationData | null;
  s3_key?: string | null;
  s3_bucket?: string | null;
  file_size?: number | null;
}

export interface DocumentsListResponse {
  total: number;
  page: number;
  limit: number;
  documents: Document[];
}

class APIService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para agregar token a las peticiones
    this.api.interceptors.request.use((config) => {
      const token = this.getToken();
      if (token) {
        // Verificar si el token está expirado antes de agregarlo
        if (isTokenExpired(token)) {
          // Token expirado, limpiar y redirigir
          this.logout();
          window.location.href = '/login';
          return Promise.reject(new Error('Token expirado'));
        }
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Interceptor para manejar errores de autenticación
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expirado o inválido
          this.logout();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Obtener token del localStorage
   */
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Guardar token en localStorage
   */
  setToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  /**
   * Login - Iniciar sesión
   */
  async login(rol?: string): Promise<LoginResponse> {
    const response = await this.api.post<LoginResponse>('/api/v1/auth/login', rol ? { rol } : {});
    if (response.data.access_token) {
      this.setToken(response.data.access_token);
    }
    return response.data;
  }

  /**
   * Renovar token
   */
  async renewToken(): Promise<LoginResponse> {
    const response = await this.api.post<LoginResponse>('/api/v1/auth/renew');
    if (response.data.access_token) {
      this.setToken(response.data.access_token);
    }
    return response.data;
  }

  /**
   * Subir documento para análisis
   */
  async uploadDocument(
    file: File,
    onUploadProgress?: (progressEvent: any) => void
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post<DocumentUploadResponse>(
      '/api/v1/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress,
      }
    );

    return response.data;
  }

  /**
   * Obtener documento por ID
   */
  async getDocument(documentId: number): Promise<Document> {
    const response = await this.api.get<Document>(`/api/v1/documents/${documentId}`);
    return response.data;
  }

  /**
   * Obtener lista de documentos
   */
  async getDocuments(filters?: {
    classification?: 'FACTURA' | 'INFORMACIÓN';
    date_from?: string;
    date_to?: string;
    page?: number;
    limit?: number;
  }): Promise<DocumentsListResponse> {
    const response = await this.api.get<DocumentsListResponse>('/api/v1/documents', {
      params: filters,
    });
    return response.data;
  }

  /**
   * Verificar si el usuario está autenticado
   * Verifica que exista el token Y que no esté expirado
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) {
      return false;
    }

    // Verificar si el token está expirado
    if (isTokenExpired(token)) {
      // Token expirado, limpiar y retornar false
      this.logout();
      return false;
    }

    return true;
  }

  /**
   * Cerrar sesión
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
  }
}

export const apiService = new APIService();

