"""
services/financial_layer.py — VERSÃO BLINDADA
Inclui extrator de JSON via Regex para evitar perda de dados quando a IA "fala demais".
"""
import logging
import re
import json
import asyncio
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class FinancialLayer:
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def _extrair_json_seguro(self, texto: str) -> Dict:
        """
        Remove textos extras (ex: 'Aqui está o JSON') e extrai apenas o objeto.
        """
        try:
            # Tenta limpar marcadores de código
            clean = texto.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            # Se falhar, usa Regex para achar o primeiro '{' e o último '}'
            try:
                match = re.search(r'\{.*\}', texto, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
            except:
                pass
            return {}
        return {}

    async def mineracao_cra_debentures(self, empresa: str, cnpj: str) -> Dict:
        """
        Busca profunda de saúde financeira em emissores de dívida (CVM/B3).
        """
        logger.info(f"[CRA] Mineração ultra-agressiva: {empresa}")
        
        prompt = f"""
        ATUE COMO: Auditor de Mercado de Capitais (CVM).
        ALVO: {empresa} (CNPJ base: {cnpj[:8] if cnpj else 'N/D'})
        
        MISSÃO: Encontrar dados financeiros reais em prospectos de CRA, Debêntures ou Balanços.
        
        PASSO 1: Busque por "{empresa} faturamento 2024", "{empresa} rating", "{empresa} emissão CRA".
        PASSO 2: Se achar CRA/Debênture, extraia o Faturamento Anual informado no prospecto (EBITDA/Receita Líquida).
        
        RETORNE JSON ESTRITO:
        {{
            "tem_cra_ativo": true/false,
            "faturamento_real": "Valor monetário explícito (ex: R$ 1.2 Bilhões em 2023) ou 'N/D'",
            "ebitda_consolidado": "Valor ou 'N/D'",
            "auditoria": "Nome da Auditoria (ex: KPMG, PwC) ou 'N/D'",
            "fonte_dado": "Link ou nome do documento encontrado"
        }}
        """
        
        try:
            # Temperatura 0.1 para precisão máxima
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            
            # USANDO O EXTRATOR SEGURO AGORA
            dados = self._extrair_json_seguro(response)
            
            # Log de sucesso para debug
            fat = dados.get("faturamento_real", "N/D")
            logger.info(f"[CRA] ✅ Resultado parseado: {fat}")
            
            return dados

        except Exception as e:
            logger.error(f"[CRA] Erro fatal na busca: {e}")
            return {}
