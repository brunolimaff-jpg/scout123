"""
services/intelligence_layer.py — VERSÃO ULTRA-AGRESSIVA
Inteligência competitiva com busca profunda
"""
import requests
import json
import logging
from typing import Dict, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class IntelligenceLayer:
    """
    Camada de inteligência com prompts ultra-agressivos.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    # ======== CONCORRENTES (ULTRA-AGRESSIVO) ========
    async def mapeamento_concorrentes(self, razao_social: str, culturas: List[str], estados: List[str]) -> Dict:
        """
        Mapeia concorrentes diretos na mesma região.
        """
        logger.info(f"[CONCORRENTES] Mapeando para: {razao_social}")
        
        culturas_str = ", ".join(culturas) if culturas else "soja, milho, algodão"
        estados_str = ", ".join(estados) if estados else "MT, MS, GO"
        
        prompt = f"""INTELIGÊNCIA COMPETITIVA - CONCORRENTES

EMPRESA ALVO: {razao_social}
CULTURAS: {culturas_str}
ESTADOS: {estados_str}

VOCÊ DEVE ENCONTRAR OS **TOP 5** CONCORRENTES DIRETOS:

CRITÉRIOS:
1. Operam nas MESMAS culturas
2. Operam nos MESMOS estados/regiões
3. Tamanho similar (±50% área/faturamento)

BUSQUE EM:
- Rankings do agronegócio (Valor 1000, Forbes Agro)
- Associações (APROSOJA, ABRAPA)
- Notícias do setor

EXEMPLO (se alvo = Grupo Scheffer em MT/MA):
Concorrentes: SLC Agrícola, Terra Santa, Vanguarda Agro, Grupo Bom Futuro

PARA CADA CONCORRENTE RETORNE:
{{
    "concorrentes_diretos": [
        {{
            "nome": "Razão Social",
            "cnpj": "00.000.000/0001-00 ou N/D",
            "area_estimada_hectares": 0,
            "culturas_principais": [],
            "estados_operacao": [],
            "nivel_ameaca": "Alto/Médio/Baixo",
            "diferenciais": "O que eles fazem melhor"
        }}
    ],
    "posicionamento_relativo": "descrição",
    "recomendacao_abordagem": "como se diferenciar na venda"
}}

BUSQUE DADOS REAIS - não invente nomes."""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.2
            )
            
            data = self._parse_json_response(response)
            
            num_concorrentes = len(data.get('concorrentes_diretos', []))
            logger.info(f"[CONCORRENTES] ✅ {num_concorrentes} concorrentes mapeados")
            
            return data
            
        except Exception as e:
            logger.error(f"[CONCORRENTES] ❌ Erro: {e}")
            return {
                "concorrentes_diretos": [],
                "status": "erro"
            }
    
    # ======== EXPANSÃO / M&A (ULTRA-AGRESSIVO) ========
    async def rastreio_movimentos_ma(self, razao_social: str, cpf_socios: List[str]) -> Dict:
        """
        Rastreia notícias de expansão, compra de terras, M&A.
        """
        logger.info(f"[M&A] Rastreando movimentações: {razao_social}")
        
        prompt = f"""INTELIGÊNCIA: MOVIMENTOS DE EXPANSÃO

EMPRESA: {razao_social}

BUSQUE NOTÍCIAS DOS **ÚLTIMOS 3 ANOS** sobre:

1. **COMPRA DE TERRAS/FAZENDAS**
   - Municípios adquiridos
   - Área em hectares
   - Valor da transação (se mencionado)

2. **FUSÕES & AQUISIÇÕES**
   - Comprou outras empresas?
   - Foi alvo de compra?
   - Parcerias estratégicas

3. **INVESTIMENTOS EM ATIVOS**
   - Novas fábricas/silos
   - Irrigação
   - Mecanização

4. **CAPITAL ABERTO / IPO**
   - Planeja abrir capital?
   - Rodadas de investimento

FONTES PRIORITÁRIAS:
- Valor Econômico (seção Agronegócio)
- Globo Rural
- Brazil Journal
- Site da empresa (Press releases)

RETORNE JSON:
{{
    "aquisicoes_ultimos_3_anos": [
        {{
            "ano": 0,
            "tipo": "Compra de terra/M&A/Investimento",
            "descricao": "",
            "valor": "R$ 0 ou N/D",
            "impacto": "descrição"
        }}
    ],
    "tendencia": "Expansão agressiva/Estável/Retração",
    "pipeline_provavel": "O que podem fazer nos próximos 12 meses",
    "momento_ideal_abordagem": "Agora/Aguardar/Não priorizar"
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[M&A] ✅ Tendência: {data.get('tendencia', 'N/D')}")
            return data
            
        except Exception as e:
            logger.error(f"[M&A] ❌ Erro: {e}")
            return {
                "aquisicoes_ultimos_3_anos": [],
                "tendencia": "Desconhecida",
                "status": "erro"
            }
    
    # ======== LIDERANÇA (ULTRA-AGRESSIVO) ========
    async def perfilamento_lideranca(self, razao_social: str, socios: List[Dict]) -> Dict:
        """
        Perfil dos sócios/executivos.
        """
        if not socios:
            return {"executivos_principais": [], "status": "sem_socios"}
        
        logger.info(f"[LIDERANÇA] Perfilando executivos de {razao_social}")
        
        # Pega top 3 sócios
        socios_str = "\n".join([f"- {s.get('nome', 'N/D')} (CPF: {s.get('cpf', 'N/D')[:3]}.***.***-**)" 
                                 for s in socios[:3]])
        
        prompt = f"""INTELIGÊNCIA: PERFIL DE LIDERANÇA

EMPRESA: {razao_social}

SÓCIOS/EXECUTIVOS CONHECIDOS:
{socios_str}

PARA CADA PESSOA, BUSQUE:

1. **LinkedIn**
   - Cargo atual
   - Formação acadêmica (universidade, MBA)
   - Experiência anterior (empresas)

2. **Notícias/Entrevistas**
   - Citações em mídia
   - Participação em eventos do setor
   - Visão de negócio

3. **Perfil Psicográfico**
   - Conservador/Inovador
   - Focado em tecnologia?
   - Aberto a mudanças?

4. **Red Flags**
   - Processos judiciais pessoais
   - Polêmicas
   - Histórico de calotes

RETORNE JSON:
{{
    "executivos_principais": [
        {{
            "nome": "",
            "cargo": "CEO/Diretor/Sócio",
            "formacao": "Agronomia USP + MBA FGV",
            "experiencia_anos_agro": 0,
            "perfil": "Inovador/Tradicional/Técnico",
            "dores_declaradas": ["falta de conectividade", "custo diesel"],
            "decisor_final": true/false,
            "abordagem_recomendada": "técnica/ROI/emocional"
        }}
    ],
    "cultura_organizacional": "Hierárquica/Horizontal/Familiar",
    "dica_abordagem_comercial": ""
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=2,
                use_search=True,
                temperature=0.2
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[LIDERANÇA] ✅ {len(data.get('executivos_principais', []))} perfis gerados")
            return data
            
        except Exception as e:
            logger.error(f"[LIDERANÇA] ❌ Erro: {e}")
            return {
                "executivos_principais": [],
                "status": "erro"
            }
    
    # ======== STACK TECNOLÓGICO (ULTRA-AGRESSIVO) ========
    async def mapeamento_stack_tecnologico(self, razao_social: str, cnpj: str) -> Dict:
        """
        Mapeia tecnologias que a empresa JÁ USA.
        """
        logger.info(f"[TECH STACK] Mapeando tecnologias: {razao_social}")
        
        prompt = f"""INTELIGÊNCIA: STACK TECNOLÓGICO ATUAL

EMPRESA: {razao_social}

VOCÊ PRECISA DESCOBRIR O QUE ELES **JÁ USAM**:

1. **ERP ATUAL**
   - SAP / Totvs / Senior / Sankhya / Outros
   - BUSQUE: vagas de emprego citando ERP, cases de implementação

2. **AGRICULTURA DE PRECISÃO**
   - Climate FieldView / Aegro / Agrosmart
   - Telemetria de máquinas (John Deere Operations Center, etc)

3. **SOFTWARE DE GESTÃO AGRÍCOLA**
   - Granular / FarmLogs / Strider

4. **PARCEIROS TECNOLÓGICOS**
   - Yara (agricultura digital)
   - Monsanto/Bayer (Climate FieldView)

FONTES:
- LinkedIn da empresa (posts sobre tecnologia)
- Vagas de emprego (requisitos técnicos)
- Cases de clientes das empresas de software
- Apresentações em eventos (Agrishow, TechShow)

RETORNE JSON:
{{
    "erp_atual": "Nome ou N/D",
    "solucoes_agricolas": [],
    "parceiros_tech": [],
    "gaps_identificados": ["Não tem telemetria", "ERP desatualizado"],
    "maturidade_digital": "Baixa/Média/Alta",
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
            logger.info(f"[TECH STACK] ✅ ERP detectado: {data.get('erp_atual', 'N/D')}")
            return data
            
        except Exception as e:
            logger.error(f"[TECH STACK] ❌ Erro: {e}")
            return {
                "erp_atual": "N/D",
                "solucoes_agricolas": [],
                "status": "erro"
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse ultra-defensivo de JSON."""
        if not response:
            return {}
        
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            start = clean.find('{')
            end = clean.rfind('}')
            if start >= 0 and end > start:
                json_str = clean[start:end+1]
                return json.loads(json_str)
        except:
            pass
        
        try:
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        
        logger.warning(f"[PARSE] Falha ao parsear JSON")
        return {}
