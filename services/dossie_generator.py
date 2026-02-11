"""
services/dossie_generator.py — GERADOR DE DOSSIÊ COMPLETO
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class DossieGenerator:
    """Gerador de dossiês Bandeirante Digital."""
    
    def gerar_dossie_completo(self, results: Dict) -> str:
        """Gera dossiê markdown completo."""
        sections = []
        
        sections.append(self._gerar_header(results))
        sections.append(self._gerar_executive_summary(results))
        sections.append(self._gerar_matriz_priorizacao(results))
        sections.append(self._gerar_recomendacoes(results))
        sections.append(self._gerar_todas_fases(results))
        sections.append(self._gerar_footer(results))
        
        return "\n\n".join(sections)
    
    def _gerar_header(self, results: Dict) -> str:
        metadata = results.get("metadata", {})
        empresa = metadata.get("empresa", "N/D")
        cnpj = metadata.get("cnpj", "N/D")
        
        return f"""# 🎯 DOSSIÊ DE INTELIGÊNCIA COMERCIAL
## BANDEIRANTE DIGITAL - MODO DEUS

**📋 EMPRESA:** {empresa}  
**🔢 CNPJ:** {cnpj}  
**📅 DATA:** {datetime.now().strftime("%d/%m/%Y %H:%M")}  
**⚡ VERSÃO:** 3.0 - MODO DEUS COMPLETO

---"""
    
    def _gerar_executive_summary(self, results: Dict) -> str:
        matriz = results.get("matriz_priorizacao", {})
        score = matriz.get("score_final", 0)
        status = matriz.get("status", "N/D")
        classificacao = matriz.get("classificacao", "N/D")
        
        rec = results.get("recomendacoes", {})
        acao = rec.get("acao_recomendada", "N/D")
        
        return f"""## 📊 EXECUTIVE SUMMARY

**🎯 SCORE FINAL:** {score}/100  
**🏆 CLASSIFICAÇÃO:** {classificacao}  
**📌 STATUS:** {status}  
**⚡ AÇÃO RECOMENDADA:** {acao}

---"""
    
    def _gerar_matriz_priorizacao(self, results: Dict) -> str:
        matriz = results.get("matriz_priorizacao", {})
        
        return f"""## 🎯 MATRIZ DE PRIORIZAÇÃO

### Indicadores Chave

- **Área Total:** {matriz.get('area_total_ha', 0):,.0f} hectares
- **Incentivos Fiscais:** {matriz.get('total_incentivos', 0)}
- **Score Final:** {matriz.get('score_final', 0)}/100
- **Status:** {matriz.get('status', 'N/D')}

---"""
    
    def _gerar_recomendacoes(self, results: Dict) -> str:
        rec = results.get("recomendacoes", {})
        
        content = f"""## 🚀 RECOMENDAÇÕES DE AÇÃO

**STATUS:** {rec.get('status', 'N/D')}  
**AÇÃO:** {rec.get('acao_recomendada', 'N/D')}  
**SCORE:** {rec.get('score', 0)}/100

### Próximos Passos

"""
        
        for passo in rec.get("proximos_passos", []):
            content += f"{passo}\n"
        
        content += f"""
### Estratégia de Abordagem

- **Decisor Principal:** {rec.get('decisor_principal', 'N/D')}
- **Gatilho a Usar:** {rec.get('gatilho_usar', 'N/D')}
- **Canal Preferido:** {rec.get('canal_preferido', 'N/D')}
- **Melhor Momento:** {rec.get('melhor_momento_contato', 'N/D')}

---"""
        
        return content
    
    def _gerar_todas_fases(self, results: Dict) -> str:
        """Gera resumo de todas as fases."""
        content = "## 📋 DETALHAMENTO DAS FASES\n\n"
        
        fases = results.get("fases", {})
        
        # Fase -1: Reputation
        reputation = fases.get("fase_-1_reputation", {})
        content += f"""### 🔍 FASE -1: SHADOW REPUTATION

**Flag de Risco:** {reputation.get('flag_risco', 'N/D')}

---

"""
        
        # Fase 1: Incentivos
        incentivos = fases.get("fase_1_incentivos", {})
        estaduais = incentivos.get("incentivos_estaduais", {})
        multas = incentivos.get("sancoes_multas", {})
        
        content += f"""### 💰 FASE 1: INCENTIVOS FISCAIS

- **Total de Incentivos:** {estaduais.get('total_incentivos', 0)}
- **Multas Fiscais:** {multas.get('total_multas_quantidade', 0)}

---

"""
        
        # Fase 2: Territorial
        territorial = fases.get("fase_2_territorial", {})
        fundiario = territorial.get("dados_fundiarios", {})
        
        content += f"""### 🗺️ FASE 2: INTELIGÊNCIA TERRITORIAL

- **Área Total:** {fundiario.get('area_total_ha', 0):,.0f} hectares
- **Total de Imóveis:** {fundiario.get('total_imoveis', 0)}
- **Estados de Presença:** {', '.join(fundiario.get('estados_presenca', ['N/D']))}

---

"""
        
        # Fase 3: Logística
        logistica = fases.get("fase_3_logistica", {})
        arm = logistica.get("armazenagem", {})
        
        content += f"""### 🚛 FASE 3: LOGÍSTICA & SUPPLY CHAIN

- **Capacidade de Armazenagem:** {arm.get('capacidade_total_toneladas', 0):,.0f} toneladas
- **Unidades:** {arm.get('total_unidades', 0)}

---

"""
        
        # Fase 6: Triggers
        triggers = fases.get("fase_6_triggers", {})
        
        content += f"""### ⏰ FASE 6: TRIGGER EVENTS

**Urgência Geral:** {triggers.get('urgencia_geral', 'N/D')}  
**Melhor Momento para Contato:** {triggers.get('melhor_momento_contato', 'N/D')}

**Triggers Identificados:** {triggers.get('total_triggers', 0)}

---

"""
        
        # Fase 7: Psicologia
        psicologia = fases.get("fase_7_psicologia", {})
        
        content += f"""### 🧠 FASE 7: PSICOLOGIA & GATILHOS

**Gatilho Psicológico:** {psicologia.get('gatilho_psicologico', 'N/D')}  
**Canal Preferido:** {psicologia.get('canal_preferido', 'N/D')}

**Storytelling de Abertura:**

