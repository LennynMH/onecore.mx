import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { DocumentUploadResponse, InvoiceData, InformationData } from '../services/api';
import * as XLSX from 'xlsx';
import { toast } from 'react-toastify';
import './DocumentResults.css';

// Función helper para formatear precios
const formatPrice = (value?: string): string => {
  if (!value || value === '-') return '-';
  // Remover caracteres no numéricos excepto punto y coma
  const cleaned = value.replace(/[^\d.,]/g, '');
  if (!cleaned) return value;
  // Convertir coma a punto si es necesario
  const normalized = cleaned.replace(',', '.');
  const num = parseFloat(normalized);
  if (isNaN(num)) return value;
  return `$${num.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const DocumentResults: React.FC = () => {
  const [result, setResult] = useState<DocumentUploadResponse | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const savedResult = localStorage.getItem('last_analysis_result');
    if (savedResult) {
      try {
        const parsed = JSON.parse(savedResult);
        setResult(parsed);
      } catch (error) {
        console.error('Error parsing result:', error);
        navigate('/upload');
      }
    } else {
      navigate('/upload');
    }
  }, [navigate]);

  if (!result) {
    return (
      <div className="document-results">
        <div className="loading">Cargando resultados...</div>
      </div>
    );
  }

  const isInvoice = result.classification === 'FACTURA';
  const extractedData = result.extracted_data as InvoiceData | InformationData;

  return (
    <div className="document-results">
      <div className="results-container">
        <div className="results-header">
          <h2>Resultados del Análisis</h2>
          <button onClick={() => navigate('/upload')} className="btn btn-secondary">
            Analizar Otro Documento
          </button>
        </div>

        <div className="result-card">
          <div className="result-section">
            <h3>Información del Documento</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Archivo:</span>
                <span className="value">{result.filename}</span>
              </div>
              <div className="info-item">
                <span className="label">Clasificación:</span>
                <span className={`value badge ${result.classification.toLowerCase()}`}>
                  {result.classification}
                </span>
              </div>
              {result.processing_time_ms && (
                <div className="info-item">
                  <span className="label">Tiempo de procesamiento:</span>
                  <span className="value">{result.processing_time_ms} ms</span>
                </div>
              )}
            </div>
          </div>

          {isInvoice && (
            <div className="result-section">
              <h3>Datos de la Factura</h3>
              <InvoiceView data={extractedData as InvoiceData} />
            </div>
          )}

          {!isInvoice && (
            <div className="result-section">
              <h3>Datos Extraídos</h3>
              <InformationView data={extractedData as InformationData} />
            </div>
          )}

          <div className="result-actions">
            <button
              onClick={() => navigate('/history')}
              className="btn btn-primary"
            >
              Ver Historial
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="btn btn-secondary"
            >
              Analizar Otro
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const InvoiceView: React.FC<{ data: InvoiceData }> = ({ data }) => {
  return (
    <div className="invoice-view">
      <div className="invoice-section">
        <h4>Cliente</h4>
        <div className="data-grid">
          {data.cliente?.nombre && (
            <div className="data-item">
              <span className="data-label">Nombre:</span>
              <span className="data-value">{data.cliente.nombre}</span>
            </div>
          )}
          {data.cliente?.direccion && (
            <div className="data-item">
              <span className="data-label">Dirección:</span>
              <span className="data-value">{data.cliente.direccion}</span>
            </div>
          )}
        </div>
      </div>

      <div className="invoice-section">
        <h4>Proveedor</h4>
        <div className="data-grid">
          {data.proveedor?.nombre && (
            <div className="data-item">
              <span className="data-label">Nombre:</span>
              <span className="data-value">{data.proveedor.nombre}</span>
            </div>
          )}
          {data.proveedor?.direccion && (
            <div className="data-item">
              <span className="data-label">Dirección:</span>
              <span className="data-value">{data.proveedor.direccion}</span>
            </div>
          )}
        </div>
      </div>

      <div className="invoice-section">
        <h4>Información de Factura</h4>
        <div className="data-grid">
          {data.numero_factura && (
            <div className="data-item">
              <span className="data-label">Número:</span>
              <span className="data-value">{data.numero_factura}</span>
            </div>
          )}
          {data.fecha && (
            <div className="data-item">
              <span className="data-label">Fecha:</span>
              <span className="data-value">{data.fecha}</span>
            </div>
          )}
        </div>
      </div>

      {data.productos && data.productos.length > 0 && (
        <ProductsTable 
          productos={data.productos} 
          subtotal={data.subtotal}
          iva={data.iva}
          total={data.total || data.total_factura}
        />
      )}
    </div>
  );
};

const InformationView: React.FC<{ data: InformationData }> = ({ data }) => {
  const getSentimentClass = (sentimiento?: string) => {
    if (!sentimiento) return '';
    return `sentiment-${sentimiento}`;
  };

  return (
    <div className="information-view">
      {data.descripcion && (
        <div className="info-section">
          <h4>Descripción</h4>
          <p className="description-text">{data.descripcion}</p>
        </div>
      )}

      {data.resumen && (
        <div className="info-section">
          <h4>Resumen del Contenido</h4>
          <p className="summary-text">{data.resumen}</p>
        </div>
      )}

      {data.sentimiento && (
        <div className="info-section">
          <h4>Análisis de Sentimiento</h4>
          <div className={`sentiment-badge ${getSentimentClass(data.sentimiento)}`}>
            {data.sentimiento.toUpperCase()}
          </div>
        </div>
      )}
    </div>
  );
};

type SortField = 'cantidad' | 'nombre' | 'precio_unitario' | 'total';
type SortDirection = 'asc' | 'desc';

interface ProductsTableProps {
  productos: Array<{
    cantidad?: string;
    nombre?: string;
    precio_unitario?: string;
    total?: string;
  }>;
  subtotal?: string;
  iva?: string;
  total?: string;
}

const ProductsTable: React.FC<ProductsTableProps> = ({ productos, subtotal, iva, total }) => {
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [filterText, setFilterText] = useState('');

  // Función para parsear valor numérico para ordenamiento
  const parseNumericValue = (value?: string): number => {
    if (!value || value === '-') return 0;
    const cleaned = value.replace(/[^\d.,]/g, '').replace(',', '.');
    const num = parseFloat(cleaned);
    return isNaN(num) ? 0 : num;
  };

  // Filtrar productos
  const filteredProductos = useMemo(() => {
    if (!filterText) return productos;
    const lowerFilter = filterText.toLowerCase();
    return productos.filter(
      (p) =>
        p.nombre?.toLowerCase().includes(lowerFilter) ||
        p.cantidad?.includes(lowerFilter) ||
        p.precio_unitario?.includes(lowerFilter) ||
        p.total?.includes(lowerFilter)
    );
  }, [productos, filterText]);

  // Ordenar productos
  const sortedProductos = useMemo(() => {
    if (!sortField) return filteredProductos;
    return [...filteredProductos].sort((a, b) => {
      let aValue: string | number = a[sortField] || '';
      let bValue: string | number = b[sortField] || '';

      // Para campos numéricos, convertir a número
      if (sortField === 'cantidad' || sortField === 'precio_unitario' || sortField === 'total') {
        aValue = parseNumericValue(a[sortField]);
        bValue = parseNumericValue(b[sortField]);
      } else {
        aValue = (aValue as string).toLowerCase();
        bValue = (bValue as string).toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredProductos, sortField, sortDirection]);

  // Calcular resumen
  const summary = useMemo(() => {
    const totalProductos = sortedProductos.length;
    const sumaTotales = sortedProductos.reduce((sum, p) => {
      return sum + parseNumericValue(p.total);
    }, 0);
    return { totalProductos, sumaTotales };
  }, [sortedProductos]);

  // Manejar ordenamiento
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Exportar a Excel
  const handleExportExcel = () => {
    try {
      const worksheetData = [
        ['Cantidad', 'Nombre', 'Precio Unitario', 'Total'],
        ...sortedProductos.map((p) => [
          p.cantidad || '-',
          p.nombre || '-',
          p.precio_unitario || '-',
          p.total || '-',
        ]),
        [],
        ['Suma de Totales', formatPrice(summary.sumaTotales.toString())],
      ];

      const ws = XLSX.utils.aoa_to_sheet(worksheetData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Productos');

      const fileName = `productos_${new Date().toISOString().split('T')[0]}.xlsx`;
      XLSX.writeFile(wb, fileName);
      toast.success('Archivo Excel exportado correctamente');
    } catch (error) {
      console.error('Error al exportar a Excel:', error);
      toast.error('Error al exportar a Excel');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return '⇅';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="invoice-section products-section">
      <div className="products-header">
        <h4>Productos</h4>
        <div className="products-actions">
          <input
            type="text"
            placeholder="Buscar productos..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="products-filter"
          />
          <button onClick={handleExportExcel} className="btn btn-export">
            Exportar a Excel
          </button>
        </div>
      </div>

      <div className="products-table-container">
        <div className="products-table">
          <table>
            <thead>
              <tr>
                <th
                  className="sortable numeric"
                  onClick={() => handleSort('cantidad')}
                >
                  Cantidad {getSortIcon('cantidad')}
                </th>
                <th className="sortable" onClick={() => handleSort('nombre')}>
                  Nombre {getSortIcon('nombre')}
                </th>
                <th
                  className="sortable numeric"
                  onClick={() => handleSort('precio_unitario')}
                >
                  Precio Unitario {getSortIcon('precio_unitario')}
                </th>
                <th
                  className="sortable numeric"
                  onClick={() => handleSort('total')}
                >
                  Total {getSortIcon('total')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedProductos.length > 0 ? (
                sortedProductos.map((producto, index) => (
                  <tr key={index}>
                    <td className="numeric">{producto.cantidad || '-'}</td>
                    <td>{producto.nombre || '-'}</td>
                    <td className="numeric price">
                      {formatPrice(producto.precio_unitario)}
                    </td>
                    <td className="numeric price total">
                      {formatPrice(producto.total)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="no-results">
                    No se encontraron productos
                  </td>
                </tr>
              )}
            </tbody>
            <tfoot>
              {subtotal && (
                <tr className="summary-row">
                  <td colSpan={3} className="summary-label text-right">
                    <strong>Subtotal:</strong>
                  </td>
                  <td className="summary-value numeric price">
                    <strong>{formatPrice(subtotal)}</strong>
                  </td>
                </tr>
              )}
              {iva && (
                <tr className="summary-row">
                  <td colSpan={3} className="summary-label text-right">
                    <strong>IVA:</strong>
                  </td>
                  <td className="summary-value numeric price">
                    <strong>{formatPrice(iva)}</strong>
                  </td>
                </tr>
              )}
              {total && (
                <tr className="summary-row total-final">
                  <td colSpan={3} className="summary-label text-right">
                    <strong>TOTAL:</strong>
                  </td>
                  <td className="summary-value numeric price">
                    <strong>{formatPrice(total)}</strong>
                  </td>
                </tr>
              )}
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DocumentResults;

