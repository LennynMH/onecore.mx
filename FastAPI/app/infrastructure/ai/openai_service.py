"""
OpenAI service for sentiment analysis and text summarization.
"""

import logging
from typing import Optional, Dict, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI integration."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        self.client = None
        self.is_configured = False
        
        if not OPENAI_AVAILABLE:
            logger.warning("openai library not available. OpenAI service will be disabled.")
            return
        
        # Check if OpenAI API key is configured
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            try:
                from openai import OpenAI
                # Test connection (will be created per request)
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.is_configured = True
                logger.info("OpenAI service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
                self.is_configured = False
        else:
            logger.warning("OpenAI API key not configured. OpenAI service will be disabled.")
    
    async def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text using OpenAI.
        
        Args:
            text: Text to analyze
            
        Returns:
            "positivo", "negativo", or "neutral"
        """
        if not self.is_configured or not self.client:
            logger.warning("OpenAI not configured. Returning neutral sentiment.")
            return "neutral"
        
        if not text or len(text.strip()) < 10:
            return "neutral"
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Use OpenAI API for sentiment analysis
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analizador de sentimientos. Analiza el texto y responde SOLO con una de estas palabras: positivo, negativo, neutral."
                    },
                    {
                        "role": "user",
                        "content": f"Analiza el sentimiento de este texto: {text[:1000]}"
                    }
                ],
                max_tokens=10,
                temperature=0.3
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            
            # Normalize response
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
        Generate a summary of text using OpenAI.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summary text
        """
        if not self.is_configured or not self.client:
            logger.warning("OpenAI not configured. Returning truncated text as summary.")
            return text[:max_length] + "..." if len(text) > max_length else text
        
        if not text or len(text.strip()) < 50:
            return text[:max_length] if len(text) > max_length else text
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"Eres un asistente que genera resúmenes concisos. Genera un resumen de máximo {max_length} caracteres."
                    },
                    {
                        "role": "user",
                        "content": f"Genera un resumen de este texto: {text[:2000]}"
                    }
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            return summary[:max_length]
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {str(e)}")
            # Fallback to simple truncation
            return text[:max_length] + "..." if len(text) > max_length else text

