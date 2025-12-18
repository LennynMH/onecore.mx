import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DocumentUploadResponse, InvoiceData, InformationData } from '../services/api';
import './DocumentResults.css';

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
          {data.total_factura && (
            <div className="data-item">
              <span className="data-label">Total:</span>
              <span className="data-value total-amount">{data.total_factura}</span>
            </div>
          )}
        </div>
      </div>

      {data.productos && data.productos.length > 0 && (
        <div className="invoice-section">
          <h4>Productos</h4>
          <div className="products-table">
            <table>
              <thead>
                <tr>
                  <th>Cantidad</th>
                  <th>Nombre</th>
                  <th>Precio Unitario</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {data.productos.map((producto, index) => (
                  <tr key={index}>
                    <td>{producto.cantidad || '-'}</td>
                    <td>{producto.nombre || '-'}</td>
                    <td>{producto.precio_unitario || '-'}</td>
                    <td>{producto.total || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
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

export default DocumentResults;

