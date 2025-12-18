import { Outlet, Link, useLocation } from 'react-router-dom';
import { apiService } from '../services/api';
import './Layout.css';

const Layout: React.FC = () => {
  const location = useLocation();

  const handleLogout = () => {
    apiService.logout();
    window.location.href = '/login';
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>OneCore - Análisis de Documentos</h1>
        </div>
        <div className="navbar-menu">
          <Link
            to="/upload"
            className={isActive('/upload') ? 'nav-link active' : 'nav-link'}
          >
            Cargar Documento
          </Link>
          <Link
            to="/history"
            className={isActive('/history') ? 'nav-link active' : 'nav-link'}
          >
            Historial
          </Link>
          <button onClick={handleLogout} className="logout-btn">
            Cerrar Sesión
          </button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

