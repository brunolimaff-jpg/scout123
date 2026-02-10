"""
services/gemini_service.py — COMPATÍVEL COM google-genai (SDK NOVO v1.0+)
Configuração agressiva com Google Search habilitado e Fallback Inteligente
"""
import google.genai as genai
from google.genai import types
import logging
import time
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Wrapper do Gemini AI com:
    - Modelo Principal: Gemini 2.5 Pro (Raciocínio Avançado)
    - Modelo Fallback: Gemini 2.5 Flash (Velocidade/Estabilidade)
    - Google Search habilitado por padrão
    - Retry automático com troca de modelo
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o Gemini com configuração de alta precisão.
        """
        if not api_key:
            logger.error("API Key não fornecida para GeminiService")
            raise ValueError("API Key do Google AI é obrigatória")
        
        # Configura cliente do novo SDK
        self.client = genai.Client(api_key=api_key)
        
        # 1. MELHOR MODELO (Precisão/Raciocínio)
        self.primary_model = "gemini-2.5-pro"
        
        # 2. MODELO DE SEGURANÇA (Fallback)
        self.fallback_model = "gemini-2.5-flash"
        
        # Rate limiting otimizado (60 req/min para Paid Tier)
        self.requests_per_minute = 60
        self.request_interval = 60.0 / self.requests_per_minute
        self.last_request_time = 0
        
        logger.info(f"[GeminiService] Inicializado. Principal: {self.primary_model} | Fallback: {self.fallback_model}")

    async def generate_content(self, prompt: str) -> str:
        """
        Método de compatibilidade para o dossier_orchestrator.py.
        Redireciona para a função robusta call_with_retry.
        """
        return await self.call_with_retry(prompt)

    async def call_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3,
        use_search: bool = True,
        temperature: float = 0.2
    ) -> str:
        """
        Chama Gemini com retry automático e FALLBACK de modelo.
        """
        # Lista de modelos para tentar em ordem: Principal -> Fallback
        models_to_try = [self.primary_model, self.fallback_model]
        
        last_error = None

        for attempt in range(1, max_retries + 1):
            await self._rate_limit()
            
            # Tenta cada modelo disponível na sequência
            for model_name in models_to_try:
                try:
                    logger.info(f"[GeminiService] Tentativa {attempt} usando modelo: {model_name}")
                    
                    # Configuração da chamada
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=8192,
                        # Habilita o SEARCH tool corretamente no novo SDK
                        tools=[types.Tool(google_search=types.GoogleSearch())] if use_search else None
                    )
                    
                    # Chamada ASYNC correta (client.aio)
                    response = await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    
                    # Extração segura do texto
                    if response and response.text:
                        return response.text
                    
                    # Se chegou aqui, resposta veio vazia mas sem erro
                    logger.warning(f"[GeminiService] Resposta vazia do modelo {model_name}")

                except Exception as e:
                    logger.warning(f"[GeminiService] Erro com {model_name}: {e}")
                    last_error = e
                    # Se for erro 404 (Modelo não encontrado) ou 429 (Quota), o loop continua para o próximo modelo (Fallback)
                    # Se o modelo principal falhar, o loop interno pega o fallback_model imediatamente
                    if model_name == self.primary_model:
                        logger.info(f"[GeminiService] Alternando para fallback: {self.fallback_model}")
                        continue
            
            # Se ambos os modelos falharam nesta tentativa, espera antes do retry global
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"[GeminiService] Todos modelos falharam na tentativa {attempt}. Aguardando {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[GeminiService] Falha fatal após {max_retries} tentativas completas.")
                
        # Se esgotou tudo
        if last_error:
            raise last_error
        return ""

    async def _rate_limit(self):
        """
        Rate limiting assíncrono para não bloquear o Streamlit.
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            await asyncio.sleep(sleep_time) # Async sleep é crucial
        
        self.last_request_time = time.time()
