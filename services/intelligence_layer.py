"""
services/intelligence_layer.py — VERSÃO FINAL (PEOPLE & CAPEX)
Camada de Inteligência Expandida para Auditoria Forense.
Inclui: Decisores, Investimentos, Tech Stack e Concorrentes.
"""
import logging
import re
import json
import asyncio
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class IntelligenceLayer:
    """
    Camada de Inteligência Competitiva.
    Responsável por varrer a web em busca de:
    1. Stack Tecnológico (ERP, Agritech)
    2. Pessoas Chave (Decisores)
    3. Investimentos (CAPEX)
    4. Concorrência
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def mapeamento_stack_tecnologico(self, empresa: str, cnpj: str) -> Dict:
        """Busca agressiva por softwares e maturidade digital."""
        logger.info(f"[TECH STACK] Mapeando tecnologias: {empresa}")
        
        prompt = f"""
        ATUE COMO: Tech Hunter Agro.
        ALVO: {empresa}
        
        MISSÃO: Descubra quais softwares eles usam.
        BUSQUE POR TERMOS: "{empresa} vaga TI", "{empresa} analista sistemas", "{empresa} case sucesso SAP/Totvs/Senior/Oracle", "{empresa} Linkedin stack".
        
        RETORNE JSON:
        {{
            "erp_atual": "Nome do ERP (ex: SAP, Totvs, Senior, Protheus) ou 'N/D'",
            "sistemas_agricolas": ["Gatec", "Pims", "Solinftec", "Climate Fieldview", etc],
            "maturidade_digital": "Baixa/Média/Alta (Justifique com base nas ferramentas)",
            "infra_nuvem": "AWS/Azure/On-Premise (se achar)"
        }}
        """
        try:
            # Temperatura baixa para evitar alucinação de softwares que não existem
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except Exception as e:
            logger.warning(f"Erro Tech Stack: {e}")
            return {}

    async def mapeamento_decisores(self, empresa: str) -> Dict:
        """
        Busca nomes de diretores e gerentes chave.
        Foco: TI, Financeiro, Agrícola, Compras.
        """
        logger.info(f"[PEOPLE] Caçando organograma: {empresa}")
        
        prompt = f"""
        ATUE COMO: Headhunter Executivo.
        ALVO: {empresa} (Agronegócio)
        
        TAREFA: Encontre nomes de executivos chave e gestores.
        BUSQUE POR: "Diretor {empresa}", "Gerente TI {empresa}", "CFO {empresa}", "Gerente Fazenda {empresa}", "Sócio {empresa}".
        
        RETORNE JSON:
        {{
            "diretoria": ["Nome (Cargo)", "Nome (Cargo)"],
            "ti_tecnologia": ["Nome (Cargo) - Foco TI/Sistemas"],
            "operacoes_campo": ["Nome (Gerente Agrícola/Fazenda)"],
            "estimativa_funcionarios": "Número estimado (ex: 500-1000) baseada no LinkedIn/Mídia"
        }}
        """
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except Exception as e:
            logger.warning(f"Erro Mapeamento Decisores: {e}")
            return {}

    async def mapeamento_investimentos_capex(self, empresa: str) -> List[str]:
        """
        Busca onde a empresa vai gastar dinheiro (CAPEX).
        """
        logger.info(f"[CAPEX] Buscando planos de investimento: {empresa}")
        prompt = f"""
        ATUE COMO: Analista de M&A.
        ALVO: {empresa}
        
        DESCUBRA: Planos de expansão anunciados (2024-2026).
        - Construção de novas unidades (armazéns, usinas, algodoeiras)?
        - Compra de terras?
        - Investimento em maquinário ou tecnologia?
        - Captação de CRA/Debêntures para investimento?
        
        RETORNE LISTA DE STRINGS:
        ["Investimento de R$ X milhões em nova algodoeira em Sapezal (Fonte: Site Y)", "Plano de dobrar área até 2026"]
        """
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else []
        except Exception as e:
            logger.warning(f"Erro CAPEX: {e}")
            return []

    async def mapeamento_concorrentes(self, empresa: str, regioes: List[str], culturas: List[str]) -> Dict:
        """Analisa quem compete com o alvo na região."""
        prompt = f"""
        ATUE COMO: Estrategista de Mercado Agro.
        ALVO: {empresa}
        REGIÃO: {', '.join(regioes) if regioes else 'Brasil'}
        CULTURAS: {', '.join(culturas) if culturas else 'Grãos/Algodão'}
        
        1. Identifique 3 concorrentes diretos na região (vizinhos ou mesmo porte).
        2. Qual o diferencial competitivo do alvo?
        
        RETORNE JSON: {{ "concorrentes": ["Empresa A", "Empresa B"], "posicionamento_relativo": "Texto curto explicando a posição no mercado" }}
        """
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.2)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except Exception as e:
            logger.warning(f"Erro Concorrentes: {e}")
            return {}
