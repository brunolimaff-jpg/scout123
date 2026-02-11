"""
services/tax_incentives_layer.py — FASE 1: INCENTIVOS FISCAIS (O OURO ESCONDIDO)
Bandeirante Digital v3.0 - Mapeamento de PRODEIC, PRODUZA-MS, SUDENE, Drawback, etc.
Cruza incentivos encontrados vs multas sofridas.
"""
import logging
import re
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class TaxIncentivesLayer:
    """
    Fase 1 do Bandeirante Digital: Caca aos Incentivos Fiscais.
    Mapeia incentivos estaduais, federais, creditos presumidos e sancoes.
    """

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def mapeamento_completo(self, empresa: str, cnpj: str = "", uf: str = "") -> Dict:
        """Pipeline completo de incentivos fiscais."""
        logger.info(f"[INCENTIVOS] Iniciando mapeamento fiscal: {empresa} ({uf})")

        results = {}

        try:
            estaduais = await self._incentivos_estaduais(empresa, cnpj, uf)
            results["incentivos_estaduais"] = estaduais
        except Exception as e:
            logger.warning(f"[INCENTIVOS] Erro estaduais: {e}")
            results["incentivos_estaduais"] = {}

        try:
            federais = await self._incentivos_federais(empresa, cnpj)
            results["incentivos_federais"] = federais
        except Exception as e:
            logger.warning(f"[INCENTIVOS] Erro federais: {e}")
            results["incentivos_federais"] = {}

        try:
            sancoes = await self._sancoes_multas(empresa, cnpj, uf)
            results["sancoes_multas"] = sancoes
        except Exception as e:
            logger.warning(f"[INCENTIVOS] Erro sancoes: {e}")
            results["sancoes_multas"] = {}

        try:
            creditos = await self._creditos_presumidos(empresa, cnpj)
            results["creditos_presumidos"] = creditos
        except Exception as e:
            logger.warning(f"[INCENTIVOS] Erro creditos: {e}")
            results["creditos_presumidos"] = {}

        # Analise consolidada
        results["analise_fiscal"] = self._analise_consolidada(results)
        return results

    async def _incentivos_estaduais(self, empresa: str, cnpj: str, uf: str) -> Dict:
        prompt = f"""ATUE COMO: Consultor Tributario Especializado em Agronegocio.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'}) - UF: {uf if uf else 'MT/MS/GO'}

BUSQUE INCENTIVOS ESTADUAIS:

MATO GROSSO (se aplicavel):
- PRODEIC (Programa de Desenvolvimento Industrial): site:al.mt.gov.br "PRODEIC" "{empresa}"
- Termos de Acordo SEFAZ: site:sefaz.mt.gov.br "Termo de Acordo" "{empresa}"
- Diario Oficial (IOMAT): site:iomat.mt.gov.br "{empresa}" "Resolucao"
- MT-COMPRE QUEM FAZ: programa de estimulo local
- PROALMAT (Algodao/Milho)

MATO GROSSO DO SUL (se aplicavel):
- PRODUZA-MS: site:ms.gov.br "PRODUZA-MS" "{empresa}"
- Licencas IMASUL: site:imasul.ms.gov.br "{empresa}"
- Credito Presumido ICMS

GOIAS (se aplicavel):
- PRODUZIR: site:sefaz.go.gov.br "PRODUZIR" "{empresa}"
- FOMENTAR

BAHIA / MATOPIBA (se aplicavel):
- DESENVOLVE BA
- Incentivos SUDENE

RETORNE JSON:
{{
    "incentivos_encontrados": [
        {{
            "nome": "PRODEIC",
            "tipo": "Estadual",
            "uf": "MT",
            "data_concessao": "2022-01-15",
            "vigencia": "2022-2032",
            "documento_prova": "Resolucao IOMAT 123/2022",
            "beneficio_estimado": "Reducao de 85% ICMS em operacoes industriais",
            "exigencias": "Motor fiscal robusto, EFD ICMS correta, compliance total"
        }}
    ],
    "total_incentivos": 0,
    "valor_beneficio_anual_estimado": "R$ 0",
    "risco_perda": "ALTO/MEDIO/BAIXO (se compliance incorreto)",
    "oportunidade_senior": "Motor fiscal automatizado garante zero risco de glosa"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[INCENTIVOS ESTADUAIS] Erro: {e}")
            return {}

    async def _incentivos_federais(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Consultor Tributario Federal.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

BUSQUE INCENTIVOS FEDERAIS:
1. SUDENE/SUDAM: site:gov.br "SUDENE" OR "SUDAM" AND "{empresa}"
   - Reducao de 75% do IRPJ para projetos aprovados
   
2. Lei de Informatica: "{empresa}" "Lei de Informatica"
   - Se for tech/automacao agricola

3. Drawback: "Drawback" AND "{empresa}"
   - Exportacao com diferimento de impostos
   - Drawback Suspensao ou Isencao

4. PADIS/PADIQ: Programas de P&D
   - "PADIS" OR "PADIQ" AND "{empresa}"

5. BNDES / Financiamentos Subsidiados:
   - Tomou emprestimo BNDES? (Software pode ser vinculado ao termo)
   - Linhas de credito ABC, Moderfrota, Inovagro

6. REIDI (Regime Especial de Incentivos para Infraestrutura):
   - Se tem usina, cogeracao, energia

RETORNE JSON:
{{
    "incentivos_federais": [
        {{
            "nome": "Drawback Suspensao",
            "tipo": "Federal",
            "beneficio": "Suspensao de II, IPI, PIS/COFINS na importacao de insumos para exportacao",
            "documento": "",
            "exigencias_sistema": "Controle rigoroso de entradas/saidas, DRE por operacao"
        }}
    ],
    "financiamentos_bndes": [
        {{
            "linha": "Inovagro",
            "valor": "R$ 0",
            "data": "",
            "vinculacao_software": "Possivel vincular investimento em ERP ao projeto"
        }}
    ],
    "total_federal": 0,
    "potencial_economia_anual": "R$ 0"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[INCENTIVOS FEDERAIS] Erro: {e}")
            return {}

    async def _sancoes_multas(self, empresa: str, cnpj: str, uf: str) -> Dict:
        prompt = f"""ATUE COMO: Auditor Fiscal.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

BUSQUE SANCOES E MULTAS:
1. Auto de Infracao SEFAZ: site:sefaz.mt.gov.br "Auto de Infracao" "{empresa}"
2. Glosa de ICMS: "Glosa de ICMS" AND "{empresa}"
3. Processo Administrativo CARF: site:carf.fazenda.gov.br "{empresa}"
4. Multas ambientais (IBAMA/SEMA)
5. Autos de infracao trabalhista (MPT)

PARA CADA MULTA/SANCAO, IDENTIFIQUE:
- Motivo (EFD incorreta? Glosa de credito? Falta de rastreabilidade?)
- Valor da multa
- Se foi paga ou esta em disputa
- Relacao com falta de sistema (oportunidade de venda)

RETORNE JSON:
{{
    "multas_fiscais": [
        {{
            "tipo": "Auto de Infracao ICMS",
            "orgao": "SEFAZ-MT",
            "valor": "R$ 0",
            "motivo": "EFD com inconsistencias",
            "data": "",
            "status": "Em disputa / Pago / Ativo",
            "relacao_sistema": "Sistema ERP inadequado ou mal parametrizado"
        }}
    ],
    "multas_ambientais": [],
    "multas_trabalhistas": [],
    "total_multas_valor": "R$ 0",
    "total_multas_quantidade": 0,
    "padrao_infracoes": "Descricao do padrao identificado",
    "argumento_venda": "Se encontrou multas por EFD/ICMS: Motor fiscal Senior elimina 100% do risco"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[SANCOES] Erro: {e}")
            return {}

    async def _creditos_presumidos(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Especialista em Creditos Tributarios.
ALVO: {empresa}

BUSQUE:
1. ICMS Diferido: "ICMS Diferido" AND "{empresa}" (Saida interestadual = rastreabilidade critica)
2. Credito PIS/COFINS: "Credito de Imposto" AND "PIS/COFINS" AND "{empresa}"
3. Substituicao Tributaria: "Substituicao Tributaria" AND "{empresa}"
4. Creditos de Carbono / CBIOs: "{empresa}" AND "CBIO" OR "credito carbono"

RETORNE JSON:
{{
    "creditos_identificados": [
        {{
            "tipo": "ICMS Diferido",
            "descricao": "",
            "requisito_sistema": "Rastreabilidade de saida interestadual"
        }}
    ],
    "cbios_renovabio": {{
        "participa": false,
        "volume_cbios": 0,
        "oportunidade": ""
    }},
    "creditos_pis_cofins_recuperaveis": "R$ 0"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[CREDITOS] Erro: {e}")
            return {}

    def _analise_consolidada(self, results: Dict) -> Dict:
        incentivos = results.get("incentivos_estaduais", {}).get("incentivos_encontrados", [])
        multas = results.get("sancoes_multas", {}).get("multas_fiscais", [])

        total_incentivos = len(incentivos)
        total_multas = len(multas)

        if total_multas > 0 and total_incentivos > 0:
            argumento = (
                f"Empresa possui {total_incentivos} incentivo(s) fiscal(is) ativo(s), "
                f"mas ja sofreu {total_multas} multa(s). "
                "Risco de PERDA de incentivos por non-compliance. "
                "Motor fiscal Senior = protecao total dos beneficios."
            )
        elif total_incentivos > 0:
            argumento = (
                f"Empresa possui {total_incentivos} incentivo(s) fiscal(is). "
                "Qualquer erro de EFD pode gerar glosa milionaria. "
                "Motor fiscal Senior garante zero risco."
            )
        else:
            argumento = "Nenhum incentivo mapeado. Verificar elegibilidade para novos beneficios."

        return {
            "total_incentivos": total_incentivos,
            "total_multas": total_multas,
            "argumento_principal": argumento,
            "urgencia": "CRITICA" if total_multas > 0 else ("ALTA" if total_incentivos > 0 else "MEDIA")
        }

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
