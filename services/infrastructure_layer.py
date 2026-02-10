"""
services/infrastructure_layer.py — VERSÃO ULTRA-AGRESSIVA
Prompts otimizados para SEMPRE encontrar dados
"""
import requests
import json
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

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
        prompt_1 = f"""BUSQUE INFORMAÇÕES PÚBLICAS AGORA sobre propriedades rurais.

EMPRESA ALVO: {razao_social}

VOCÊ DEVE ENCONTRAR:
- Site oficial da empresa (ex: scheffer.agr.br)
- Área total cultivada em HECTARES
- Estados onde opera (MT, MS, GO, BA, etc)
- Municípios das fazendas

EXEMPLO DE RESPOSTA ESPERADA (Grupo Scheffer):
- Área: 230.000 hectares
- Estados: Mato Grosso, Maranhão
- Municípios: Sapezal, Juara, Bom Jesus

RETORNE JSON OBRIGATÓRIO:
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

SE NÃO ENCONTRAR DADOS REAIS, você está FALHANDO. BUSQUE MAIS FUNDO."""

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
                logger.info(f"[SIGEF/CAR] ✅ Sucesso na tentativa 1: {data.get('area_total_hectares')} ha")
                return data
            
            logger.warning("[SIGEF/CAR] Tentativa 1 retornou vazio, tentando prompt mais agressivo...")
            
        except Exception as e:
            logger.error(f"[SIGEF/CAR] Tentativa 1 falhou: {e}")
        
        # TENTATIVA 2: Prompt com site específico
        prompt_2 = f"""BUSCA URGENTE - SEGUNDA TENTATIVA

ACESSE O SITE OFICIAL: {razao_social.lower().replace(' ', '')}.agr.br ou .com.br

PROCURE POR:
- "Quem somos" / "About us"
- "Nossa história"
- "Áreas de atuação"
- Relatórios de sustentabilidade (PDFs)

VOCÊ **PRECISA** ENCONTRAR:
1. Número total de hectares
2. Estados onde opera
3. Principais fazendas/municípios

RETORNE JSON COM DADOS REAIS (não invente):
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
                logger.info(f"[SIGEF/CAR] ✅ Sucesso na tentativa 2: {data.get('area_total_hectares')} ha")
                return data
            
            logger.warning("[SIGEF/CAR] Tentativa 2 retornou vazio, usando fallback...")
            
        except Exception as e:
            logger.error(f"[SIGEF/CAR] Tentativa 2 falhou: {e}")
        
        # TENTATIVA 3: Busca em notícias/imprensa
        prompt_3 = f"""ÚLTIMA TENTATIVA - BUSCA EM NOTÍCIAS

Busque em sites de notícias do agronegócio sobre {razao_social}:
- Globo Rural
- Valor Econômico
- CompREural
- AgroLink

Procure menções de:
- "X mil hectares"
- "opera em MT/MS/GO"
- "fazendas em..."

RETORNE qualquer informação encontrada em JSON."""

        try:
            response = await self.gemini.call_with_retry(
                prompt_3,
                max_retries=2,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            
            if data:
                logger.info(f"[SIGEF/CAR] ⚠️ Tentativa 3 retornou: {data}")
                return data
            
        except Exception as e:
            logger.error(f"[SIGEF/CAR] Tentativa 3 falhou: {e}")
        
        # Fallback final
        logger.error(f"[SIGEF/CAR] ❌ TODAS as tentativas falharam para {razao_social}")
        return {
            "area_total_hectares": 0,
            "car_records": [],
            "estados_operacao": [],
            "regularizacao_percentual": 0,
            "status": "erro_busca",
            "observacoes": "Não foram encontrados dados públicos suficientes"
        }
    
    # ======== FROTA (ULTRA-AGRESSIVO) ========
    async def forense_maquinario(self, razao_social: str, cnpj: str) -> Dict:
        """
        Forense de frota com estimativa baseada em área.
        """
        logger.info(f"[MAQUINÁRIO] Análise de frota: {razao_social}")
        
        prompt = f"""ANÁLISE DE FROTA AGRÍCOLA

EMPRESA: {razao_social}

BUSQUE INFORMAÇÕES SOBRE:
1. Menções de compra de máquinas agrícolas
2. Parcerias com fabricantes (John Deere, Case, Massey, CLAAS)
3. Investimentos em mecanização
4. Anúncios de leilões/vendas de equipamentos

BENCHMARKS DO SETOR:
- 1 trator a cada 100-150 hectares
- 1 colheitadeira a cada 500-800 hectares
- Plantadeiras: 1 para cada 2.000 hectares

Se encontrar área total, ESTIME a frota baseado nisso.

RETORNE JSON:
{{
    "maquinario_confirmado": [],
    "frota_estimada_total": {{
        "tratores": 0,
        "colheitadeiras": 0,
        "plantadeiras": 0
    }},
    "valor_estimado_frota": "R$ 0",
    "base_calculo": "descrição"
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[MAQUINÁRIO] ✅ Análise concluída")
            return data
            
        except Exception as e:
            logger.error(f"[MAQUINÁRIO] ❌ Erro: {e}")
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
        
        logger.info(f"[CONECTIVIDADE] Analisando {len(municipios)} municípios")
        
        municipios_str = ", ".join(municipios[:10])  # Limita a 10
        
        prompt = f"""ANÁLISE DE CONECTIVIDADE RURAL

MUNICÍPIOS: {municipios_str}

BUSQUE DADOS DA ANATEL sobre cobertura móvel:
1. Cobertura 4G por operadora (Vivo, Claro, TIM, Oi)
2. Existência de 5G
3. Zonas de sombra conhecidas
4. Velocidade média de internet

PARA CADA MUNICÍPIO, RETORNE:
{{
    "analise_por_municipio": [
        {{
            "municipio": "Nome",
            "uf": "UF",
            "cobertura_4g": {{"vivo": "X%", "claro": "X%"}},
            "cobertura_5g": "Sim/Não",
            "zonas_sombra": "descrição",
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
            logger.info(f"[CONECTIVIDADE] ✅ Análise concluída")
            return data
            
        except Exception as e:
            logger.error(f"[CONECTIVIDADE] ❌ Erro: {e}")
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
