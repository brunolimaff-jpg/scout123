"""
services/dossie_generator.py — GERADOR DE DOSSIÊ
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class DossieGenerator:
    """Gerador de dossiês."""
    
    def gerar_dossie_completo(self, results: Dict) -> str:
        """Gera dossiê markdown."""
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

**📋 EMPRESA:** {empresa}  
**🔢 CNPJ:** {cnpj}  
**📅 DATA:** {datetime.now().strftime("%d/%m/%Y %H:%M")}

---"""
    
    def _gerar_executive_summary(self, results: Dict) -> str:
        matriz = results.get("matriz_priorizacao", {})
        
        return f"""## 📊 EXECUTIVE SUMMARY

**🎯 SCORE:** {matriz.get('score_final', 0)}/100  
**📌 STATUS:** {matriz.get('status', 'N/D')}  
**🏆 CLASSIFICAÇÃO:** {matriz.get('classificacao', 'N/D')}

---"""
    
    def _gerar_matriz_priorizacao(self, results: Dict) -> str:
        matriz = results.get("matriz_priorizacao", {})
        
        return f"""## 🎯 MATRIZ DE PRIORIZAÇÃO

- **Área:** {matriz.get('area_total_ha', 0):,.0f} ha
- **Score:** {matriz.get('score_final', 0)}/100
- **Status:** {matriz.get('status', 'N/D')}

---"""
    
    def _gerar_recomendacoes(self, results: Dict) -> str:
        rec = results.get("recomendacoes", {})
        
        content = f"""## 🚀 RECOMENDAÇÕES

**AÇÃO:** {rec.get('acao_recomendada', 'N/D')}

### Próximos Passos

"""
        
        for passo in rec.get("proximos_passos", []):
            content += f"{passo}\n"
        
        content += f"""
### Estratégia

- **Decisor:** {rec.get('decisor_principal', 'N/D')}
- **Gatilho:** {rec.get('gatilho_usar', 'N/D')}
- **Canal:** {rec.get('canal_preferido', 'N/D')}

---"""
        
        return content
    
    def _gerar_todas_fases(self, results: Dict) -> str:
        content = "## 📋 FASES\n\n"
        
        fases = results.get("fases", {})
        
        # Reputation
        reputation = fases.get("fase_-1_reputation", {})
        content += f"""### 🔍 FASE -1: REPUTATION

**Flag:** {reputation.get('flag_risco', 'N/D')}

---

"""
        
        # Incentivos
        incentivos = fases.get("fase_1_incentivos", {})
        content += f"""### 💰 FASE 1: INCENTIVOS

**Total:** {incentivos.get('incentivos_estaduais', {}).get('total_incentivos', 0)}

---

"""
        
        # Territorial
        territorial = fases.get("fase_2_territorial", {})
        fundiario = territorial.get("dados_fundiarios", {})
        content += f"""### 🗺️ FASE 2: TERRITORIAL

**Área:** {fundiario.get('area_total_ha', 0):,.0f} ha

---

"""
        
        # Triggers
        triggers = fases.get("fase_6_triggers", {})
        content += f"""### ⏰ FASE 6: TRIGGERS

**Urgência:** {triggers.get('urgencia_geral', 'N/D')}

---

"""
        
        # Psicologia
        psicologia = fases.get("fase_7_psicologia", {})
        content += f"""### 🧠 FASE 7: PSICOLOGIA

**Gatilho:** {psicologia.get('gatilho_psicologico', 'N/D')}

**Storytelling:**

