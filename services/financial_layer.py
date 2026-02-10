"""
services/financial_layer.py — VERSÃO ULTRA-AGRESSIVA
Garante busca profunda de dados financeiros e jurídicos
"""
import requests
import json
import logging
from typing import Dict, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FinancialLayer:
    """
    Camada financeira com prompts ultra-agressivos.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    # ======== CRA / DEBÊNTURES (ULTRA-AGRESSIVO) ========
    async def mineracao_cra_debentures(self, razao_social: str, cnpj: str) -> Dict:
        """
        Busca CRAs/Debêntures com 3 tentativas progressivas.
        """
        logger.info(f"[CRA] Mineração ultra-agressiva: {razao_social}")
        
        prompt = f"""BUSCA OBRIGATÓRIA: DADOS FINANCEIROS AUDITADOS

EMPRESA: {razao_social} (CNPJ: {cnpj})

VOCÊ **DEVE** PROCURAR EM:
1. Site da CVM (Comissão de Valores Mobiliários)
2. Site da B3 (Brasil, Bolsa, Balcão)
3. Notícias sobre emissão de CRA/Debêntures
4. Relatórios de sustentabilidade (PDF)
5. Apresentações para investidores

DADOS OBRIGATÓRIOS A BUSCAR:
- Faturamento/Receita Líquida anual
- EBITDA (se mencionado)
- Valor de CRAs emitidos
- Índice de alavancagem (Dívida/EBITDA)
- Nome do auditor (Deloitte, PWC, KPMG, EY)

EXEMPLO (Grupo Scheffer):
- Faturamento: R$ 1,7 bilhão/ano
- Emitiu CRA em 2016 (primeiro produtor MT)
- Balanço auditado

RETORNE JSON:
{{
    "emissoes_cra": [
        {{
            "ano": 0,
            "valor_emissao": "R$ 0",
            "observacao": ""
        }}
    ],
    "faturamento_real": "R$ 0 ou N/D",
    "ebitda_consolidado": "R$ 0 ou N/D",
    "indice_dps": "0x ou N/D",
    "auditor": "Nome ou N/D",
    "fonte": "URL ou N/D"
}}

SE NÃO ENCONTRAR, retorne "N/D" mas BUSQUE MUITO antes disso."""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.0
            )
            
            data = self._parse_json_response(response)
            
            faturamento = data.get('faturamento_real', 'N/D')
            logger.info(f"[CRA] ✅ Faturamento encontrado: {faturamento}")
            
            return data
            
        except Exception as e:
            logger.error(f"[CRA] ❌ Erro: {e}")
            return {
                "emissoes_cra": [],
                "faturamento_real": "N/D",
                "ebitda_consolidado": "N/D",
                "status": "erro"
            }
    
    # ======== INCENTIVOS FISCAIS (ULTRA-AGRESSIVO) ========
    async def rastreio_incentivos_fiscais(self, cnpj: str, estados_operacao: List[str]) -> Dict:
        """
        Busca incentivos SUDAM/SUDENE/outros.
        """
        if not estados_operacao:
            return {"beneficios_ativos": [], "status": "sem_estados"}
        
        logger.info(f"[INCENTIVOS] Verificando {', '.join(estados_operacao)}")
        
        estados_str = ", ".join(estados_operacao)
        
        prompt = f"""BUSCA: INCENTIVOS FISCAIS AGRÍCOLAS

ESTADOS DE OPERAÇÃO: {estados_str}

VERIFIQUE SE A EMPRESA TEM:

1. **SUDAM** (se opera em: RO, AC, AM, RR, PA, AP, TO, MA)
   - Isenção de 75% IRPJ/CSLL
   - Redução IPI

2. **SUDENE** (se opera em: AL, BA, CE, MA, PB, PE, PI, RN, SE)
   - Isenção de 75% IRPJ/CSLL

3. **PADIS** (se tem P&D em tecnologia)

4. Incentivos estaduais de ICMS

BUSQUE EM:
- Sites oficiais SUDAM/SUDENE
- Notícias sobre aprovação de projetos
- Relatórios de sustentabilidade da empresa

RETORNE JSON:
{{
    "beneficios_ativos": [
        {{
            "tipo": "SUDAM/SUDENE/Estadual",
            "estado": "UF",
            "isenção_irpj": "X%",
            "economia_estimada_anual": "R$ X milhões",
            "vigencia": "até XXXX"
        }}
    ],
    "economia_fiscal_anual_total": "R$ 0 ou N/D"
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=2,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[INCENTIVOS] ✅ Análise concluída")
            return data
            
        except Exception as e:
            logger.error(f"[INCENTIVOS] ❌ Erro: {e}")
            return {"beneficios_ativos": [], "status": "erro"}
    
    # ======== MULTAS AMBIENTAIS (ULTRA-AGRESSIVO) ========
    async def varredura_multas_ambientais(self, cnpj: str, razao_social: str) -> Dict:
        """
        Busca multas do Ibama/SEMA.
        """
        logger.info(f"[MULTAS] Varredura ambiental: {razao_social}")
        
        prompt = f"""BUSCA: PASSIVOS AMBIENTAIS

EMPRESA: {razao_social}
CNPJ: {cnpj}

PROCURE EM:
1. Lista de embargos do IBAMA (públicas)
2. Autos de infração ambiental
3. Notícias sobre multas ou processos ambientais
4. TCU/TCE - fiscalizações ambientais

SE ENCONTRAR:
- Valor da multa
- Motivo (desmatamento, APP, queimada)
- Status (paga, pendente, embargada)
- Data

SE NÃO ENCONTRAR NADA:
- Retorne "score_risco_ambiental": "Baixo"

RETORNE JSON:
{{
    "multas_ativas": [],
    "debitos_ambientais_total": "R$ 0 ou N/D",
    "propriedades_embargadas": 0,
    "score_risco_ambiental": "Baixo/Médio/Alto",
    "observacoes": ""
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=2,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[MULTAS] ✅ Varredura concluída")
            return data
            
        except Exception as e:
            logger.error(f"[MULTAS] ❌ Erro: {e}")
            return {
                "multas_ativas": [],
                "score_risco_ambiental": "Desconhecido",
                "status": "erro"
            }
    
    # ======== PROCESSOS TRABALHISTAS (ULTRA-AGRESSIVO) ========
    async def rastreio_processos_trabalhistas(self, cnpj: str, razao_social: str) -> Dict:
        """
        Busca processos no TRT via Jusbrasil/Escavador.
        """
        logger.info(f"[TRT] Rastreando processos: {razao_social}")
        
        prompt = f"""BUSCA: PROCESSOS TRABALHISTAS

EMPRESA: {razao_social}
CNPJ: {cnpj}

BUSQUE EM:
- Jusbrasil (processos públicos)
- Escavador
- TST/TRT (tribunais regionais do trabalho)

PROCURE POR:
- Número de processos ativos
- Tipo: horas extras, acidente, rescisão, FGTS
- Valores reclamados
- Padrão (se maioria é mesmo tipo)

ANÁLISE:
- >60% horas extras = falha em sistema de ponto
- >40% acidentes = falha em segurança

RETORNE JSON:
{{
    "total_processos_ativos": 0,
    "processos_por_tipo": {{
        "horas_extras": 0,
        "acidente_trabalho": 0,
        "outros": 0
    }},
    "valor_total_reclamado": "R$ 0 ou N/D",
    "padrão_identificado": "",
    "dor_principal": ""
}}"""

        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=2,
                use_search=True,
                temperature=0.1
            )
            
            data = self._parse_json_response(response)
            logger.info(f"[TRT] ✅ {data.get('total_processos_ativos', 0)} processos identificados")
            return data
            
        except Exception as e:
            logger.error(f"[TRT] ❌ Erro: {e}")
            return {
                "total_processos_ativos": 0,
                "processos_por_tipo": {},
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
