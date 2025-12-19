import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { toast } from 'react-toastify';
import './EventsHistory.css';

interface Event {
  id: number;
  event_type: string;
  description: string;
  document_id?: number;
  document_filename?: string;
  document_classification?: string;
  user_id?: number;
  created_at: string;
}

interface EventsResponse {
  events: Event[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const EventsHistory: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    event_type: '' as 'DOCUMENT_UPLOAD' | 'AI_PROCESSING' | 'USER_INTERACTION' | '',
    description_search: '',
    date_from: '',
    date_to: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 50,
    total: 0,
    total_pages: 0,
  });

  useEffect(() => {
    loadEvents();
  }, [filters, pagination.page]);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        toast.error('No hay token de autenticación');
        return;
      }

      const params = new URLSearchParams();
      params.append('page', pagination.page.toString());
      params.append('page_size', pagination.page_size.toString());

      if (filters.event_type) {
        params.append('event_type', filters.event_type);
      }
      if (filters.description_search) {
        params.append('description_search', filters.description_search);
      }
      if (filters.date_from) {
        params.append('date_from', filters.date_from);
      }
      if (filters.date_to) {
        params.append('date_to', filters.date_to);
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/history?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error al cargar eventos');
      }

      const data: EventsResponse = await response.json();
      setEvents(data.events);
      setPagination((prev) => ({
        ...prev,
        total: data.total,
        total_pages: data.total_pages,
      }));
    } catch (error: any) {
      toast.error('Error al cargar el historial de eventos');
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
      if (filters.event_type) {
        params.append('event_type', filters.event_type);
      }
      if (filters.description_search) {
        params.append('description_search', filters.description_search);
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
      link.download = `historial_eventos_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      toast.success('Historial de eventos exportado correctamente');
    } catch (error: any) {
      toast.error('Error al exportar historial');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm:ss');
    } catch {
      return dateString;
    }
  };

  const getEventTypeLabel = (eventType: string) => {
    const labels: Record<string, string> = {
      'DOCUMENT_UPLOAD': 'Carga de Documento',
      'AI_PROCESSING': 'Procesamiento IA',
      'USER_INTERACTION': 'Interacción del Usuario',
    };
    return labels[eventType] || eventType;
  };

  const getEventTypeBadgeClass = (eventType: string) => {
    const classes: Record<string, string> = {
      'DOCUMENT_UPLOAD': 'badge-upload',
      'AI_PROCESSING': 'badge-ai',
      'USER_INTERACTION': 'badge-interaction',
    };
    return classes[eventType] || 'badge-default';
  };

  return (
    <div className="events-history">
      <div className="history-container">
        <div className="history-header">
          <h2>Historial de Eventos</h2>
          <button onClick={handleExportExcel} className="btn btn-primary" disabled={loading}>
            Exportar a Excel
          </button>
        </div>

        <div className="filters-section">
          <h3>Filtros</h3>
          <div className="filters-grid">
            <div className="filter-item">
              <label htmlFor="event_type">Tipo de Evento</label>
              <select
                id="event_type"
                value={filters.event_type}
                onChange={(e) =>
                  handleFilterChange('event_type', e.target.value)
                }
                className="form-control"
              >
                <option value="">Todos</option>
                <option value="DOCUMENT_UPLOAD">Carga de Documento</option>
                <option value="AI_PROCESSING">Procesamiento IA</option>
                <option value="USER_INTERACTION">Interacción del Usuario</option>
              </select>
            </div>

            <div className="filter-item">
              <label htmlFor="description_search">Buscar en Descripción</label>
              <input
                type="text"
                id="description_search"
                value={filters.description_search}
                onChange={(e) => handleFilterChange('description_search', e.target.value)}
                className="form-control"
                placeholder="Buscar..."
              />
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
                  setFilters({
                    event_type: '',
                    description_search: '',
                    date_from: '',
                    date_to: '',
                  });
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
          <div className="loading">Cargando eventos...</div>
        ) : events.length === 0 ? (
          <div className="empty-state">
            <p>No se encontraron eventos</p>
          </div>
        ) : (
          <>
            <div className="events-list">
              <table className="events-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Tipo</th>
                    <th>Descripción</th>
                    <th>Documento</th>
                    <th>Fecha y Hora</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id}>
                      <td className="event-id">{event.id}</td>
                      <td>
                        <span className={`badge ${getEventTypeBadgeClass(event.event_type)}`}>
                          {getEventTypeLabel(event.event_type)}
                        </span>
                      </td>
                      <td className="event-description">{event.description}</td>
                      <td className="event-document">
                        {event.document_filename ? (
                          <div>
                            <div className="document-name">{event.document_filename}</div>
                            {event.document_classification && (
                              <span className="document-classification">
                                {event.document_classification}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="no-document">-</span>
                        )}
                      </td>
                      <td className="event-date">{formatDate(event.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
                Página {pagination.page} de {pagination.total_pages} ({pagination.total} eventos)
              </span>
              <button
                onClick={() =>
                  setPagination((prev) => ({
                    ...prev,
                    page: prev.page + 1,
                  }))
                }
                disabled={pagination.page >= pagination.total_pages}
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

export default EventsHistory;

