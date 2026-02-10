"""
services/gemini_service.py — COMPATÍVEL COM google-genai (SDK NOVO)
Configuração agressiva com Google Search habilitado
"""
import google.genai as genai  # ← SDK NOVO (google-genai)
import logging
import time
from typing import Optional
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Wrapper do Gemini AI com:
    - Google Search habilitado por padrão
    - Rate limiting otimizado (60 req/min)
    - Retry automático com backoff
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o Gemini com configuração agressiva.
        
        Args:
            api_key: Google AI API Key
        """
        if not api_key:
            raise ValueError("API Key do Google AI é obrigatória")
        
        # Configura cliente
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash-exp"
        
        # Rate limiting otimizado
        self.requests_per_minute = 60
        self.request_interval = 60.0 / self.requests_per_minute  # ~1 req/seg
        self.last_request_time = 0
        
        logger.info("[GeminiService] Inicializado com sucesso")
    
    async def call_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3,
        use_search: bool = True,
        temperature: float = 0.0
    ) -> str:
        """
        Chama Gemini com retry automático.
        
        Args:
            prompt: Prompt para o modelo
            max_retries: Número máximo de tentativas
            use_search: Habilitar Google Search
            temperature: Criatividade (0.0 = determinístico)
            
        Returns:
            Resposta do modelo em texto
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limit()
                
                # Configuração do modelo
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                )
                
                # Habilita Google Search se solicitado
                if use_search:
                    config.tools = [types.Tool(google_search=types.GoogleSearch())]
                
                # Chama API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                # Extrai texto da resposta
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        return "".join([part.text for part in parts if hasattr(part, 'text')])
                
                logger.warning(f"[GeminiService] Resposta sem texto na tentativa {attempt}")
                return ""
                
            except Exception as e:
                logger.warning(f"[GeminiService] Tentativa {attempt}/{max_retries} falhou: {e}")
                
                if attempt < max_retries:
                    # Backoff exponencial
                    wait_time = 2 ** attempt
                    logger.info(f"[GeminiService] Aguardando {wait_time}s antes de retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[GeminiService] Todas as tentativas falharam: {e}")
                    raise
        
        return ""
    
    async def _rate_limit(self):
        """
        Implementa rate limiting simples.
        Garante intervalo mínimo entre requisições.
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
