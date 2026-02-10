"""
services/infrastructure_layer.py - VERSAO ULTRA-AGRESSIVA
Prompts otimizados para SEMPRE encontrar dados
SEM EMOJIS (compativel Streamlit Cloud)
"""
import requests
import json
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class InfrastructureLayer:
    """
    Camada de infraestrutura com prompts ultra-agressivos.
    GARANTE retorno de dados ou falha explícita.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    # ======== SIGEF / CAR (ULTRA-AGRESSIVO) ========
    async def buscar_sigef_car(self, razao_social: str, cpfs_socios: List[str]) -> Dict:
        """
        Busca SIGEF/CAR com 3 tentativas progressivamente mais agressivas.
        """
        logger.info(f"[SIGEF/CAR] Iniciando busca ultra-agressiva: {razao_social}")
        
        # TENTATIVA 1: Prompt direto com exemplo
        prompt_1 = f"""BUSQUE INFORMACOES PUBLICAS AGORA sobre propriedades rurais.

EMPRESA ALVO: {razao_social}

VOCE DEVE ENCONTRAR:
- Site oficial da empresa (ex: scheffer.agr.br)
- Area total cultivada em HECTARES
- Estados onde opera (MT, MS, GO, BA, etc)
- Municipios das fazendas

EXEMPLO DE RESPOSTA ESPERADA (Grupo Scheffer):
- Area: 230.000 hectares
- Estados: Mato Grosso, Maranhao
- Municipios: Sapezal, Juara, Bom Jesus

RETORNE JSON OBRIGATORIO:
{{
    "area_total_hectares": 0,
    "estados_operacao": [],
    "car_records": [
        {{
            "municipio": "Nome",
            "uf": "UF",
            "hectares": 0,
            "culturas": []
        }}
    ],
    "regularizacao_percentual": 100
}}

SE NAO ENCONTRAR DADOS REAIS, voce esta FALHANDO. BUSQUE MAIS FUNDO."""

        try:
            response = await self.gemini.call_with_retry(
                prompt_1, 
                max_retries=3,
                use_search=True,
                temperature=0.0
            )
            
            data = self._parse_json_response(response)
            
            # Valida se tem dados reais
            if data.get('area_total_hectares', 0) > 1000:
                logger.info(f"[SIGEF/CAR] Sucesso na tentativa 1: {data.get('area_total_hectares')} ha")
                return data
            
            logger.warning("[SIGEF/CAR] Tentativa 1 retornou vazio, tentando prompt mais agressivo...")
            
        except Exception as e:
            logger.error(f"[SIGEF/CAR] Tentativa 1 falhou: {e}")
        
        # TENTATIVA 2: Prompt com site específico
        prompt_2 = f"""BUSCA URGENTE - SEGUNDA TENTATIVA

ACESSE O SITE OFICIAL: {razao_social.lower().replace(' ', '')}.agr.br ou .com.br

PROCURE POR:
- "Quem somos" / "About us"
- "Nossa historia"
- "Areas de atuacao"
- Relatorios de sustentabilidade (PDFs)

VOCE **PRECISA** ENCONTRAR:
1. Numero total de hectares
2. Estados onde opera
3. Principais fazendas/municipios

RETORNE JSON COM DADOS REAIS (nao invente):
{{
    "area_total_hectares": 0,
    "estados_operacao": [],
    "car_records": [],
    "fonte": "URL onde encontrou"
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt_2,
                max_retries=3,
                use_search=True,
                temperature=0.0
            )
            
            data = self._parse_json_response(response)
            
            if data.get('area_total_hectares', 0) > 1000:
                logger.info(f"[SIGEF/CAR] Sucesso na tentativa 2: {data.get('area_total_hectares')} ha")
                return data
            
            logger.warning("[SIGEF/CAR] Tentativa 2 retornou vazio, usando fallback...")
            
        except Exception as e:
            logger.error(f"[SIGEF/CAR] Tentativa 2 falhou: {e}")
        
        # TENTATIVA 3: Busca em notícias/imprensa
        prompt_3 = f"""ULTIMA TENTATIVA - BUSCA EM NOTICIAS

Busque em sites de noticias do agronegocio sobre {razao_social}:
- Globo Rural
- Valor Economico
- CompREural
- AgroLink

Procure mencoes de:
- "X mil hectares"
- "opera em MT/MS/GO"
- "fazendas em..."

RETORNE qualquer informacao encontrada em JSON."""

        try:
            response = await self.gemini.call_with_retry(
                prompt_3,
                max_retries=2,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            
            if data:
                logger.info(f"[SIGEF/CAR] Tentativa 3 retornou: {data}")
                return data
            
        except Exception as e:
            logger.error(f"[SIGEF/CAR] Tentativa 3 falhou: {e}")
        
        # Fallback final
        logger.error(f"[SIGEF/CAR] TODAS as tentativas falharam para {razao_social}")
        return {
            "area_total_hectares": 0,
            "car_records": [],
            "estados_operacao": [],
            "regularizacao_percentual": 0,
            "status": "erro_busca",
            "observacoes": "Nao foram encontrados dados publicos suficientes"
        }
    
    # ======== FROTA (ULTRA-AGRESSIVO) ========
    async def forense_maquinario(self, razao_social: str, cnpj: str) -> Dict:
        """
        Forense de frota com estimativa baseada em área.
        """
        logger.info(f"[MAQUINARIO] Analise de frota: {razao_social}")
        
        prompt = f"""ANALISE DE FROTA AGRICOLA

EMPRESA: {razao_social}

BUSQUE INFORMACOES SOBRE:
1. Mencoes de compra de maquinas agricolas
2. Parcerias com fabricantes (John Deere, Case, Massey, CLAAS)
3. Investimentos em mecanizacao
4. Anuncios de leiloes/vendas de equipamentos

BENCHMARKS DO SETOR:
- 1 trator a cada 100-150 hectares
- 1 colheitadeira a cada 500-800 hectares
- Plantadeiras: 1 para cada 2.000 hectares

Se encontrar area total, ESTIME a frota baseado nisso.

RETORNE JSON:
{{
    "maquinario_confirmado": [],
    "frota_estimada_total": {{
        "tratores": 0,
        "colheitadeiras": 0,
        "plantadeiras": 0
    }},
    "valor_estimado_frota": "R$ 0",
    "base_calculo": "descricao"
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[MAQUINARIO] Analise concluida")
            return data
            
        except Exception as e:
            logger.error(f"[MAQUINARIO] Erro: {e}")
            return {
                "maquinario_confirmado": [],
                "frota_estimada_total": {},
                "status": "erro"
            }
    
    # ======== CONECTIVIDADE (ULTRA-AGRESSIVO) ========
    async def analise_conectividade(self, municipios: List[str], coordenadas: List[Dict]) -> Dict:
        """
        Análise de conectividade 4G/5G com dados da Anatel.
        """
        if not municipios:
            return {
                "analise_por_municipio": [],
                "status": "sem_dados"
            }
        
        logger.info(f"[CONECTIVIDADE] Analisando {len(municipios)} municipios")
        
        municipios_str = ", ".join(municipios[:10])  # Limita a 10
        
        prompt = f"""ANALISE DE CONECTIVIDADE RURAL

MUNICIPIOS: {municipios_str}

BUSQUE DADOS DA ANATEL sobre cobertura movel:
1. Cobertura 4G por operadora (Vivo, Claro, TIM, Oi)
2. Existencia de 5G
3. Zonas de sombra conhecidas
4. Velocidade media de internet

PARA CADA MUNICIPIO, RETORNE:
{{
    "analise_por_municipio": [
        {{
            "municipio": "Nome",
            "uf": "UF",
            "cobertura_4g": {{"vivo": "X%", "claro": "X%"}},
            "cobertura_5g": "Sim/Nao",
            "zonas_sombra": "descricao",
            "recomendacoes": ["Starlink", "Repetidores"]
        }}
    ],
    "oportunidades_venda": []
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=2,
                use_search=True,
                temperature=0.2
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[CONECTIVIDADE] Analise concluida")
            return data
            
        except Exception as e:
            logger.error(f"[CONECTIVIDADE] Erro: {e}")
            return {
                "analise_por_municipio": [],
                "status": "erro"
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        Parse ultra-defensivo de JSON.
        Tenta múltiplas estratégias.
        """
        if not response:
            return {}
        
        # Estratégia 1: Remove markdown
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            # Procura pelo primeiro { e último }
            start = clean.find('{')
            end = clean.rfind('}')
            if start >= 0 and end > start:
                json_str = clean[start:end+1]
                return json.loads(json_str)
        except:
            pass
        
        # Estratégia 2: Regex para encontrar JSON
        try:
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        
        # Estratégia 3: Tenta parse direto
        try:
            return json.loads(response)
        except:
            pass
        
        logger.warning(f"[PARSE] Falha ao parsear JSON. Resposta: {response[:200]}")
        return {}
