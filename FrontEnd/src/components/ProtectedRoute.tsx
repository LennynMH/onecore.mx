import { Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { apiService } from '../services/api';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    // Verificar autenticación al montar el componente
    const checkAuth = () => {
      const authenticated = apiService.isAuthenticated();
      setIsAuthenticated(authenticated);
      
      // Si no está autenticado, limpiar datos
      if (!authenticated) {
        apiService.logout();
      }
    };

    checkAuth();

    // Verificar periódicamente (cada 30 segundos) si el token expiró
    const interval = setInterval(() => {
      if (!apiService.isAuthenticated()) {
        setIsAuthenticated(false);
        apiService.logout();
      }
    }, 30000); // 30 segundos

    return () => clearInterval(interval);
  }, []);

  // Mostrar loading mientras se verifica
  if (isAuthenticated === null) {
    return <div>Cargando...</div>;
  }

  // Redirigir al login si no está autenticado
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

