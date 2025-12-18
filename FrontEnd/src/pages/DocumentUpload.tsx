import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';
import { apiService, DocumentUploadResponse } from '../services/api';
import './DocumentUpload.css';

const DocumentUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const acceptedFile = acceptedFiles[0];
    if (acceptedFile) {
      // Validar tipo de archivo
      const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
      const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png'];
      const fileExtension = acceptedFile.name.toLowerCase().substring(acceptedFile.name.lastIndexOf('.'));

      if (!validTypes.includes(acceptedFile.type) && !validExtensions.includes(fileExtension)) {
        toast.error('Solo se permiten archivos PDF, JPG o PNG');
        return;
      }

      // Validar tamaño (10 MB máximo)
      const maxSize = 10 * 1024 * 1024; // 10 MB
      if (acceptedFile.size > maxSize) {
        toast.error('El archivo no debe exceder 10 MB');
        return;
      }

      setFile(acceptedFile);
      toast.success('Archivo seleccionado correctamente');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10 MB
  });

  const handleUpload = async () => {
    if (!file) {
      toast.error('Por favor selecciona un archivo');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simular progreso (en producción, esto vendría del servidor)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response: DocumentUploadResponse = await apiService.uploadDocument(
        file,
        (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(percentCompleted);
          }
        }
      );

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Guardar resultado para la página de resultados
      localStorage.setItem('last_analysis_result', JSON.stringify(response));

      toast.success('Documento procesado exitosamente');
      
      // Navegar a la página de resultados después de un breve delay
      setTimeout(() => {
        navigate('/results');
      }, 1000);
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || 'Error al procesar el documento'
      );
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setFile(null);
    setUploadProgress(0);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="document-upload">
      <div className="upload-container">
        <h2>Cargar Documento</h2>
        <p className="subtitle">
          Sube un documento en formato PDF, JPG o PNG para análisis con IA
        </p>

        {!file ? (
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'active' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="dropzone-content">
              <div className="dropzone-icon">📄</div>
              {isDragActive ? (
                <p>Suelta el archivo aquí...</p>
              ) : (
                <>
                  <p>Arrastra un archivo aquí o haz clic para seleccionar</p>
                  <p className="dropzone-hint">
                    Formatos: PDF, JPG, PNG (máx. 10MB)
                  </p>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="file-preview">
            <div className="file-info">
              <div className="file-icon">
                {file.type === 'application/pdf' ? '📄' : '🖼️'}
              </div>
              <div className="file-details">
                <h3>{file.name}</h3>
                <p>{formatFileSize(file.size)}</p>
              </div>
            </div>

            {uploadProgress > 0 && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="progress-text">
                  {uploadProgress < 100
                    ? `Procesando... ${uploadProgress}%`
                    : 'Completado'}
                </p>
              </div>
            )}

            <div className="file-actions">
              <button
                onClick={handleUpload}
                className="btn btn-primary"
                disabled={uploading}
              >
                {uploading ? 'Procesando...' : 'Subir y Analizar'}
              </button>
              <button
                onClick={handleCancel}
                className="btn btn-secondary"
                disabled={uploading}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        <div className="upload-info">
          <h3>¿Qué hace el análisis?</h3>
          <ul>
            <li>
              <strong>Clasificación automática:</strong> Identifica si el
              documento es una Factura o Información general
            </li>
            <li>
              <strong>Extracción de datos:</strong> Extrae automáticamente los
              datos relevantes según el tipo de documento
            </li>
            <li>
              <strong>Análisis con IA:</strong> Utiliza servicios de IA para
              procesar y analizar el contenido
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;

