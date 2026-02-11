"""
services/logistics_layer.py — FASE 3/5: LOGISTICA & SUPPLY CHAIN COMPLETO
Bandeirante Digital v3.0 - ANTT/RNTRC, Frota, CTe/MDFe, CONAB, Comexstat.
"""
import logging
import re
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class LogisticsLayer:
    """
    Fases 3/5 do Bandeirante Digital: Infraestrutura de Supply Chain.
    CONAB (armazenagem), ANTT (frota), Comexstat (exportacao).
    """

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def mapeamento_logistico_completo(self, empresa: str, cnpj: str = "") -> Dict:
        """Pipeline completo de logistica e supply chain."""
        logger.info(f"[LOGISTICA] Iniciando mapeamento: {empresa}")

        results = {}

        try:
            armazenagem = await self._armazenagem_conab(empresa)
            results["armazenagem"] = armazenagem
        except Exception as e:
            logger.warning(f"[LOGISTICA] Erro armazenagem: {e}")
            results["armazenagem"] = {}

        try:
            frota = await self._frota_rntrc(empresa)
            results["frota_logistica"] = frota
        except Exception as e:
            logger.warning(f"[LOGISTICA] Erro frota: {e}")
            results["frota_logistica"] = {}

        try:
            exportacao = await self._exportacao_comexstat(empresa, cnpj)
            results["exportacao"] = exportacao
        except Exception as e:
            logger.warning(f"[LOGISTICA] Erro exportacao: {e}")
            results["exportacao"] = {}

        results["cadeia_valor_resumo"] = self._resumo_cadeia(results)
        return results

    async def _armazenagem_conab(self, empresa: str) -> Dict:
        prompt = f"""ATUE COMO: Auditor de Armazenagem Agricola (CONAB).
ALVO: {empresa}

BUSQUE DADOS PUBLICOS DE ARMAZENAGEM:

1. CONAB - Unidades Armazenadoras:
   - site:conab.gov.br "Unidade Armazenadora" "{empresa}"
   - Capacidade estatica (toneladas exatas)
   - Localizacao de cada unidade
   - Tipo (silo metalico, silo bolsa, galpao, patio)
   - Proprietario vs Operador

2. SIARH (Sistema de Informacoes de Armazenagem):
   - Relatorios de estoque quinzenal/mensal
   - Se empresa aparece = obrigacao de prestacao de contas

3. ANVISA (se manipulam alimentos/racoes):
   - "Licenca de Funcionamento" AND "Armazem" AND "{empresa}"

CAPACIDADE TOTAL INDICA:
- < 50k ton = Operacao pequena
- 50k-200k ton = Operacao media, precisa de WMS
- > 200k ton = Operacao grande, WMS CRITICO

RETORNE JSON:
{{
    "unidades_armazenagem": [
        {{
            "nome": "Armazem Sapezal",
            "municipio": "Sapezal-MT",
            "tipo": "Silo Metalico",
            "capacidade_toneladas": 50000,
            "proprietario": true,
            "status_conab": "Registrado"
        }}
    ],
    "capacidade_total_toneladas": 0,
    "total_unidades": 0,
    "tipo_predominante": "Silo/Galpao/Misto",
    "necessidade_wms": "CRITICA/ALTA/MEDIA/BAIXA",
    "argumento_venda": ""
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[CONAB] Erro: {e}")
            return {}

    async def _frota_rntrc(self, empresa: str) -> Dict:
        prompt = f"""ATUE COMO: Auditor de Transporte (ANTT).
ALVO: {empresa}

BUSQUE DADOS DE FROTA E LOGISTICA:

1. ANTT - RNTRC (Registro Nacional de Transportadores):
   - site:antt.gov.br "RNTRC" "{empresa}"
   - Se ativo: empresa EH transportadora
   - Dados: quantidade veiculos, tipos, placas

2. SE TEM RNTRC = OBRIGACOES FISCAIS:
   - CTe (Conhecimento de Transporte Eletronico)
   - MDFe (Manifesto de Documento Fiscal Eletronico)
   - CIOT (Comprovante de Informacoes Operacionais)
   - Declaracao de Cargas Especiais

3. SE NAO TEM RNTRC MAS TRANSPORTA:
   - "Contrato de Logistica" AND "{empresa}" (Usa terceiros?)
   - Qual operadora logistica?

4. FROTA PROPRIA (NOTICIAS):
   - "{empresa}" compra caminhoes/colheitadeiras
   - Marca predominante (Volvo, Scania, Mercedes)
   - Frota agricola (John Deere, Case, Massey)

PERGUNTA DE VENDEDOR: "Voce esta emitindo X documentos por dia manualmente ou integrado?"

RETORNE JSON:
{{
    "rntrc": {{
        "ativo": false,
        "numero": "",
        "desde": "",
        "quantidade_veiculos": 0,
        "tipos_veiculos": []
    }},
    "obrigacoes_fiscais": {{
        "cte_obrigatorio": false,
        "mdfe_obrigatorio": false,
        "ciot_obrigatorio": false,
        "volume_documentos_estimado_dia": 0
    }},
    "frota_propria": {{
        "caminhoes": 0,
        "carretas": 0,
        "marca_predominante": "",
        "colheitadeiras": 0,
        "marca_agricola": ""
    }},
    "logistica_terceirizada": {{
        "usa_terceiros": false,
        "operadoras": []
    }},
    "necessidade_tms": "CRITICA/ALTA/MEDIA/BAIXA",
    "argumento_venda": "Se emitem 200+ CTe/dia manualmente, Senior TMS resolve em 3 segundos integrado com SEFAZ"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[RNTRC] Erro: {e}")
            return {}

    async def _exportacao_comexstat(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Analista de Comercio Exterior Agricola.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

BUSQUE DADOS DE EXPORTACAO:

1. Comexstat (MDIC): site:comexstat.mdic.gov.br "{empresa}"
   - Exportacoes ultimos 24 meses
   - Paises destino (NCM x Pais)
   - Valores FOB
   - Sazonalidade

2. SISCOMEX: "{empresa}" "Exportador" site:gov.br

3. ANALISE COMERCIAL:
   - Se exportam muito = Compliance internacional = Oportunidade de sistema integrado
   - Se exportacao caiu = Dificuldade = Aceita investimento para "eficiencia"
   - Se concentrada em 1-2 paises = Risco geopolitico = Venda de "diversificacao"

RETORNE JSON:
{{
    "exporta": true,
    "dados_exportacao": [
        {{
            "produto": "Soja em Grao",
            "ncm": "1201.10.00",
            "paises_destino": {{"China": "70%", "EU": "20%", "Outros": "10%"}},
            "volume_toneladas_2024": 0,
            "valor_fob_usd_2024": 0,
            "sazonalidade": "Pico jan-abr"
        }}
    ],
    "receita_total_exportacao": "USD 0",
    "concentracao_mercado": {{
        "pais_principal": "China",
        "percentual": "70%",
        "risco_geopolitico": "ALTO/MEDIO/BAIXO"
    }},
    "tendencia": "CRESCIMENTO/ESTAVEL/QUEDA",
    "compliance_exigido": ["Drawback", "EUDR", "Fitossanitario", "Certificado Origem"],
    "argumento_venda": ""
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[EXPORTACAO] Erro: {e}")
            return {}

    def _resumo_cadeia(self, results: Dict) -> Dict:
        arm = results.get("armazenagem", {})
        frota = results.get("frota_logistica", {})
        exp = results.get("exportacao", {})

        cap_total = arm.get("capacidade_total_toneladas", 0)
        veiculos = frota.get("frota_propria", {}).get("caminhoes", 0)
        exporta = exp.get("exporta", False)

        cadeia = "[Fazenda]"
        if cap_total > 0:
            cadeia += f" -> [Armazenagem {cap_total:,.0f}t]"
        if veiculos > 0:
            cadeia += f" -> [Frota {veiculos} veiculos]"
        if exporta:
            cadeia += " -> [Exportacao]"

        return {
            "diagrama_cadeia": cadeia,
            "complexidade": "ALTA" if (cap_total > 100000 and veiculos > 30) else "MEDIA" if cap_total > 0 else "BAIXA",
            "modulos_necessarios": self._modulos_necessarios(results)
        }

    def _modulos_necessarios(self, results: Dict) -> List[str]:
        modulos = ["ERP Core"]
        arm = results.get("armazenagem", {})
        frota = results.get("frota_logistica", {})
        exp = results.get("exportacao", {})

        if arm.get("capacidade_total_toneladas", 0) > 0:
            modulos.append("WMS (Warehouse)")
        if frota.get("rntrc", {}).get("ativo"):
            modulos.append("TMS (Transporte)")
        if frota.get("obrigacoes_fiscais", {}).get("cte_obrigatorio"):
            modulos.append("CTe/MDFe Integrado")
        if exp.get("exporta"):
            modulos.append("Compliance Exportacao")
            modulos.append("Drawback")
        return modulos

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
