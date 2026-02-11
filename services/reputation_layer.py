"""
services/reputation_layer.py — FASE -1: INTELIGENCIA PREVIA (SHADOW REPUTATION)
Bandeirante Digital v3.0 - Checagem de Reputacao, Judicial, Financeira e Redes Sociais.

Fontes: JusBrasil, Reclame Aqui, Glassdoor, PGFN, MPT, IBAMA
"""
import logging
import re
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class ReputationLayer:
    """
    Fase -1 do Bandeirante Digital: Inteligencia Previa (Underground).
    Varre reputacao judicial, financeira, trabalhista e online ANTES de abordar.
    """

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def checagem_completa(self, empresa: str, cnpj: str = "") -> Dict:
        """
        Executa checagem de reputacao em 4 dimensoes:
        1. Historico Judicial & Moral
        2. Reputacao Online (Reclame Aqui, Glassdoor)
        3. Saude Financeira Shadow (Serasa, PGFN)
        4. Presenca Digital (Site, Redes Sociais)
        """
        logger.info(f"[REPUTACAO] Iniciando checagem shadow: {empresa}")

        results = {}
        try:
            judicial = await self._checagem_judicial(empresa, cnpj)
            results["judicial"] = judicial
        except Exception as e:
            logger.warning(f"[REPUTACAO] Erro judicial: {e}")
            results["judicial"] = {}

        try:
            online = await self._checagem_reputacao_online(empresa)
            results["reputacao_online"] = online
        except Exception as e:
            logger.warning(f"[REPUTACAO] Erro reputacao online: {e}")
            results["reputacao_online"] = {}

        try:
            financeira = await self._checagem_saude_financeira(empresa, cnpj)
            results["saude_financeira"] = financeira
        except Exception as e:
            logger.warning(f"[REPUTACAO] Erro saude financeira: {e}")
            results["saude_financeira"] = {}

        try:
            digital = await self._checagem_presenca_digital(empresa)
            results["presenca_digital"] = digital
        except Exception as e:
            logger.warning(f"[REPUTACAO] Erro presenca digital: {e}")
            results["presenca_digital"] = {}

        # Score consolidado
        results["flag_risco"] = self._calcular_flag_risco(results)
        logger.info(f"[REPUTACAO] Flag de risco: {results['flag_risco']}")
        return results

    async def _checagem_judicial(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Investigador Judicial Forense.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

BUSQUE INFORMACOES PUBLICAS SOBRE:

1. PROCESSOS JUDICIAIS:
   - Acoes civis publicas (site:jusbrasil.com.br "{empresa}" "Acao Civil")
   - Reclamacoes trabalhistas (site:jusbrasil.com.br "{empresa}" "Trabalhista")
   - Acoes ambientais (IBAMA, MPF)
   - Acoes de execucao fiscal

2. LISTA SUJA / TRABALHO ESCRAVO:
   - Verificar no Observatorio Brasil Trabalhista (obt.org.br)
   - "Trabalho Escravo" OR "Escravidao" AND "{empresa}"
   - Ministerio Publico do Trabalho (site:mpt.mp.br "{empresa}")

3. EMBARGOS AMBIENTAIS:
   - site:ibama.gov.br "{empresa}" "Embargo"
   - Multas IBAMA ativas
   - Auto de infracao ambiental

4. PROCESSOS NO CARF (Tributario):
   - site:carf.fazenda.gov.br "{empresa}"
   - Disputas com o fisco federal

RETORNE JSON ESTRITO:
{{
    "processos_civis": {{
        "quantidade_estimada": 0,
        "tipos_principais": ["Trabalhista", "Ambiental"],
        "valor_total_estimado": "R$ 0",
        "detalhes": "Resumo dos principais processos encontrados"
    }},
    "trabalhista": {{
        "reclamacoes_ativas": 0,
        "lista_suja": false,
        "acoes_mpt": [],
        "padrao_reclamacoes": "Descricao do padrao se houver"
    }},
    "ambiental": {{
        "embargos_ativos": false,
        "multas_ibama": [],
        "autos_infracao": 0,
        "valor_multas": "R$ 0"
    }},
    "tributario": {{
        "processos_carf": 0,
        "execucoes_fiscais": 0,
        "detalhes": ""
    }},
    "severidade_geral": "VERDE/AMARELO/VERMELHO"
}}

NAO INVENTE dados. Se nao encontrar, retorne campos vazios/zerados."""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[JUDICIAL] Erro: {e}")
            return {}

    async def _checagem_reputacao_online(self, empresa: str) -> Dict:
        prompt = f"""ATUE COMO: Analista de Reputacao Digital.
ALVO: {empresa}

BUSQUE EM:
1. Reclame Aqui (site:reclameaqui.com.br "{empresa}")
   - Score geral, quantidade de reclamacoes, taxa de resposta
   - Padrao de reclamacoes (atraso, qualidade, atendimento)

2. Glassdoor (site:glassdoor.com.br "{empresa}")
   - Nota geral, clima organizacional
   - O que funcionarios dizem sobre TI/sistemas

3. Google Maps / Reviews
   - Reviews de unidades locais
   
4. Redes Sociais:
   - Facebook: Tom de comunicacao, comentarios negativos
   - Instagram: Fotos de operacao (estrutura real vs marketing)
   - LinkedIn: Engajamento, vagas abertas
   - YouTube: Canal ativo? Conteudo educativo?

5. Vagas de Emprego (SINAL CRITICO):
   - Esta contratando "Gerente de TI"? = Mudanca de sistema iminente
   - Esta contratando "Analista de Sistemas"? = Sistema quebrado
   - Timing: Contratacao -> 2-3 meses -> Implementacao

RETORNE JSON:
{{
    "reclame_aqui": {{
        "score": 0,
        "total_reclamacoes": 0,
        "taxa_resposta": "0%",
        "padrao_reclamacoes": "",
        "link": ""
    }},
    "glassdoor": {{
        "nota": 0,
        "clima": "",
        "mencionam_ti": false,
        "detalhes_ti": ""
    }},
    "redes_sociais": {{
        "facebook_ativo": false,
        "instagram_ativo": false,
        "linkedin_ativo": false,
        "youtube_ativo": false,
        "tom_comunicacao": "",
        "sinais_expansao": []
    }},
    "vagas_abertas": {{
        "vagas_ti": [],
        "vagas_gerenciais": [],
        "sinal_mudanca_sistema": false,
        "detalhes": ""
    }},
    "osint_score": 0
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[REPUTACAO ONLINE] Erro: {e}")
            return {}

    async def _checagem_saude_financeira(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Auditor de Credito.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

BUSQUE:
1. PGFN - Lista de inadimplentes da Uniao (site:pgfn.fazenda.gov.br "{cnpj if cnpj else empresa}")
2. Protestos em cartorio ("Protesto" OR "Protestado" AND "{empresa}")
3. Operacoes de credito publicas (site:bcb.gov.br "{empresa}")
4. "Calote" AND "{empresa}" (forums de credores)
5. Alteracoes societarias recentes:
   - Aumentos de capital = Dinheiro fresco entrando
   - Reducao de capital = Empresa sangrando
   - Venda de subsidiaria = Enxugamento
   - Mudanca de endereco = Reducao de footprint

RETORNE JSON:
{{
    "pgfn_inadimplente": false,
    "protestos_ativos": 0,
    "valor_protestos": "R$ 0",
    "endividamento_publico": "",
    "alteracoes_societarias": {{
        "aumento_capital_recente": false,
        "reducao_capital": false,
        "venda_subsidiaria": false,
        "mudanca_endereco": false,
        "detalhes": ""
    }},
    "score_saude": "SOLIDA/FRAGIL/COLAPSO",
    "capacidade_investimento": "ALTA/MEDIA/BAIXA/NULA"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[SAUDE FINANCEIRA] Erro: {e}")
            return {}

    async def _checagem_presenca_digital(self, empresa: str) -> Dict:
        prompt = f"""ATUE COMO: Analista de Presenca Digital.
ALVO: {empresa}

VERIFIQUE:
1. Site da empresa:
   - Existe? Qual URL?
   - Ultima atualizacao (parece recente ou abandonado?)
   - HTTPS seguro ou HTTP inseguro?
   - Mobile responsive?

2. Stack Tecnologico do Site:
   - WordPress? React? HTML estatico?
   - WordPress outdated = Gestao tradicional
   - React/Modern = Investem em tech

3. Dominio (Whois):
   - Registrado em nome de quem?
   - Quando foi registrado?

4. SEO / Presenca Google:
   - Aparece bem no Google?
   - Google My Business atualizado?

RETORNE JSON:
{{
    "site": {{
        "url": "",
        "existe": true,
        "https_seguro": true,
        "aparencia": "Moderno/Basico/Outdated/Inexistente",
        "ultima_atualizacao_estimada": "",
        "mobile_responsive": true
    }},
    "stack_web": {{
        "tecnologia": "WordPress/React/HTML/Outro",
        "indicador_maturidade": "Alta/Media/Baixa"
    }},
    "google_presence": {{
        "google_my_business": false,
        "reviews_google": 0,
        "nota_google": 0
    }},
    "maturidade_digital_score": 0
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[PRESENCA DIGITAL] Erro: {e}")
            return {}

    def _calcular_flag_risco(self, results: Dict) -> str:
        """Calcula flag VERDE/AMARELO/VERMELHO baseado nos dados coletados."""
        red_flags = 0

        judicial = results.get("judicial", {})
        if judicial.get("trabalhista", {}).get("lista_suja"):
            red_flags += 3
        if judicial.get("ambiental", {}).get("embargos_ativos"):
            red_flags += 2
        if judicial.get("severidade_geral") == "VERMELHO":
            red_flags += 2

        financeira = results.get("saude_financeira", {})
        if financeira.get("pgfn_inadimplente"):
            red_flags += 3
        if financeira.get("score_saude") == "COLAPSO":
            red_flags += 3

        if red_flags >= 4:
            return "VERMELHO"
        elif red_flags >= 2:
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
