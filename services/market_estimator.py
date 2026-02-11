"""
services/market_estimator.py
Calculadora de Score SAS (Senior Attractiveness Score)
Atualizada para tolerar dados parciais.
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SASTier(Enum):
    IRON = "FERRO 🔩"
    BRONZE = "BRONZE 🥉"
    SILVER = "PRATA 🥈"
    GOLD = "OURO 🥇"
    PLATINUM = "PLATINA 💎"

@dataclass
class SASResult:
    score: int
    tier: SASTier
    recomendacao_comercial: str
    detalhes_pontuacao: Dict[str, int]

class MarketEstimator:
    def __init__(self):
        logger.info("[MarketEstimator] Inicializado")

    def calcular_sas(self, dados: Dict[str, Any]) -> SASResult:
        """
        Calcula o Score SAS (0-1000) baseado em 4 pilares:
        1. Porte (Hectares/Faturamento) - Peso 40%
        2. Tecnologia (Stack) - Peso 30%
        3. Complexidade (Industrial/Funcionários) - Peso 20%
        4. Momento (Investimentos/Notícias) - Peso 10%
        """
        score = 0
        detalhes = {}
        
        # 1. PORTE (Max 400 pts)
        try:
            ha = float(dados.get("hectares_total", 0) or 0)
            score_porte = 0
            
            if ha > 100000: score_porte = 400
            elif ha > 50000: score_porte = 300
            elif ha > 20000: score_porte = 200
            elif ha > 5000: score_porte = 100
            else: score_porte = 50
            
            score += score_porte
            detalhes["porte"] = score_porte
        except:
            detalhes["porte"] = 0

        # 2. TECNOLOGIA (Max 300 pts)
        # Pontuamos ALTO se o ERP for ruim (Oportunidade) ou se já for Senior (Base)
        try:
            tech = dados.get("tech_stack", {})
            erp = str(tech.get("erp_atual", "")).lower()
            score_tech = 0
            
            if "não identificado" in erp or "excel" in erp or not erp:
                score_tech = 300 # Oportunidade crítica (Greenfield)
            elif "totvs" in erp or "protheus" in erp or "rm" in erp:
                score_tech = 250 # Oportunidade de troca (Competidor)
            elif "senior" in erp:
                score_tech = 200 # Base instalada (Cross-sell)
            elif "sap" in erp or "oracle" in erp:
                score_tech = 100 # Difícil penetração (Tier 1)
            else:
                score_tech = 150
                
            score += score_tech
            detalhes["tech"] = score_tech
        except:
            detalhes["tech"] = 0

        # 3. COMPLEXIDADE (Max 200 pts)
        # Indústria, Algodão e Funcionários aumentam complexidade = Mais aderência
        try:
            score_comp = 0
            # Se tiver 'detalhes_industriais' no dicionário original (passado via wrapper)
            # Mas aqui recebemos 'dados_sas' simplificado. Vamos assumir base simples.
            # Se faturamento > 500M, assume complexidade alta.
            fat_str = str(dados.get("faturamento_estimado", ""))
            
            if "bilhão" in fat_str.lower() or "bi" in fat_str.lower():
                score_comp = 200
            elif "milhões" in fat_str.lower():
                score_comp = 100
            else:
                score_comp = 50
                
            score += score_comp
            detalhes["complexidade"] = score_comp
        except:
            detalhes["complexidade"] = 0

        # 4. TIER FINAL
        if score >= 800: tier = SASTier.PLATINUM
        elif score >= 600: tier = SASTier.GOLD
        elif score >= 400: tier = SASTier.SILVER
        elif score >= 200: tier = SASTier.BRONZE
        else: tier = SASTier.IRON
        
        return SASResult(
            score=score,
            tier=tier,
            recomendacao_comercial=f"Score {score}: Cliente {tier.value} - Prioridade Alta",
            detalhes_pontuacao=detalhes
        )
