"""
services/orchestrator.py — BANDEIRANTE DIGITAL ORCHESTRATOR
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

class BandeiranteOrchestrator:
    """Bandeirante Digital - Orchestrator Completo"""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        self.reputation_layer = ReputationLayer(gemini_service)
        self.tax_layer = TaxIncentivesLayer(gemini_service)
        self.territorial_layer = TerritorialLayer(gemini_service)
        self.logistics_layer = LogisticsLayer(gemini_service)
        self.corporate_layer = CorporateStructureLayer(gemini_service)
        self.executive_profiler = ExecutiveProfiler(gemini_service)
        
        logger.info("[BANDEIRANTE] Orchestrator inicializado")
    
    async def investigacao_completa(
        self,
        empresa: str,
        cnpj: str = "",
        uf: str = "",
        socios: Optional[List[Dict]] = None,
        modo: str = "completo"
    ) -> Dict:
        """Executa investigação completa em todas as 10 fases."""
        logger.info(f"[BANDEIRANTE] Iniciando investigação: {empresa}")
        
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
            # FASE -1: SHADOW REPUTATION
            logger.info("[FASE -1] Shadow Reputation...")
            reputation = await self.reputation_layer.checagem_completa(empresa, cnpj)
            results["fases"]["fase_-1_reputation"] = reputation
            
            # FASE 1: INCENTIVOS FISCAIS
            logger.info("[FASE 1] Incentivos fiscais...")
            incentivos = await self.tax_layer.mapeamento_completo(empresa, cnpj, uf)
            results["fases"]["fase_1_incentivos"] = incentivos
            
            # FASE 2: TERRITORIAL
            logger.info("[FASE 2] Territorial...")
            territorial = await self.territorial_layer.mapeamento_territorial_completo(empresa, cnpj)
            results["fases"]["fase_2_territorial"] = territorial
            
            # FASE 3: LOGÍSTICA
            logger.info("[FASE 3] Logística...")
            logistica = await self.logistics_layer.mapeamento_logistico_completo(empresa, cnpj)
            results["fases"]["fase_3_logistica"] = logistica
            
            # FASE 4: ESTRUTURA SOCIETÁRIA
            logger.info("[FASE 4] Societário...")
            societario = await self.corporate_layer.mapeamento_societario_completo(
                empresa, cnpj, socios or []
            )
            results["fases"]["fase_4_societario"] = societario
            
            # FASE 5: PROFILING EXECUTIVOS
            logger.info("[FASE 5] Executivos...")
            executivos = await self.executive_profiler.profiling_completo(empresa)
            results["fases"]["fase_5_executivos"] = executivos
            
            # FASE 6: TRIGGER EVENTS
            logger.info("[FASE 6] Triggers...")
            triggers = await self._identificar_triggers(results)
            results["fases"]["fase_6_triggers"] = triggers
            
            # FASE 7: PSICOLOGIA & GATILHOS
            logger.info("[FASE 7] Psicologia...")
            psicologia = await self._mapear_psicologia(results)
            results["fases"]["fase_7_psicologia"] = psicologia
            
            # FASE 10: MATRIZ DE PRIORIZAÇÃO
            logger.info("[FASE 10] Matriz...")
            matriz = self._calcular_matriz_priorizacao(results)
            results["matriz_priorizacao"] = matriz
            
            # RECOMENDAÇÕES FINAIS
            results["recomendacoes"] = self._gerar_recomendacoes(results)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            results["metadata"]["timestamp_fim"] = end_time.isoformat()
            results["metadata"]["duracao_segundos"] = duration
            
            logger.info(f"[BANDEIRANTE] Completo em {duration:.1f}s - Score: {matriz.get('score_final', 0)}")
            
            return results
            
        except Exception as e:
            logger.error(f"[BANDEIRANTE] Erro: {e}", exc_info=True)
            results["erro"] = str(e)
            return results
    
    async def _identificar_triggers(self, results: Dict) -> Dict:
        """FASE 6: Identifica trigger events."""
        triggers_identificados = []
        urgencia = "BAIXA"
        
        # Analisa licenças recentes
        territorial = results.get("fases", {}).get("fase_2_territorial", {})
        licencas = territorial.get("licencas_ambientais", {})
        licencas_recentes = licencas.get("licencas_recentes_6m", 0)
        
        if licencas_recentes > 0:
            triggers_identificados.append({
                "tipo": "LICENCA_RECENTE",
                "severidade": "CRITICA",
                "descricao": f"{licencas_recentes} licença(s) emitida(s) recentemente",
                "implicacao": "Novos ativos = precisa de sistema urgente"
            })
            urgencia = "CRITICA"
        
        # Analisa multas fiscais
        incentivos = results.get("fases", {}).get("fase_1_incentivos", {})
        multas = incentivos.get("sancoes_multas", {}).get("total_multas_quantidade", 0)
        
        if multas > 0:
            triggers_identificados.append({
                "tipo": "MULTAS_FISCAIS",
                "severidade": "ALTA",
                "descricao": f"{multas} multa(s) fiscal(is)",
                "implicacao": "Risco de perda de incentivos"
            })
            if urgencia != "CRITICA":
                urgencia = "ALTA"
        
        # Contexto sazonal
        mes_atual = datetime.now().month
        contexto_sazonal = self._contexto_sazonal_agro(mes_atual)
        
        return {
            "triggers": triggers_identificados,
            "total_triggers": len(triggers_identificados),
            "urgencia_geral": urgencia,
            "contexto_sazonal": contexto_sazonal,
            "melhor_momento_contato": self._calcular_melhor_momento(triggers_identificados, mes_atual)
        }
    
    def _contexto_sazonal_agro(self, mes: int) -> Dict:
        """Contexto sazonal do agronegócio."""
        calendario = {
            1: {"periodo": "Pré-safra", "abertura": "ALTA"},
            2: {"periodo": "Pré-safra", "abertura": "ALTA"},
            7: {"periodo": "Pós-colheita", "abertura": "ALTA"},
            10: {"periodo": "Planejamento", "abertura": "CRITICA"},
            4: {"periodo": "Safra", "abertura": "BAIXA"},
        }
        return calendario.get(mes, {"periodo": "Normal", "abertura": "MEDIA"})
    
    def _calcular_melhor_momento(self, triggers: List[Dict], mes_atual: int) -> str:
        """Calcula melhor momento para contato."""
        if any(t.get("severidade") == "CRITICA" for t in triggers):
            return "IMEDIATAMENTE - Trigger crítico identificado"
        
        sazonal = self._contexto_sazonal_agro(mes_atual)
        if sazonal.get("abertura") in ["CRITICA", "ALTA"]:
            return f"AGORA - {sazonal.get('periodo')} favorável"
        
        return "PRÓXIMOS 30 DIAS"
    
    async def _mapear_psicologia(self, results: Dict) -> Dict:
        """FASE 7: Mapa psicológico e storytelling."""
        territorial = results.get("fases", {}).get("fase_2_territorial", {})
        area_total = territorial.get("dados_fundiarios", {}).get("area_total_ha", 0)
        empresa = results["metadata"]["empresa"]
        
        storytelling = f"""Oi [Nome],

Pesquisei a {empresa} e vi que vocês têm {area_total:,.0f} hectares.

Conversando com empresas do seu porte, uma coisa que sempre vira problema é rastreabilidade e compliance.

Como vocês fazem isso hoje?"""
        
        return {
            "storytelling_abertura": storytelling,
            "gatilho_psicologico": "ROI + Compliance + Escalabilidade",
            "canal_preferido": "LinkedIn",
            "tom_recomendado": "Consultivo, não vendedor"
        }
    
    def _calcular_matriz_priorizacao(self, results: Dict) -> Dict:
        """FASE 10: Matriz de priorização."""
        territorial = results.get("fases", {}).get("fase_2_territorial", {})
        area_total = territorial.get("dados_fundiarios", {}).get("area_total_ha", 0)
        
        incentivos = results.get("fases", {}).get("fase_1_incentivos", {})
        total_incentivos = incentivos.get("incentivos_estaduais", {}).get("total_incentivos", 0)
        
        # Cálculo de score
        score_area = min(40, (area_total / 2500))  # Máximo 40 pontos
        score_incentivos = min(35, total_incentivos * 10)  # Máximo 35 pontos
        score_base = 25  # Pontos base
        
        score_final = int(score_area + score_incentivos + score_base)
        
        # Classificação
        if score_final >= 80:
            status = "STRIKE"
            classificacao = "🔥 STRIKE IMEDIATO"
        elif score_final >= 60:
            status = "QUALIFICAR"
            classificacao = "🎯 QUALIFICAR"
        else:
            status = "MONITORAR"
            classificacao = "📊 MONITORAR"
        
        return {
            "score_final": score_final,
            "classificacao": classificacao,
            "status": status,
            "area_total_ha": area_total,
            "total_incentivos": total_incentivos
        }
    
    def _gerar_recomendacoes(self, results: Dict) -> Dict:
        """Gera recomendações finais de ação."""
        matriz = results.get("matriz_priorizacao", {})
        status = matriz.get("status", "MONITORAR")
        score = matriz.get("score_final", 0)
        
        if status == "STRIKE":
            acao = "AÇÃO IMEDIATA"
            passos = [
                "1. Contatar decisor nas próximas 24-48h",
                "2. Usar storytelling personalizado do dossiê",
                "3. Agendar call de 20 minutos",
                "4. Enviar proposta customizada em 72h",
                "5. Follow-up em 1 semana"
            ]
            decisor = "CEO ou Diretor Geral"
            gatilho = "Inovação + Case de Sucesso + ROI"
            
        elif status == "QUALIFICAR":
            acao = "QUALIFICAR EM 7-15 DIAS"
            passos = [
                "1. Pesquisa adicional sobre contexto atual",
                "2. Monitorar movimentações no LinkedIn",
                "3. Preparar proposta técnica detalhada",
                "4. Identificar contato interno de TI",
                "5. Abordagem consultiva em 2 semanas"
            ]
            decisor = "Gerente de TI ou Operações"
            gatilho = "Eficiência Operacional + Compliance"
            
        else:
            acao = "MONITORAR POR 30-60 DIAS"
            passos = [
                "1. Adicionar empresa ao pipeline de monitoramento",
                "2. Configurar alertas de triggers (licenças, vagas)",
                "3. Nutrir com conteúdo relevante",
                "4. Reavaliar trimestralmente",
                "5. Aguardar sinal de abertura"
            ]
            decisor = "Aguardar definição"
            gatilho = "Aguardar trigger adequado"
        
        return {
            "acao_recomendada": acao,
            "status": status,
            "score": score,
            "proximos_passos": passos,
            "decisor_principal": decisor,
            "gatilho_usar": gatilho,
            "melhor_momento_contato": results.get("fases", {}).get("fase_6_triggers", {}).get("melhor_momento_contato", "N/D"),
            "canal_preferido": "LinkedIn"
        }
