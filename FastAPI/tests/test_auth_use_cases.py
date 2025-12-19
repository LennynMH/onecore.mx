"""
Pruebas unitarias para AuthUseCases.

Este módulo contiene al menos 10 casos de prueba para cada método de AuthUseCases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import timedelta
from typing import Dict, Any

from app.application.use_cases.auth_use_cases import AuthUseCases
from app.core.security import decode_token


class TestLoginAnonymousUser:
    """Pruebas para el método login_anonymous_user."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_with_rol_provided(self, mock_auth_repository):
        """Test 1: Login con rol proporcionado."""
        # Configurar mock para retornar el rol correcto
        mock_auth_repository.create_or_get_anonymous_session = AsyncMock(
            return_value={"id": 1, "rol": "admin", "session_id": "test-session-id"}
        )
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user(rol="admin")
        
        assert result["token_type"] == "bearer"
        assert "access_token" in result
        assert result["user"]["rol"] == "admin"
        assert result["user"]["id_usuario"] == 1
        mock_auth_repository.create_or_get_anonymous_session.assert_called_once_with(rol="admin")
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_without_rol_defaults_to_gestor(self, mock_auth_repository):
        """Test 2: Login sin rol, debe usar 'gestor' por defecto."""
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user()
        
        assert result["user"]["rol"] == "gestor"
        mock_auth_repository.create_or_get_anonymous_session.assert_called_once_with(rol="gestor")
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_with_none_rol_defaults_to_gestor(self, mock_auth_repository):
        """Test 3: Login con rol=None, debe usar 'gestor' por defecto."""
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user(rol=None)
        
        assert result["user"]["rol"] == "gestor"
        mock_auth_repository.create_or_get_anonymous_session.assert_called_once_with(rol="gestor")
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_without_repository_uses_fallback(self):
        """Test 4: Login sin repositorio, debe usar valores fallback."""
        use_case = AuthUseCases(auth_repository=None)
        result = await use_case.login_anonymous_user(rol="admin")
        
        assert result["user"]["id_usuario"] == 999
        assert result["user"]["rol"] == "admin"
        assert "access_token" in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_returns_valid_token_structure(self, mock_auth_repository):
        """Test 5: Login debe retornar estructura de token válida."""
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user()
        
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert isinstance(result["access_token"], str)
        assert isinstance(result["expires_in"], int)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_token_is_decodable(self, mock_auth_repository):
        """Test 6: Token generado debe ser decodificable."""
        # Configurar mock para retornar el rol correcto
        mock_auth_repository.create_or_get_anonymous_session = AsyncMock(
            return_value={"id": 1, "rol": "admin", "session_id": "test-session-id"}
        )
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user(rol="admin")
        
        token = result["access_token"]
        payload = decode_token(token)
        
        assert payload["id_usuario"] == 1
        assert payload["rol"] == "admin"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_expires_in_is_correct(self, mock_auth_repository):
        """Test 7: expires_in debe ser correcto (minutos * 60)."""
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user()
        
        # expires_in debe ser minutos * 60 (15 * 60 = 900)
        assert result["expires_in"] == 900
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_with_different_roles(self, mock_auth_repository):
        """Test 8: Login con diferentes roles debe funcionar."""
        roles = ["admin", "gestor", "usuario"]
        
        for rol in roles:
            mock_auth_repository.create_or_get_anonymous_session = AsyncMock(
                return_value={"id": 1, "rol": rol, "session_id": f"session-{rol}"}
            )
            use_case = AuthUseCases(auth_repository=mock_auth_repository)
            result = await use_case.login_anonymous_user(rol=rol)
            
            assert result["user"]["rol"] == rol
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_repository_error_handling(self, mock_auth_repository):
        """Test 9: Manejo de errores del repositorio."""
        mock_auth_repository.create_or_get_anonymous_session = AsyncMock(
            side_effect=Exception("Database error")
        )
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        
        with pytest.raises(Exception):
            await use_case.login_anonymous_user()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_login_user_data_structure(self, mock_auth_repository):
        """Test 10: Estructura de datos de usuario debe ser correcta."""
        use_case = AuthUseCases(auth_repository=mock_auth_repository)
        result = await use_case.login_anonymous_user(rol="admin")
        
        user_data = result["user"]
        assert "id_usuario" in user_data
        assert "rol" in user_data
        assert isinstance(user_data["id_usuario"], int)
        assert isinstance(user_data["rol"], str)


class TestRenewToken:
    """Pruebas para el método renew_token."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_with_valid_token(self, sample_jwt_token):
        """Test 1: Renovar token válido debe generar nuevo token."""
        result = await AuthUseCases.renew_token(sample_jwt_token)
        
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["access_token"] != sample_jwt_token  # Debe ser diferente
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_preserves_user_data(self, sample_jwt_token):
        """Test 2: Renovar token debe preservar datos del usuario."""
        original_payload = decode_token(sample_jwt_token)
        result = await AuthUseCases.renew_token(sample_jwt_token)
        
        new_token = result["access_token"]
        new_payload = decode_token(new_token)
        
        assert new_payload["id_usuario"] == original_payload["id_usuario"]
        assert new_payload["rol"] == original_payload["rol"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_returns_correct_structure(self, sample_jwt_token):
        """Test 3: Estructura de respuesta debe ser correcta."""
        result = await AuthUseCases.renew_token(sample_jwt_token)
        
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert result["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_expires_in_is_correct(self, sample_jwt_token):
        """Test 4: expires_in debe ser correcto (refresh_expiration_minutes * 60)."""
        result = await AuthUseCases.renew_token(sample_jwt_token)
        
        # refresh_expiration_minutes = 30, entonces 30 * 60 = 1800
        assert result["expires_in"] == 1800
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_with_invalid_token(self):
        """Test 5: Renovar token inválido debe lanzar excepción."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):
            await AuthUseCases.renew_token(invalid_token)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_with_expired_token(self):
        """Test 6: Renovar token expirado debe lanzar excepción."""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Crear token expirado (tiempo negativo)
        expired_data = {"id_usuario": 1, "rol": "gestor"}
        expired_token = create_access_token(expired_data, timedelta(seconds=-1))
        
        # Esperar un momento para asegurar que expiró
        import asyncio
        await asyncio.sleep(0.1)
        
        with pytest.raises(Exception):
            await AuthUseCases.renew_token(expired_token)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_with_empty_string(self):
        """Test 7: Renovar token vacío debe lanzar excepción."""
        with pytest.raises(Exception):
            await AuthUseCases.renew_token("")
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_user_data_structure(self, sample_jwt_token):
        """Test 8: Estructura de datos de usuario debe ser correcta."""
        result = await AuthUseCases.renew_token(sample_jwt_token)
        
        user_data = result["user"]
        assert "id_usuario" in user_data
        assert "rol" in user_data
        assert isinstance(user_data["id_usuario"], int)
        assert isinstance(user_data["rol"], str)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_multiple_times(self, sample_jwt_token):
        """Test 9: Renovar token múltiples veces debe funcionar."""
        import asyncio
        result1 = await AuthUseCases.renew_token(sample_jwt_token)
        token1 = result1["access_token"]
        
        # Decodificar token1 para verificar su contenido
        payload1 = decode_token(token1)
        iat1 = payload1.get("iat")
        
        # Esperar un momento para que el tiempo de creación sea diferente
        await asyncio.sleep(1)  # Esperar 1 segundo para asegurar diferencia
        
        result2 = await AuthUseCases.renew_token(token1)
        token2 = result2["access_token"]
        
        # Decodificar token2 para verificar su contenido
        payload2 = decode_token(token2)
        iat2 = payload2.get("iat")
        
        # Los tokens deben ser diferentes porque tienen diferentes timestamps (iat)
        # Verificar que los iat (issued at) sean diferentes
        assert iat1 != iat2, f"Los iat deben ser diferentes: {iat1} vs {iat2}"
        assert token1 != token2, "Los tokens deben ser diferentes"
        assert result1["user"]["id_usuario"] == result2["user"]["id_usuario"]
        assert result1["user"]["rol"] == result2["user"]["rol"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_renew_token_with_different_user_roles(self):
        """Test 10: Renovar token con diferentes roles debe preservar el rol."""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        roles = ["admin", "gestor", "usuario"]
        
        for rol in roles:
            user_data = {"id_usuario": 1, "rol": rol}
            token = create_access_token(user_data, timedelta(minutes=15))
            result = await AuthUseCases.renew_token(token)
            
            assert result["user"]["rol"] == rol
            assert result["user"]["id_usuario"] == 1

