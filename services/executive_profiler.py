"""
services/executive_profiler.py — FASE 5/7: PROFILING DE EXECUTIVOS & DECISION MAKERS
Bandeirante Digital v3.0 - Mapa Psicologico, Tech-Affinity, Vulnerabilidades.
"""
import logging
import re
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class ExecutiveProfiler:
    """
    Fases 5/7 do Bandeirante Digital: Profiling do Tomador de Decisao.
    Mapeia hierarquia real, background, tech-affinity, vulnerabilidades.
    """

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def profiling_completo(self, empresa: str) -> Dict:
        """Pipeline de profiling de decisores."""
        logger.info(f"[PROFILING] Iniciando profiling de executivos: {empresa}")

        results = {}

        try:
            hierarquia = await self._mapear_hierarquia(empresa)
            results["hierarquia"] = hierarquia
        except Exception as e:
            logger.warning(f"[PROFILING] Erro hierarquia: {e}")
            results["hierarquia"] = {}

        try:
            perfis = await self._profiling_decisores(empresa, hierarquia)
            results["perfis_decisores"] = perfis
        except Exception as e:
            logger.warning(f"[PROFILING] Erro perfis: {e}")
            results["perfis_decisores"] = {}

        results["matriz_receptividade"] = self._montar_matriz(results)
        return results

    async def _mapear_hierarquia(self, empresa: str) -> Dict:
        prompt = f"""ATUE COMO: Headhunter Executivo Especializado em Agronegocio.
ALVO: {empresa}

MAPEIE A HIERARQUIA REAL DA EMPRESA (nao o que esta no site):

1. VIA LINKEDIN:
   - Procure: CEO, CFO, COO, CIO, Diretor TI, Diretor Agro, Diretor Comercial
   - Quem tem mais conexoes? = Quem tem poder real
   - Quem posta mais? = Mais engajado/aberto a inovacao

2. RED FLAGS DE PODER:
   - CEO eh socio fundador? = Decisao rapida (controla tudo)
   - CEO eh profissional contratado? = Precisa aprovacao de board = Mais lento
   - Tem CIO/Diretor de TI? = Tech-savvy = Ve valor tecnico
   - Nao tem ninguem de TI? = Decisoes por "custo", nao por "solucao"

3. VAGAS ABERTAS (SINAL CRITICO):
   - Contratando "Gerente de TI" = Mudanca de sistema iminente
   - Contratando "Analista de Sistemas" = Sistema atual quebrado
   - Contratando "Desenvolvedor" = Construindo interno

RETORNE JSON:
{{
    "executivos_identificados": [
        {{
            "nome": "",
            "cargo": "CEO/CFO/CIO/Diretor TI/Gerente Fazenda",
            "linkedin": "",
            "tipo_poder": "TOTAL/CONSULTIVO/OPERACIONAL",
            "eh_socio_fundador": false,
            "tempo_empresa": "X anos",
            "formacao": "",
            "sinais_engajamento": "Posta sobre tech/AI/gestao"
        }}
    ],
    "tem_area_ti": true,
    "tipo_decisao": "RAPIDA (fundador) / LENTA (board) / COLEGIADA",
    "vagas_ti_abertas": [],
    "sinal_mudanca_sistema": false
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[HIERARQUIA] Erro: {e}")
            return {}

    async def _profiling_decisores(self, empresa: str, hierarquia: Dict) -> Dict:
        executivos = hierarquia.get("executivos_identificados", [])
        nomes = [e.get("nome", "") for e in executivos[:3]]
        nomes_str = ", ".join(nomes) if nomes else "N/D"

        prompt = f"""ATUE COMO: Psicologo Organizacional + Investigador OSINT.
ALVO: {empresa}
EXECUTIVOS: {nomes_str}

PARA CADA EXECUTIVO, FACA PROFILING:

1. TECH-AFFINITY (site:linkedin.com "[Nome]"):
   - Segue empresas de tech/software? = Early adopter
   - Compartilha artigos de IA/automacao? = Ja esta pronto mentalmente
   - Trabalhou em empresa com ERP moderno? = Sabe do problema
   - Historico: Startup tech ou sempre agro analogico?
   - Certificacoes: MBA? Cursos de TI?
   
2. RISK-AVERSION:
   - Empresa anterior faliu? = Trauma = Precisa provar ROI
   - 15+ anos em agro tradicional? = Confortavel com "do jeito que eh"
   - < 1 ano na empresa? = Tentando provar competencia = Agressivo

3. VULNERABILIDADE PROFISSIONAL:
   - Quantas vezes trocou de emprego? Instavel = Aceita rapido
   - Aumentou cargo recentemente? Sim = Pressao de performance
   - Novo na empresa? Quer fazer marca = Mais aberto

4. GATILHO PSICOLOGICO ESPECIFICO:
   Se "tech-savvy + novo cargo": Pitch = "Case de sucesso para sua carreira"
   Se "tradicional + 15 anos": Pitch = "Seu sistema aguenta crescimento?"
   Se "sob pressao": Pitch = "ROI em 6 meses documentado"

RETORNE JSON:
{{
    "perfis": [
        {{
            "nome": "",
            "cargo": "",
            "tech_affinity_score": 0,
            "risk_aversion_score": 0,
            "poder_decisao": "TOTAL/CONSULTIVO/NENHUM",
            "vulnerabilidade": "Pressao performance/Confortavel/Fragil/Nenhuma",
            "tempo_empresa_anos": 0,
            "formacao_resumo": "",
            "gatilho_recomendado": "Inovacao + Case Success / ROI + Reducao Custo / Compliance",
            "score_receptividade": 0,
            "melhor_abordagem": ""
        }}
    ],
    "decisor_principal_recomendado": "",
    "tipo_pitch_recomendado": "",
    "canal_preferido": "LinkedIn/WhatsApp/Email/Call"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.2)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[PROFILING DECISORES] Erro: {e}")
            return {}

    def _montar_matriz(self, results: Dict) -> List[Dict]:
        """Monta Matriz de Receptividade por Executivo."""
        perfis = results.get("perfis_decisores", {}).get("perfis", [])
        matriz = []
        for p in perfis:
            matriz.append({
                "executivo": p.get("nome", "N/D"),
                "cargo": p.get("cargo", "N/D"),
                "poder": p.get("poder_decisao", "N/D"),
                "tech_affinity": f"{p.get('tech_affinity_score', 0)}/10",
                "risco_pessoal": p.get("vulnerabilidade", "N/D"),
                "score": p.get("score_receptividade", 0),
                "gatilho": p.get("gatilho_recomendado", "N/D")
            })
        return sorted(matriz, key=lambda x: x.get("score", 0), reverse=True)

    def _parse_json(self, response: str) -> Dict:
        if not response:
            return {}
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {}
