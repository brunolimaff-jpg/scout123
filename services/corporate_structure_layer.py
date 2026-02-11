"""
services/corporate_structure_layer.py — FASE 4: ESTRUTURA SOCIETARIA & LABIRINTO PATRIMONIAL
Bandeirante Digital v3.0 - Holdings, Laranjas, Sucessao, Conflitos Societarios.
"""
import logging
import re
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class CorporateStructureLayer:
    """
    Fase 4 do Bandeirante Digital: Desvendando o Codigo da Empresa.
    Mapeia holdings patrimoniais, laranjas, conflitos de sucessao.
    """

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def mapeamento_societario_completo(self, empresa: str, cnpj: str = "", socios: List[Dict] = None) -> Dict:
        """Pipeline de mapeamento societario total."""
        logger.info(f"[SOCIETARIO] Iniciando mapeamento: {empresa}")

        results = {}

        try:
            estrutura = await self._estrutura_societaria(empresa, cnpj)
            results["estrutura"] = estrutura
        except Exception as e:
            logger.warning(f"[SOCIETARIO] Erro estrutura: {e}")
            results["estrutura"] = {}

        try:
            holdings = await self._detectar_holdings(empresa, cnpj, socios or [])
            results["holdings"] = holdings
        except Exception as e:
            logger.warning(f"[SOCIETARIO] Erro holdings: {e}")
            results["holdings"] = {}

        try:
            red_flags = await self._detectar_red_flags(empresa, cnpj, socios or [])
            results["red_flags_societarias"] = red_flags
        except Exception as e:
            logger.warning(f"[SOCIETARIO] Erro red flags: {e}")
            results["red_flags_societarias"] = {}

        results["risco_societario"] = self._calcular_risco(results)
        return results

    async def _estrutura_societaria(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Investigador Societario / Due Diligence.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

MAPEIE A ESTRUTURA SOCIETARIA COMPLETA:

1. VIA CNPJ RAIZ (site:cnpj.com.br "{empresa}"):
   - Todos os CNPJs filiais/subsidiarias
   - Empresas em nome dos socios
   - Historico de alteracoes (quando mudou? O que?)

2. VIA JUNTA COMERCIAL:
   - Atas de Assembleia (quem entra/sai)
   - Aumentos de capital (quando? quanto?)
   - Mudancas de administracao

3. GRUPO ECONOMICO:
   - Quantas empresas no grupo?
   - Controladora / Holding principal
   - Subsidiarias operacionais

RETORNE JSON:
{{
    "cnpj_matriz": "{cnpj if cnpj else 'N/D'}",
    "razao_social": "{empresa}",
    "grupo_economico": {{
        "holding_controladora": "",
        "total_empresas_grupo": 0,
        "empresas_relacionadas": [
            {{
                "razao_social": "",
                "cnpj": "",
                "tipo": "Filial/Subsidiaria/Coligada/Holding",
                "atividade": "",
                "uf": ""
            }}
        ]
    }},
    "socios_principais": [
        {{
            "nome": "",
            "tipo": "PF/PJ",
            "qualificacao": "Socio-Administrador/Socio/Diretor",
            "participacao_estimada": "X%",
            "desde": "2020"
        }}
    ],
    "alteracoes_recentes": [
        {{
            "tipo": "Aumento de Capital/Entrada Socio/Saida Socio",
            "data": "",
            "detalhes": "",
            "implicacao": ""
        }}
    ],
    "capital_social_total_grupo": "R$ 0"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[ESTRUTURA] Erro: {e}")
            return {}

    async def _detectar_holdings(self, empresa: str, cnpj: str, socios: List[Dict]) -> Dict:
        nomes_socios = [s.get("nome", "") for s in socios[:5]] if socios else []
        nomes_str = ", ".join(nomes_socios) if nomes_socios else "N/D"

        prompt = f"""ATUE COMO: Especialista em Planejamento Patrimonial e Family Offices.
ALVO: {empresa}
SOCIOS CONHECIDOS: {nomes_str}

BUSQUE HOLDINGS PATRIMONIAIS:

1. Holdings em nome dos socios:
   - "[Nome Socio] Participacoes" OR "[Nome Socio] Holding" site:cnpj.com.br
   - Empresas com mesmo sobrenome em diferentes estados

2. Family Office:
   - Investimentos fora do agro (imobiliario, financeiro)
   - Participacoes em fundos
   - O dinheiro para TI pode sair do Family Office, nao da operacao

3. Planejamento Sucessorio:
   - Holdings familiares para separacao patrimonial
   - Usufruto vitalicio em nome de patriarcas
   - Doacao de cotas com clausula de inalienabilidade

RETORNE JSON:
{{
    "holdings_identificadas": [
        {{
            "razao_social": "",
            "cnpj": "",
            "tipo": "Holding Patrimonial/Holding Operacional/Family Office",
            "socios": [],
            "patrimonio_estimado": "R$ 0",
            "participacoes": []
        }}
    ],
    "patrimonio_total_estimado_grupo": "R$ 0",
    "capacidade_investimento_family_office": "R$ 0/ano",
    "planejamento_sucessorio": {{
        "em_andamento": false,
        "geracao_atual": "1a/2a/3a geracao",
        "risco_sucessao": "ALTO/MEDIO/BAIXO"
    }},
    "implicacao_vendas": "Se Family Office tem capacidade de R$X, investimento em ERP nao compromete EBITDA operacional"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[HOLDINGS] Erro: {e}")
            return {}

    async def _detectar_red_flags(self, empresa: str, cnpj: str, socios: List[Dict]) -> Dict:
        nomes_socios = [s.get("nome", "") for s in socios[:5]] if socios else []
        nomes_str = ", ".join(nomes_socios) if nomes_socios else "N/D"

        prompt = f"""ATUE COMO: Investigador de Fraude Corporativa.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})
SOCIOS: {nomes_str}

DETECTE RED FLAGS SOCIETARIAS:

1. CONFLITOS SOCIETARIOS:
   - "Acao de Divorcio" AND "[Socio]" site:jusbrasil.com.br
   - "Inventario" AND "[Socio]" (Morte = lista de bens publica)
   - Distratos revelam patrimonio real vs declarado

2. RED FLAGS ESTRUTURAIS:
   - Empresa aberta ha <2 anos com incentivo "antigo" (Relocation de outro CNPJ?)
   - Multiplas empresas com mesmo nome em estados diferentes (Tax arbitrage)
   - Socios com mesmo sobrenome mas empresas diferentes (Separacao patrimonial)
   - Sede em escritorio virtual, operacao no interior
   - Entrada subita de socio novo desconhecido (Estrutura de emprestimo?)
   - Capital social "redondo" demais (R$ 100k exato = fabricado)

3. AFILIACAO POLITICA:
   - site:tse.jus.br "[Socio]" (Financiou campanha? Ideologia?)
   - Pode bloquear ou facilitar venda baseado em conexoes politicas

RETORNE JSON:
{{
    "red_flags": [
        {{
            "tipo": "Conflito Sucessorio/Divorcio/Tax Arbitrage/Laranja/Politica",
            "severidade": "CRITICA/ALTA/MEDIA/BAIXA",
            "descricao": "",
            "implicacao_venda": ""
        }}
    ],
    "conflitos_societarios": {{
        "divorcios_ativos": false,
        "inventarios_abertos": false,
        "disputas_entre_socios": false,
        "detalhes": ""
    }},
    "afiliacao_politica": {{
        "financiou_campanha": false,
        "partidos": [],
        "risco_ideologico": "NENHUM/BAIXO/MEDIO/ALTO"
    }},
    "risco_geral": "VERDE/AMARELO/VERMELHO"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[RED FLAGS] Erro: {e}")
            return {}

    def _calcular_risco(self, results: Dict) -> str:
        red_flags = results.get("red_flags_societarias", {}).get("red_flags", [])
        criticas = sum(1 for r in red_flags if r.get("severidade") == "CRITICA")
        altas = sum(1 for r in red_flags if r.get("severidade") == "ALTA")

        if criticas > 0:
            return "VERMELHO"
        elif altas >= 2:
            return "AMARELO"
        return "VERDE"

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
