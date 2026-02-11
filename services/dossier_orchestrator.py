"""
services/orchestrator_v3.py — BANDEIRANTE DIGITAL v3.0 MODO DEUS
Orquestrador completo das 10 fases de inteligência de mercado.
"""

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from services.reputation_layer import ReputationLayer
from services.tax_incentives_layer import TaxIncentivesLayer
from services.territorial_layer import TerritorialLayer
from services.logistics_layer import LogisticsLayer
from services.corporate_structure_layer import CorporateStructureLayer
from services.executive_profiler import ExecutiveProfiler

logger = logging.getLogger(__name__)

class BandeiranteOrchestratorV3:
    """Bandeirante Digital v3.0 - MODO DEUS COMPLETO"""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        self.reputation_layer = ReputationLayer(gemini_service)
        self.tax_layer = TaxIncentivesLayer(gemini_service)
        self.territorial_layer = TerritorialLayer(gemini_service)
        self.logistics_layer = LogisticsLayer(gemini_service)
        self.corporate_layer = CorporateStructureLayer(gemini_service)
        self.executive_profiler = ExecutiveProfiler(gemini_service)
        
        logger.info("[BANDEIRANTE V3] Orchestrator inicializado")
    
    async def investigacao_completa(
        self,
        empresa: str,
        cnpj: str = "",
        uf: str = "",
        socios: Optional[List[Dict]] = None,
        modo: str = "completo"
    ) -> Dict:
        """Executa investigação completa em todas as 10 fases."""
        logger.info(f"[BANDEIRANTE V3] Iniciando investigação: {empresa}")
        
        start_time = datetime.now()
        results = {
            "metadata": {
                "empresa": empresa,
                "cnpj": cnpj,
                "uf": uf,
                "modo": modo,
                "timestamp_inicio": start_time.isoformat(),
                "versao": "3.0-MODO-DEUS"
            },
            "fases": {}
        }
        
        try:
            # FASE -1
            logger.info("[FASE -1] Shadow Reputation...")
            reputation = await self.reputation_layer.checagem_completa(empresa, cnpj)
            results["fases"]["fase_-1_reputation"] = reputation
            
            # FASE 1
            logger.info("[FASE 1] Incentivos fiscais...")
            incentivos = await self.tax_layer.mapeamento_completo(empresa, cnpj, uf)
            results["fases"]["fase_1_incentivos"] = incentivos
            
            # FASE 2
            logger.info("[FASE 2] Territorial...")
            territorial = await self.territorial_layer.mapeamento_territorial_completo(empresa, cnpj)
            results["fases"]["fase_2_territorial"] = territorial
            
            # FASE 3
            logger.info("[FASE 3] Logística...")
            logistica = await self.logistics_layer.mapeamento_logistico_completo(empresa, cnpj)
            results["fases"]["fase_3_logistica"] = logistica
            
            # FASE 4
            logger.info("[FASE 4] Societário...")
            societario = await self.corporate_layer.mapeamento_societario_completo(
                empresa, cnpj, socios or []
            )
            results["fases"]["fase_4_societario"] = societario
            
            # FASE 5
            logger.info("[FASE 5] Executivos...")
            executivos = await self.executive_profiler.profiling_completo(empresa)
            results["fases"]["fase_5_executivos"] = executivos
            
            # FASE 6
            logger.info("[FASE 6] Triggers...")
            triggers = await self._identificar_triggers(results)
            results["fases"]["fase_6_triggers"] = triggers
            
            # FASE 7
            logger.info("[FASE 7] Psicologia...")
            psicologia = await self._mapear_psicologia(results)
            results["fases"]["fase_7_psicologia"] = psicologia
            
            # FASE 10
            logger.info("[FASE 10] Matriz...")
            matriz = self._calcular_matriz_priorizacao(results)
            results["matriz_priorizacao"] = matriz
            
            # RECOMENDAÇÕES
            results["recomendacoes"] = self._gerar_recomendacoes(results)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            results["metadata"]["timestamp_fim"] = end_time.isoformat()
            results["metadata"]["duracao_segundos"] = duration
            
            logger.info(f"[BANDEIRANTE V3] Completo em {duration:.1f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"[BANDEIRANTE V3] Erro: {e}", exc_info=True)
            results["erro"] = str(e)
            return results
    
    async def _identificar_triggers(self, results: Dict) -> Dict:
        """FASE 6: Identifica trigger events."""
        triggers_identificados = []
        urgencia = "BAIXA"
        
        territorial = results.get("fases", {}).get("fase_2_territorial", {})
        licencas = territorial.get("licencas_ambientais", {})
        licencas_recentes = licencas.get("licencas_recentes_6m", 0)
        
        if licencas_recentes > 0:
            triggers_identificados.append({
                "tipo": "LICENCA_RECENTE",
                "severidade": "CRITICA",
                "descricao": f"{licencas_recentes} licença(s) recente(s)"
            })
            urgencia = "CRITICA"
        
        mes_atual = datetime.now().month
        contexto_sazonal = self._contexto_sazonal_agro(mes_atual)
        
        return {
            "triggers": triggers_identificados,
            "total_triggers": len(triggers_identificados),
            "urgencia_geral": urgencia,
            "contexto_sazonal": contexto_sazonal,
            "melhor_momento_contato": "PRÓXIMOS 30 DIAS"
        }
    
    def _contexto_sazonal_agro(self, mes: int) -> Dict:
        """Contexto sazonal."""
        cal = {
            1: {"periodo": "Pré-safra", "abertura": "ALTA"},
            2: {"periodo": "Pré-safra", "abertura": "ALTA"},
            10: {"periodo": "Planejamento", "abertura": "CRITICA"},
        }
        return cal.get(mes, {"periodo": "Normal", "abertura": "MEDIA"})
    
    async def _mapear_psicologia(self, results: Dict) -> Dict:
        """FASE 7."""
        return {
            "gatilho_psicologico": "ROI + Compliance",
            "canal_preferido": "LinkedIn",
            "storytelling_abertura": "Storytelling personalizado aqui"
        }
    
    def _calcular_matriz_priorizacao(self, results: Dict) -> Dict:
        """FASE 10."""
        territorial = results.get("fases", {}).get("fase_2_territorial", {})
        area_total = territorial.get("dados_fundiarios", {}).get("area_total_ha", 0)
        
        if area_total > 100000:
            score = 90
        elif area_total > 50000:
            score = 75
        else:
            score = 50
        
        status = "STRIKE" if score >= 80 else "QUALIFICAR"
        
        return {
            "score_final": score,
            "status": status,
            "classificacao": f"🔥 {status}",
            "area_total_ha": area_total
        }
    
    def _gerar_recomendacoes(self, results: Dict) -> Dict:
        """Gera recomendações."""
        matriz = results.get("matriz_priorizacao", {})
        
        return {
            "acao_recomendada": "AÇÃO IMEDIATA",
            "status": matriz.get("status"),
            "score": matriz.get("score_final"),
            "proximos_passos": [
                "1. Contatar nas próximas 24-48h",
                "2. Agendar call de 20 minutos",
                "3. Enviar proposta em 72h"
            ]
        }
