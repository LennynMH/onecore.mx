/**
 * Utilidades para manejo de JWT tokens
 */

/**
 * Decodifica un JWT token sin verificar la firma
 * (Solo para obtener información del payload)
 */
export function decodeJWT(token: string): any | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
}

/**
 * Verifica si un token JWT está expirado
 */
export function isTokenExpired(token: string): boolean {
  try {
    const decoded = decodeJWT(token);
    if (!decoded || !decoded.exp) {
      return true; // Si no tiene exp, considerarlo expirado
    }

    // exp está en segundos, Date.now() está en milisegundos
    const expirationTime = decoded.exp * 1000;
    const currentTime = Date.now();

    // Considerar expirado si falta menos de 1 minuto (margen de seguridad)
    const margin = 60 * 1000; // 1 minuto en milisegundos
    return currentTime >= (expirationTime - margin);
  } catch (error) {
    console.error('Error checking token expiration:', error);
    return true; // En caso de error, considerar expirado
  }
}

/**
 * Obtiene el tiempo restante hasta la expiración del token (en segundos)
 */
export function getTokenTimeRemaining(token: string): number {
  try {
    const decoded = decodeJWT(token);
    if (!decoded || !decoded.exp) {
      return 0;
    }

    const expirationTime = decoded.exp * 1000;
    const currentTime = Date.now();
    const remaining = Math.floor((expirationTime - currentTime) / 1000);

    return remaining > 0 ? remaining : 0;
  } catch (error) {
    console.error('Error getting token time remaining:', error);
    return 0;
  }
}

