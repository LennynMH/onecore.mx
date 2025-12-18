import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { apiService } from '../services/api';
import './Login.css';

const Login: React.FC = () => {
  const [rol, setRol] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (selectedRol?: string) => {
    setLoading(true);
    try {
      const response = await apiService.login(selectedRol || undefined);
      localStorage.setItem('user_data', JSON.stringify(response.user));
      toast.success(`Bienvenido! Rol: ${response.user.rol}`);
      navigate('/upload');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(rol || undefined);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>OneCore</h1>
        <h2>Análisis de Documentos con IA</h2>
        <p className="subtitle">Inicia sesión para comenzar</p>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="rol">Rol (opcional)</label>
            <select
              id="rol"
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              className="form-control"
            >
              <option value="">Por defecto (gestor)</option>
              <option value="admin">Administrador</option>
              <option value="gestor">Gestor</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div className="quick-login">
          <p>O inicia sesión rápidamente:</p>
          <div className="quick-buttons">
            <button
              onClick={() => handleLogin('admin')}
              className="btn btn-secondary"
              disabled={loading}
            >
              Como Admin
            </button>
            <button
              onClick={() => handleLogin('gestor')}
              className="btn btn-secondary"
              disabled={loading}
            >
              Como Gestor
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

