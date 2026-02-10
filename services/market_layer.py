"""
services/market_layer.py — VERSÃO ULTRA-AGRESSIVA
Análise profunda de mercado, concorrentes e posicionamento
"""
import logging
from typing import Dict, List, Optional
import re
import json

logger = logging.getLogger(__name__)

class MarketLayer:
    """
    Camada de análise de mercado com prompts ultra-agressivos.
    Foca em: concorrentes, market share, posicionamento, tendências.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    async def analise_concorrentes(self, razao_social: str, estados: List[str], culturas: List[str]) -> Dict:
        """
        Identifica concorrentes diretos na mesma região/culturas.
        """
        logger.info(f"[CONCORRENTES] Analisando competição: {razao_social}")
        
        estados_str = ", ".join(estados) if estados else "Brasil"
        culturas_str = ", ".join(culturas) if culturas else "grãos"
        
        prompt = f"""ANÁLISE DE CONCORRÊNCIA NO AGRONEGÓCIO

EMPRESA ALVO: {razao_social}
CULTURAS: {culturas_str}
REGIÃO: {estados_str}

VOCÊ DEVE IDENTIFICAR:

1. **TOP 5 CONCORRENTES DIRETOS** na mesma região/culturas
   Para cada concorrente, busque:
   - Nome completo
   - Área total (hectares)
   - Principais fazendas/municípios
   - Diferencial competitivo

2. **MARKET SHARE ESTIMADO**
   - % da produção regional
   - Ranking estadual/nacional

3. **POSICIONAMENTO**
   - Foco (grãos, pecuária, integração)
   - Certificações (regenagri, Rainforest, etc)
   - Tecnologia (agricultura de precisão, drones)

EXEMPLO (Grupo Scheffer):
- Concorrentes: SLC Agrícola, Agrifirma, Vanguarda Agro
- Market share: Top 3 em algodão no MT (~8%)
- Diferencial: Primeira certificação regenagri no Brasil

RETORNE JSON COMPLETO:
{{
    "concorrentes_diretos": [
        {{
            "nome": "Nome da empresa",
            "area_hectares": 0,
            "culturas_principais": [],
            "diferenciais": "texto",
            "presenca_regional": []
        }}
    ],
    "market_share_estimado": {{
        "producao_regional_percent": 0,
        "ranking_nacional": "Top X",
        "base_calculo": "fonte"
    }},
    "posicionamento_competitivo": {{
        "fortalezas": [],
        "fraquezas": [],
        "diferenciais": [],
        "certificacoes": []
    }}
}}

BUSQUE EM:
- Sites oficiais dos concorrentes
- Ranking SAFRAS & Mercado
- Anuário da Agricultura Brasileira
- Notícias do setor (Globo Rural, Valor Econômico)

NÃO INVENTE DADOS. Se não encontrar concorrentes específicos, retorne lista vazia."""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json(response)
            
            # Valida se encontrou concorrentes
            concorrentes = data.get('concorrentes_diretos', [])
            if len(concorrentes) > 0:
                logger.info(f"[CONCORRENTES] ✅ Encontrados {len(concorrentes)} concorrentes")
            else:
                logger.warning(f"[CONCORRENTES] ⚠️ Nenhum concorrente identificado")
            
            return data
            
        except Exception as e:
            logger.error(f"[CONCORRENTES] ❌ Erro: {e}")
            return {
                "concorrentes_diretos": [],
                "market_share_estimado": {},
                "posicionamento_competitivo": {},
                "status": "erro"
            }
    
    async def analise_fornecedores(self, razao_social: str, culturas: List[str]) -> Dict:
        """
        Identifica fornecedores atuais (sementes, defensivos, fertilizantes).
        CRÍTICO para vendas de ERP/AgTech.
        """
        logger.info(f"[FORNECEDORES] Analisando cadeia de suprimentos: {razao_social}")
        
        culturas_str = ", ".join(culturas) if culturas else "grãos"
        
        prompt = f"""ANÁLISE DE FORNECEDORES E INSUMOS AGRÍCOLAS

EMPRESA: {razao_social}
CULTURAS: {culturas_str}

OBJETIVO: Identificar fornecedores atuais para mapear oportunidades de venda.

BUSQUE INFORMAÇÕES SOBRE:

1. **PARCERIAS PÚBLICAS** (confirmadas em notícias/sites)
   - Sementes: Bayer, Corteva, Syngenta, Basf
   - Defensivos: FMC, UPL, Nufarm
   - Fertilizantes: Mosaic, Yara, Nutriem

2. **TECNOLOGIA AGRÍCOLA**
   - Agricultura de precisão: Trimble, John Deere, CNH
   - Drones/imagens: Strider, Horus, Skydrones
   - Software: Climate FieldView, Aegro, Solinftec

3. **MENÇÕES DE CONTRATOS/COMPRAS**
   Procure em:
   - Comunicados à imprensa
   - Relatórios de sustentabilidade (PDFs)
   - LinkedIn da empresa
   - Balanços financeiros

EXEMPLO (Grupo Scheffer):
- Syngenta: Parceria de 10 anos (oficial)
- Biofábrica própria: 2.6 milhões litros/ano
- Certificação regenagri: indica uso de bioinsumos

RETORNE JSON:
{{
    "fornecedores_confirmados": [
        {{
            "nome": "Empresa",
            "categoria": "sementes/defensivos/fertilizantes/tech",
            "tipo_parceria": "descrição",
            "fonte": "URL ou documento"
        }}
    ],
    "tecnologias_utilizadas": [
        {{
            "tipo": "precisão/drones/software",
            "fornecedor": "nome",
            "descricao": "uso"
        }}
    ],
    "oportunidades_venda": [
        {{
            "gap_identificado": "descrição",
            "solucao_sugerida": "produto/serviço",
            "potencial": "alto/médio/baixo"
        }}
    ]
}}

SE NÃO ENCONTRAR PARCERIAS CONFIRMADAS, deixe arrays vazios (não invente)."""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json(response)
            
            fornecedores = data.get('fornecedores_confirmados', [])
            logger.info(f"[FORNECEDORES] ✅ Identificados {len(fornecedores)} fornecedores")
            
            return data
            
        except Exception as e:
            logger.error(f"[FORNECEDORES] ❌ Erro: {e}")
            return {
                "fornecedores_confirmados": [],
                "tecnologias_utilizadas": [],
                "oportunidades_venda": [],
                "status": "erro"
            }
    
    async def analise_tendencias_mercado(self, culturas: List[str], estados: List[str]) -> Dict:
        """
        Mapeia tendências macro do agro que impactam a empresa.
        """
        logger.info(f"[TENDÊNCIAS] Analisando mercado para culturas: {culturas}")
        
        culturas_str = ", ".join(culturas) if culturas else "grãos"
        estados_str = ", ".join(estados) if estados else "Brasil"
        
        prompt = f"""ANÁLISE DE TENDÊNCIAS DO AGRONEGÓCIO

FOCO: {culturas_str} em {estados_str}
DATA DE REFERÊNCIA: Últimos 12 meses

BUSQUE INFORMAÇÕES SOBRE:

1. **PREÇOS E MERCADO**
   - Cotação atual vs 1 ano atrás
   - Previsão de safra (CONAB/USDA)
   - Exportações (China, Europa)

2. **REGULAMENTAÇÃO E SUSTENTABILIDADE**
   - Novas leis ambientais
   - Certificações em alta (regenagri, BCI, Rainforest)
   - Exigências de rastreabilidade

3. **TECNOLOGIA E INOVAÇÃO**
   - Adoção de AgTechs no Brasil (%)
   - Crescimento de agricultura de precisão
   - Novos produtos (bioinsumos, defensivos biológicos)

4. **RISCOS E DESAFIOS**
   - Clima (La Niña, El Niño)
   - Pragas emergentes
   - Custo de insumos

RETORNE JSON:
{{
    "precos_commodities": {{
        "cultura": "nome",
        "cotacao_atual_saca": "R$ X",
        "variacao_12m": "+X% ou -X%",
        "previsao_safra": "descrição CONAB"
    }},
    "tendencias_regulatorias": [
        {{
            "tema": "sustentabilidade/rastreabilidade",
            "impacto": "descrição",
            "oportunidade_venda": "solução tech"
        }}
    ],
    "tecnologias_emergentes": [
        {{
            "tipo": "drones/IA/blockchain",
            "adocao_atual_percent": "X%",
            "potencial_crescimento": "descrição"
        }}
    ],
    "riscos_identificados": []
}}

FONTES RECOMENDADAS:
- CONAB (safras)
- CEPEA (preços)
- Embrapa (tecnologia)
- Ministério da Agricultura"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=2,
                use_search=True,
                temperature=0.2
            )
            
            data = self._parse_json(response)
            logger.info(f"[TENDÊNCIAS] ✅ Análise macro concluída")
            
            return data
            
        except Exception as e:
            logger.error(f"[TENDÊNCIAS] ❌ Erro: {e}")
            return {
                "precos_commodities": {},
                "tendencias_regulatorias": [],
                "tecnologias_emergentes": [],
                "status": "erro"
            }
    
    def _parse_json(self, response: str) -> Dict:
        """Parse defensivo de JSON."""
        if not response:
            return {}
        
        try:
            # Remove markdown
            clean = response.replace("```json", "").replace("```", "").strip()
            
            # Procura por { ... }
            start = clean.find('{')
            end = clean.rfind('}')
            
            if start >= 0 and end > start:
                json_str = clean[start:end+1]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: tenta regex
        try:
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        
        logger.warning(f"[PARSE] Falha ao parsear JSON")
        return {}
