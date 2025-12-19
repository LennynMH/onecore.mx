import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { apiService, Document, DocumentsListResponse } from '../services/api';
import { toast } from 'react-toastify';
import './DocumentHistory.css';

const DocumentHistory: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    classification: '' as 'FACTURA' | 'INFORMACIÓN' | '',
    date_from: '',
    date_to: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
  });

  useEffect(() => {
    loadDocuments();
  }, [filters, pagination.page]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: pagination.page,
        limit: pagination.limit,
      };

      if (filters.classification) {
        params.classification = filters.classification;
      }
      if (filters.date_from) {
        params.date_from = filters.date_from;
      }
      if (filters.date_to) {
        params.date_to = filters.date_to;
      }

      const response: DocumentsListResponse = await apiService.getDocuments(params);
      setDocuments(response.documents);
      setPagination((prev) => ({
        ...prev,
        total: response.total,
      }));
    } catch (error: any) {
      toast.error('Error al cargar el historial');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleExportExcel = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        toast.error('No hay token de autenticación');
        return;
      }

      // Construir URL con filtros
      const params = new URLSearchParams();
      if (filters.classification) {
        params.append('classification', filters.classification);
      }
      if (filters.date_from) {
        params.append('date_from', filters.date_from);
      }
      if (filters.date_to) {
        params.append('date_to', filters.date_to);
      }

      const url = `http://localhost:8000/api/v1/history/export?${params.toString()}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Error al exportar historial');
      }

      // Descargar archivo
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `historial_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      toast.success('Historial exportado correctamente');
    } catch (error: any) {
      toast.error('Error al exportar historial');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="document-history">
      <div className="history-container">
        <div className="history-header">
          <h2>Historial de Documentos</h2>
          <button onClick={handleExportExcel} className="btn btn-primary">
            Exportar a Excel
          </button>
        </div>

        <div className="filters-section">
          <h3>Filtros</h3>
          <div className="filters-grid">
            <div className="filter-item">
              <label htmlFor="classification">Tipo de Documento</label>
              <select
                id="classification"
                value={filters.classification}
                onChange={(e) =>
                  handleFilterChange('classification', e.target.value)
                }
                className="form-control"
              >
                <option value="">Todos</option>
                <option value="FACTURA">Factura</option>
                <option value="INFORMACIÓN">Información</option>
              </select>
            </div>

            <div className="filter-item">
              <label htmlFor="date_from">Fecha Desde</label>
              <input
                type="date"
                id="date_from"
                value={filters.date_from}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                className="form-control"
              />
            </div>

            <div className="filter-item">
              <label htmlFor="date_to">Fecha Hasta</label>
              <input
                type="date"
                id="date_to"
                value={filters.date_to}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                className="form-control"
              />
            </div>

            <div className="filter-item">
              <button
                onClick={() => {
                  setFilters({ classification: '', date_from: '', date_to: '' });
                  setPagination((prev) => ({ ...prev, page: 1 }));
                }}
                className="btn btn-secondary"
              >
                Limpiar Filtros
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="loading">Cargando documentos...</div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <p>No se encontraron documentos</p>
          </div>
        ) : (
          <>
            <div className="documents-list">
              {documents.map((doc) => (
                <div key={doc.id} className="document-card">
                  <div className="document-header">
                    <div className="document-title">
                      <span className="document-icon">
                        {doc.classification === 'FACTURA' ? '📄' : '📋'}
                      </span>
                      <h3>{doc.filename}</h3>
                    </div>
                    <span
                      className={`badge ${doc.classification.toLowerCase()}`}
                    >
                      {doc.classification}
                    </span>
                  </div>

                  <div className="document-info">
                    <div className="info-row">
                      <span className="label">Tipo de archivo:</span>
                      <span className="value">{doc.file_type}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">Subido:</span>
                      <span className="value">{formatDate(doc.uploaded_at)}</span>
                    </div>
                    {doc.processed_at && (
                      <div className="info-row">
                        <span className="label">Procesado:</span>
                        <span className="value">{formatDate(doc.processed_at)}</span>
                      </div>
                    )}
                  </div>

                  <div className="document-preview">
                    <h4>Datos Extraídos:</h4>
                    <pre className="extracted-data">
                      {JSON.stringify(doc.extracted_data, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>

            <div className="pagination">
              <button
                onClick={() =>
                  setPagination((prev) => ({
                    ...prev,
                    page: Math.max(1, prev.page - 1),
                  }))
                }
                disabled={pagination.page === 1}
                className="btn btn-secondary"
              >
                Anterior
              </button>
              <span className="page-info">
                Página {pagination.page} de{' '}
                {Math.ceil(pagination.total / pagination.limit)}
              </span>
              <button
                onClick={() =>
                  setPagination((prev) => ({
                    ...prev,
                    page: prev.page + 1,
                  }))
                }
                disabled={
                  pagination.page >= Math.ceil(pagination.total / pagination.limit)
                }
                className="btn btn-secondary"
              >
                Siguiente
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DocumentHistory;

