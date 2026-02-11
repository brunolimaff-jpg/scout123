"""
services/territorial_layer.py — FASE 2: INTELIGENCIA TERRITORIAL ABSOLUTA
Bandeirante Digital v3.0 - INCRA, SIGEF, SEMA, EIA/RIMA, CAR.
Mapeamento fundiario completo com adjacencias e conflitos.
"""
import logging
import re
import json
from typing import Dict, List

logger = logging.getLogger(__name__)


class TerritorialLayer:
    """
    Fase 2 do Bandeirante Digital: Intelecto Territorial.
    Mapeia fazendas, areas, licencas ambientais, conflitos fundiarios.
    """

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def mapeamento_territorial_completo(self, empresa: str, cnpj: str = "") -> Dict:
        """Pipeline completo de inteligencia territorial."""
        logger.info(f"[TERRITORIAL] Iniciando mapeamento fundiario: {empresa}")

        results = {}

        try:
            fundiario = await self._busca_fundiaria(empresa, cnpj)
            results["dados_fundiarios"] = fundiario
        except Exception as e:
            logger.warning(f"[TERRITORIAL] Erro fundiario: {e}")
            results["dados_fundiarios"] = {}

        try:
            ambiental = await self._licencas_ambientais(empresa)
            results["licencas_ambientais"] = ambiental
        except Exception as e:
            logger.warning(f"[TERRITORIAL] Erro ambiental: {e}")
            results["licencas_ambientais"] = {}

        try:
            adjacencias = await self._analise_adjacencias(empresa, fundiario)
            results["adjacencias"] = adjacencias
        except Exception as e:
            logger.warning(f"[TERRITORIAL] Erro adjacencias: {e}")
            results["adjacencias"] = {}

        # Resumo territorial
        results["resumo_territorial"] = self._resumo(results)
        return results

    async def _busca_fundiaria(self, empresa: str, cnpj: str) -> Dict:
        prompt = f"""ATUE COMO: Perito em Cartografia Rural e Georreferenciamento.
ALVO: {empresa} (CNPJ: {cnpj if cnpj else 'N/D'})

BUSQUE DADOS FUNDIARIOS EM FONTES PUBLICAS:

1. INCRA (Livro de Ouro):
   - CCIRs (Certificado de Cadastro de Imovel Rural): site:incra.gov.br "CCIRs" "{empresa}"
   - SIGEF (Sistema de Gestao Fundiaria): site:incra.gov.br "SIGEF" "{empresa}"
   - Busca direta de imoveis: site:incra.gov.br "Imovel" "{empresa}"
   Para cada imovel: Nome fazenda, tamanho (ha), municipio, coordenadas, data registro

2. CAR (Cadastro Ambiental Rural):
   - Busque no SICAR (Sistema Nacional de Cadastro Ambiental Rural)
   - "{empresa}" "CAR" OR "Cadastro Ambiental Rural"
   - Sobreposicoes de poligonos, areas de APP, Reserva Legal

3. EIA/RIMA (Documentos Gold Mine):
   - "Estudo de Impacto Ambiental" OR "EIA/RIMA" AND "{empresa}"
   - "Relatorio Ambiental Preliminar" AND "{empresa}"
   - Contem: Descricao geologica, solo, clima, mapa completo, lista de equipamentos

4. GEORREFERENCIAMENTO:
   - "{empresa}" "georreferenciado" "ha"
   - "Poligono" AND "{empresa}" site:sigef.incra.gov.br

RETORNE JSON:
{{
    "imoveis_rurais": [
        {{
            "nome_fazenda": "Fazenda Sao Jose",
            "municipio": "Sapezal-MT",
            "uf": "MT",
            "area_ha": 15000,
            "tipo_operacao": "Soja/Milho/Algodao",
            "data_registro": "2018-06-15",
            "georreferenciado": true,
            "coordenadas_aprox": "-13.5, -58.7",
            "infraestrutura_visivel": "Silos, secadores, sede administrativa"
        }}
    ],
    "area_total_ha": 0,
    "total_imoveis": 0,
    "estados_presenca": [],
    "municipios": [],
    "expansao_recente": {{
        "novas_areas_12m": false,
        "detalhes": ""
    }},
    "car_status": {{
        "cadastrado": true,
        "app_regular": true,
        "reserva_legal_ok": true,
        "sobreposicoes": false
    }}
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[FUNDIARIO] Erro: {e}")
            return {}

    async def _licencas_ambientais(self, empresa: str) -> Dict:
        prompt = f"""ATUE COMO: Consultor Ambiental.
ALVO: {empresa}

BUSQUE LICENCAS AMBIENTAIS EM:
1. SEMA-MT: site:sema.mt.gov.br "Licenca de Operacao" "{empresa}"
2. IMASUL-MS: site:imasul.ms.gov.br "Autorizacao Ambiental" "{empresa}"
3. SEMA-GO: site:sema.go.gov.br "{empresa}"
4. IBAMA: site:ibama.gov.br "{empresa}"

PARA CADA LICENCA:
- Tipo (LP, LI, LO, LAU)
- Data emissao e validade
- Atividade licenciada
- Localizacao (coordenadas se possivel)
- Condicionantes relevantes (rastreabilidade ambiental?)

LICENCAS EMITIDAS HA MENOS DE 6 MESES = NOVOS ATIVOS = PRECISA DE SISTEMA URGENTE

RETORNE JSON:
{{
    "licencas_ativas": [
        {{
            "tipo": "LO - Licenca de Operacao",
            "orgao": "SEMA-MT",
            "data_emissao": "2024-06-15",
            "validade": "2028-06-15",
            "atividade": "Atividade agroindustrial - Algodoeira",
            "localizacao": "Sapezal-MT",
            "recente": true,
            "implicacao": "Nova algodoeira = precisa de WMS + rastreabilidade"
        }}
    ],
    "total_licencas": 0,
    "licencas_recentes_6m": 0,
    "condicionantes_sistema": "Condicionantes que exigem software (rastreabilidade, monitoramento)"
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[LICENCAS] Erro: {e}")
            return {}

    async def _analise_adjacencias(self, empresa: str, dados_fundiarios: Dict) -> Dict:
        fazendas = dados_fundiarios.get("imoveis_rurais", [])
        municipios = [f.get("municipio", "") for f in fazendas[:5]]
        municipios_str = ", ".join(municipios) if municipios else "N/D"

        prompt = f"""ATUE COMO: Geoestrategista Rural.
ALVO: {empresa}
MUNICIPIOS IDENTIFICADOS: {municipios_str}

ANALISE ADJACENCIAS ESTRATEGICAS:

1. INFRAESTRUTURA PROXIMA:
   - Silos de terceiros proximos?
   - Moagens/processadoras vizinhas?
   - Portos/terminais de grãos acessíveis?
   - Ferrovias (Ferrograo, Rumo, VLI)?

2. RISCOS FUNDIARIOS:
   - "Conflito Fundiario" AND "{empresa}" (Disputa de terras?)
   - "Invasao" AND "{empresa}" (MST ou posseiros?)
   - Unidades de Conservacao proximas (regulacao extra)?
   - Bacias hidrograficas sensiveis?

3. LOGISTICA:
   - Distancia ate porto mais proximo
   - Estradas (BR/MT pavimentada ou terra?)
   - Ferrovia acessivel?

RETORNE JSON:
{{
    "infraestrutura_proxima": {{
        "silos_terceiros": [],
        "processadoras": [],
        "portos_acessiveis": [],
        "ferrovias": []
    }},
    "riscos_fundiarios": {{
        "conflitos_ativos": false,
        "invasoes": false,
        "unidades_conservacao_proximas": false,
        "detalhes": ""
    }},
    "logistica": {{
        "porto_mais_proximo": "",
        "distancia_porto_km": 0,
        "ferrovia_acessivel": false,
        "qualidade_estradas": "Boa/Regular/Precaria"
    }}
}}"""

        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.2)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"[ADJACENCIAS] Erro: {e}")
            return {}

    def _resumo(self, results: Dict) -> Dict:
        fundiario = results.get("dados_fundiarios", {})
        licencas = results.get("licencas_ambientais", {})

        area_total = fundiario.get("area_total_ha", 0)
        total_imoveis = fundiario.get("total_imoveis", 0)
        licencas_recentes = licencas.get("licencas_recentes_6m", 0)

        argumento = ""
        if area_total > 50000:
            argumento = f"Empresa com {area_total:,.0f} ha espalhados em {total_imoveis} unidades. "
            argumento += "Gestao multi-site desta complexidade exige sistema centralizado."
        if licencas_recentes > 0:
            argumento += f" {licencas_recentes} licenca(s) recente(s) = novos ativos = URGENCIA de sistema."

        return {
            "area_total_ha": area_total,
            "total_imoveis": total_imoveis,
            "estados": fundiario.get("estados_presenca", []),
            "licencas_recentes": licencas_recentes,
            "argumento_venda": argumento or "Verificar dados fundiarios para argumento personalizado."
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
