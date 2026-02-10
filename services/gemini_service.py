"""
services/gemini_service.py — VERSÃO OTIMIZADA PARA STREAMLIT CLOUD
Configuração agressiva com Google Search habilitado
"""
import google.generativeai as genai
import logging
import time
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Serviço Gemini com configuração ultra-agressiva.
    - Google Search SEMPRE habilitado
    - Rate limit 60 req/min
    - Retry automático 3x
    - Temperature baixa para precisão
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa Gemini com Search habilitado.
        
        Args:
            api_key: Chave da API (vem de st.secrets ou input)
        """
        if not api_key:
            raise ValueError("❌ API Key do Gemini não fornecida!")
        
        genai.configure(api_key=api_key)
        
        # Configuração ULTRA-AGRESSIVA
        self.generation_config = {
            "temperature": 0.0,  # Zero = máxima precisão
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,  # Respostas longas permitidas
        }
        
        # Safety settings MÍNIMOS (dados públicos apenas)
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Google Search TOOLS (sempre habilitado)
        self.tools_search = [{"google_search_retrieval": {}}]
        
        # Rate limiting (60 req/min = 1 por segundo)
        self.min_interval = 1.0  # segundos entre chamadas
        self.last_call_time = 0
        
        logger.info("✅ GeminiService inicializado com Google Search")
    
    async def call_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3,
        use_search: bool = True,
        temperature: Optional[float] = None
    ) -> str:
        """
        Chama Gemini com retry automático e rate limiting.
        
        Args:
            prompt: Texto do prompt
            max_retries: Tentativas máximas
            use_search: Se True, habilita Google Search
            temperature: Override de temperatura (0.0-1.0)
        
        Returns:
            Resposta do Gemini
        """
        # Override de temperatura se fornecido
        config = self.generation_config.copy()
        if temperature is not None:
            config["temperature"] = temperature
        
        # Escolhe ferramentas
        tools = self.tools_search if use_search else None
        
        for attempt in range(max_retries):
            try:
                # Rate limiting
                await self._respect_rate_limit()
                
                # Cria modelo
                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash-exp",  # Modelo mais recente
                    generation_config=config,
                    safety_settings=self.safety_settings,
                    tools=tools
                )
                
                # Faz a chamada
                logger.debug(f"[GEMINI] Tentativa {attempt+1}/{max_retries} | Search: {use_search}")
                
                response = model.generate_content(prompt)
                
                # Extrai texto
                if hasattr(response, 'text') and response.text:
                    logger.info(f"[GEMINI] ✅ Resposta recebida ({len(response.text)} chars)")
                    return response.text
                
                # Se bloqueado por safety
                if hasattr(response, 'prompt_feedback'):
                    logger.warning(f"[GEMINI] ⚠️ Bloqueado por safety: {response.prompt_feedback}")
                    if attempt == max_retries - 1:
                        return "ERRO: Conteúdo bloqueado por filtros de segurança"
                
                # Nenhum texto retornado
                logger.warning(f"[GEMINI] ⚠️ Resposta vazia na tentativa {attempt+1}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                    
            except Exception as e:
                logger.error(f"[GEMINI] ❌ Tentativa {attempt+1} falhou: {e}")
                
                if attempt == max_retries - 1:
                    raise
                
                # Backoff exponencial: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)
        
        # Todas tentativas falharam
        logger.error(f"[GEMINI] ❌ Todas as {max_retries} tentativas falharam")
        return "ERRO: Não foi possível obter resposta do Gemini após múltiplas tentativas"
    
    async def _respect_rate_limit(self):
        """
        Garante 60 req/min (1 req/segundo).
        """
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"[RATE LIMIT] Aguardando {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_call_time = time.time()
    
    def call_sync(self, prompt: str, use_search: bool = True) -> str:
        """
        Versão síncrona para compatibilidade.
        """
        return asyncio.run(self.call_with_retry(prompt, use_search=use_search))
