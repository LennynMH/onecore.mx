"""
OpenAI service for sentiment analysis and text summarization.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona servicios para integración con OpenAI, incluyendo análisis de sentimiento
y generación de resúmenes. Esta refactorización elimina código duplicado de creación
de clientes y llamadas a la API.

¿Qué clases contiene?
- OpenAIService: Servicio principal para integración con OpenAI
"""

import logging
from typing import Optional, Dict, Any, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Servicio para integración con OpenAI.
    
    ¿Qué hace la clase?
    Proporciona métodos para análisis de sentimiento y generación de resúmenes
    usando la API de OpenAI. Maneja la configuración del cliente y las llamadas
    a la API de forma consistente.
    
    ¿Qué métodos tiene?
    - analyze_sentiment: Analiza el sentimiento de un texto
    - generate_summary: Genera un resumen de un texto
    - _get_client: Obtiene el cliente OpenAI configurado
    - _call_chat_completion: Realiza llamadas a la API de chat
    """
    
    def __init__(self):
        """
        Inicializa el servicio de OpenAI.
        
        ¿Qué hace la función?
        Verifica si OpenAI está disponible y configurado, y establece el estado
        de configuración del servicio.
        
        ¿Qué parámetros recibe y de qué tipo?
        - Ninguno
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.is_configured = False
        
        if not OPENAI_AVAILABLE:
            logger.warning("openai library not available. OpenAI service will be disabled.")
            return
        
        # Verificar si la API key de OpenAI está configurada
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            self.is_configured = True
            logger.info("OpenAI service initialized successfully")
        else:
            logger.warning("OpenAI API key not configured. OpenAI service will be disabled.")
    
    def _get_client(self):
        """
        Obtiene el cliente OpenAI configurado.
        
        ¿Qué hace la función?
        Crea y retorna una instancia del cliente OpenAI usando la API key
        configurada en settings. Este método centraliza la creación del cliente
        para evitar duplicación.
        
        ¿Qué parámetros recibe y de qué tipo?
        - Ninguno
        
        ¿Qué dato regresa y de qué tipo?
        - OpenAI: Cliente de OpenAI configurado
        
        Raises:
            Exception: Si OpenAI no está disponible o la API key no está configurada
        """
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI library not available")
        
        if not self.is_configured or not hasattr(settings, 'openai_api_key') or not settings.openai_api_key:
            raise Exception("OpenAI API key not configured")
        
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)
    
    def _call_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 200,
        temperature: float = 0.5
    ) -> str:
        """
        Realiza una llamada a la API de chat completions de OpenAI.
        
        ¿Qué hace la función?
        Envía una solicitud a la API de OpenAI para completar un chat,
        manejando errores y retornando el contenido de la respuesta.
        
        ¿Qué parámetros recibe y de qué tipo?
        - messages (List[Dict[str, str]]): Lista de mensajes para el chat
        - model (str): Modelo a usar (default: "gpt-3.5-turbo")
        - max_tokens (int): Máximo de tokens en la respuesta (default: 200)
        - temperature (float): Temperatura para la generación (default: 0.5)
        
        ¿Qué dato regresa y de qué tipo?
        - str: Contenido de la respuesta del modelo
        
        Raises:
            Exception: Si ocurre un error en la llamada a la API
        """
        client = self._get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    
    async def analyze_sentiment(self, text: str) -> str:
        """
        Analiza el sentimiento de un texto usando OpenAI.
        
        ¿Qué hace la función?
        Envía el texto a OpenAI para analizar su sentimiento y retorna
        "positivo", "negativo" o "neutral" según el análisis.
        
        ¿Qué parámetros recibe y de qué tipo?
        - text (str): Texto a analizar
        
        ¿Qué dato regresa y de qué tipo?
        - str: Sentimiento detectado ("positivo", "negativo", o "neutral")
        """
        if not self.is_configured:
            logger.warning("OpenAI not configured. Returning neutral sentiment.")
            return "neutral"
        
        if not text or len(text.strip()) < 10:
            return "neutral"
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Eres un analizador de sentimientos. Analiza el texto y responde SOLO con una de estas palabras: positivo, negativo, neutral."
                },
                {
                    "role": "user",
                    "content": f"Analiza el sentimiento de este texto: {text[:1000]}"
                }
            ]
            
            sentiment = self._call_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                max_tokens=10,
                temperature=0.3
            ).lower()
            
            # Normalizar respuesta
            if "positivo" in sentiment or "positive" in sentiment:
                return "positivo"
            elif "negativo" in sentiment or "negative" in sentiment:
                return "negativo"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment with OpenAI: {str(e)}")
            return "neutral"
    
    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        Genera un resumen de un texto usando OpenAI.
        
        ¿Qué hace la función?
        Envía el texto a OpenAI para generar un resumen conciso del contenido,
        limitado a la longitud máxima especificada.
        
        ¿Qué parámetros recibe y de qué tipo?
        - text (str): Texto a resumir
        - max_length (int): Longitud máxima del resumen en caracteres (default: 500)
        
        ¿Qué dato regresa y de qué tipo?
        - str: Resumen generado, o texto truncado si OpenAI no está disponible
        """
        if not self.is_configured:
            logger.warning("OpenAI not configured. Returning truncated text as summary.")
            return text[:max_length] + "..." if len(text) > max_length else text
        
        if not text or len(text.strip()) < 50:
            return text[:max_length] if len(text) > max_length else text
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"Eres un asistente que genera resúmenes concisos. Genera un resumen de máximo {max_length} caracteres."
                },
                {
                    "role": "user",
                    "content": f"Genera un resumen de este texto: {text[:2000]}"
                }
            ]
            
            summary = self._call_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                max_tokens=200,
                temperature=0.5
            )
            
            return summary[:max_length]
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {str(e)}")
            # Fallback a truncación simple
            return text[:max_length] + "..." if len(text) > max_length else text

