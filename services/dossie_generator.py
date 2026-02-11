"""
services/dossie_generator_v3.py — GERADOR DE DOSSIÊ V3.0
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class DossieGeneratorV3:
    """Gerador de dossiês Bandeirante Digital v3.0."""
    
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
        return f"""# 🎯 DOSSIÊ DE INTELIGÊNCIA COMERCIAL
## BANDEIRANTE DIGITAL v3.0 - MODO DEUS

**📋 EMPRESA:** {metadata.get("empresa", "N/D")}  
**🔢 CNPJ:** {metadata.get("cnpj", "N/D")}  
**📅 DATA:** {datetime.now().strftime("%d/%m/%Y")}  
**⚡ VERSÃO:** 3.0 - MODO DEUS COMPLETO

---"""
    
    def _gerar_executive_summary(self, results: Dict) -> str:
        matriz = results.get("matriz_priorizacao", {})
        return f"""## 📊 EXECUTIVE SUMMARY

**🎯 SCORE FINAL:** {matriz.get('score_final', 0)}/100  
**🏆 CLASSIFICAÇÃO:** {matriz.get('classificacao', 'N/D')}  
**📌 STATUS:** {matriz.get('status', 'N/D')}

---"""
    
    def _gerar_matriz_priorizacao(self, results: Dict) -> str:
        matriz = results.get("matriz_priorizacao", {})
        return f"""## 🎯 MATRIZ DE PRIORIZAÇÃO

- **Área Total:** {matriz.get('area_total_ha', 0):,.0f} hectares
- **Score:** {matriz.get('score_final', 0)}/100
- **Status:** {matriz.get('status', 'N/D')}

---"""
    
    def _gerar_recomendacoes(self, results: Dict) -> str:
        rec = results.get("recomendacoes", {})
        
        content = f"""## 🚀 RECOMENDAÇÕES DE AÇÃO

**AÇÃO:** {rec.get('acao_recomendada', 'N/D')}

### Próximos Passos

"""
        
        for passo in rec.get("proximos_passos", []):
            content += f"{passo}\n"
        
        content += "\n---"
        return content
    
    def _gerar_todas_fases(self, results: Dict) -> str:
        """Gera resumo de todas as fases."""
        content = "## 📋 DETALHAMENTO DAS FASES\n\n"
        
        fases = results.get("fases", {})
        
        for fase_key, fase_data in fases.items():
            content += f"### {fase_key.replace('_', ' ').upper()}\n"
            content += f"Dados coletados: {len(fase_data)} campos\n\n"
        
        return content
    
    def _gerar_footer(self, results: Dict) -> str:
        metadata = results.get("metadata", {})
        duracao = metadata.get("duracao_segundos", 0)
        
        return f"""## 📝 METADADOS

**Duração:** {duracao:.1f}s  
**Timestamp:** {metadata.get('timestamp_fim', 'N/D')}

---

**🎯 Bandeirante Digital v3.0**  
© 2026 - Bruno Lima / Senior Sistemas"""

