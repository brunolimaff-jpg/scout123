import requests
import json
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class InfrastructureLayer:
    """
    Camada responsável por mapear ativos físicos:
    - SIGEF/CAR (terra + regularização fundiária)
    - Frota (maquinário via leilões, CPR, BNDES/Finame)
    - Conectividade (cobertura 4G/5G Anatel)
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    # ======== SIGEF / CAR ========
    async def buscar_sigef_car(self, razao_social: str, cpfs_socios: List[str]) -> Dict:
        """
        Busca códigos SIGEF e CAR via Diários Oficiais e dados públicos.
        Output: Polígonos, localização, status, hectares.
        """
        logger.info(f"[SIGEF/CAR] Rastreando {razao_social}")
        
        prompt = f"""Você é um especialista em consultas fundiárias brasileiras. Sua missão é ENCONTRAR propriedades rurais documentadas.

ALVO: {razao_social}
CPFs SÓCIOS: {', '.join(cpfs_socios)}

BUSQUE EM:
1. Registros SIGEF (Sistema de Gestão Fundiária) - Código: SIGEF-XXXXXX
2. Registros CAR (Cadastro Ambiental Rural) - ID: formato numérico 
3. Diários Oficiais (DOE) de MG, SP, MT, GO, MS, BA, MA, TO, PR, RS
4. Palavras-chave: "Deferimento CAR {razao_social}", "Registro de Imóvel Rural", "Matrícula"

VALIDE:
- Município onde está registrada cada propriedade
- Tamanho em hectares (extrair do CAR ou estimativa de área)
- Status: Deferido / Pendente / Cancelado
- Data de registro ou deferimento
- Se possível, identificar culturas (soja, milho, algodão, pecuária)

RETORNE JSON COM:
{{
    "sigef_records": [
        {{"codigo": "SIGEF-123456", "municipio": "Bom Despacho", "uf": "MG", "hectares": 2500, "status": "Ativo"}},
        {{"codigo": "SIGEF-789012", "municipio": "Cuiabá", "uf": "MT", "hectares": 1800, "status": "Ativo"}}
    ],
    "car_records": [
        {{"id_car": "ABC123456789", "municipio": "Bom Despacho", "uf": "MG", "hectares": 2500, "status": "Deferido", "data_deferimento": "2024-01-15", "culturas": ["Soja", "Algodão"]}},
        {{"id_car": "XYZ987654321", "municipio": "Cuiabá", "uf": "MT", "hectares": 1800, "status": "Deferido", "data_deferimento": "2023-11-22", "culturas": ["Soja", "Milho"]}}
    ],
    "area_total_hectares": 4300,
    "regularizacao_percentual": 100,
    "estados_operacao": ["MG", "MT"],
    "observacoes": "Todas as propriedades deferidas. Documentação regularizada."
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[SIGEF/CAR] ✅ {data.get('area_total_hectares', 0)} ha mapeados")
            return data
        except Exception as e:
            logger.error(f"[SIGEF/CAR] ❌ Erro: {e}")
            return {
                "sigef_records": [],
                "car_records": [],
                "area_total_hectares": 0,
                "regularizacao_percentual": 0,
                "status": "erro"
            }
    
    # ======== FROTA (Maquinário) ========
    async def forense_maquinario(self, razao_social: str, cnpj: str) -> Dict:
        """
        Busca maquinário via:
        - Leilões históricos (equipamentos)
        - CPR (Cédulas de Produto Rural)
        - Financiamentos BNDES/Finame (públicos)
        - Registros de garantia (Anajus)
        """
        logger.info(f"[MAQUINÁRIO] Forense de frota: {razao_social}")
        
        prompt = f"""Você é especialista em rastreamento de frotas agrícolas e financiamentos de máquinas.

ALVO: {razao_social} ({cnpj})

BUSQUE EVIDÊNCIAS DE MAQUINÁRIO:
1. Leilões (editalais de leilão, sucata, equipamentos) - mencionar {razao_social} como licitante/vendedor
2. CPR (Cédulas de Produto Rural) registradas com garantia em máquinas
3. Operações BNDES/Finame (Programa de Modernização da Frota Agrícola)
4. Registros de penhor em cartório (máquinas como garantia)
5. Notas de compra/venda de equipamentos agrícolas (John Deere, CLAAS, Massey Ferguson, etc)

PADRÕES TÍPICOS:
- 1 propriedade de 1000ha = ~10 Tratores + 5 Colheitadeiras
- Propriedade de 5000ha = ~50 Tratores + 25 Colheitadeiras + implementos

RETORNE JSON:
{{
    "maquinario_confirmado": [
        {{"tipo": "Colheitadeira", "modelo": "S700", "quantidade": 45, "fonte": "Leilão ABC 2023", "ano_aquisicao": 2022}},
        {{"tipo": "Trator", "modelo": "8R", "quantidade": 120, "fonte": "BNDES/Finame", "ano_aquisicao": "2021-2024"}},
        {{"tipo": "Plantadeira", "modelo": "SoilLiner", "quantidade": 35, "fonte": "CPR com Garantia", "ano_aquisicao": 2023}}
    ],
    "frota_estimada_total": {{
        "tratores": 120,
        "colheitadeiras": 45,
        "plantadeiras": 35,
        "implementos": 200,
        "pivot_center": 12
    }},
    "valor_estimado_frota": "R$ 450 milhões",
    "idade_media_anos": 4.2,
    "financiamentos_ativos": [
        {{"programa": "FINAME", "valor": "R$ 150M", "vencimento": "2026"}}
    ],
    "observacoes": "Frota moderna, bem financiada, indica operação de escala gigante."
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[MAQUINÁRIO] ✅ Frota estimada: {data.get('frota_estimada_total', {}).get('tratores', 0)} tratores")
            return data
        except Exception as e:
            logger.error(f"[MAQUINÁRIO] ❌ Erro: {e}")
            return {"maquinario_confirmado": [], "frota_estimada_total": {}, "status": "erro"}
    
    # ======== CONECTIVIDADE (Anatel/4G/5G) ========
    async def analise_conectividade(self, municipios: List[str], coordenadas: List[Dict]) -> Dict:
        """
        Cruza localização das fazendas com cobertura 4G/5G da Anatel.
        Identifica zonas de sombra = oportunidades de infra privada/Starlink.
        """
        logger.info(f"[CONECTIVIDADE] Analisando {len(municipios)} municípios")
        
        municipios_str = ", ".join(municipios)
        coordenadas_str = json.dumps(coordenadas)
        
        prompt = f"""Você é especialista em infraestrutura de telecomunicações rural.

FAZENDAS LOCALIZADAS EM: {municipios_str}
COORDENADAS GEOGRÁFICAS: {coordenadas_str}

CONSULTE MAPA ANATEL (dados abertos) E VERIFIQUE:
1. Cobertura 4G por operadora (Vivo, Claro, Oi, TIM)
2. Cobertura 5G (onde existe)
3. Zonas de sombra (sem sinal)
4. Velocidade média esperada (Mbps)
5. Latência típica

IDENTIFIQUE OPORTUNIDADES:
- Zona de Sombra → Venda de: Starlink, tower privada, mesh network
- 4G fraco → Venda de: repetidores, antenas internas, roteadores profissionais
- Sem 5G → Oportunidade de parceria de instalação

RETORNE JSON:
{{
    "analise_por_municipio": [
        {{
            "municipio": "Bom Despacho",
            "uf": "MG",
            "cobertura_4g": {{"vivo": "95%", "claro": "90%", "oi": "40%", "tim": "70%"}},
            "cobertura_5g": "Não",
            "zonas_sombra": "Norte do município",
            "velocidade_media_mbps": 15,
            "latencia_ms": 45,
            "recomendacoes": ["Starlink para zonas críticas", "Tower privada possível"]
        }},
        {{
            "municipio": "Cuiabá",
            "uf": "MT",
            "cobertura_4g": {{"vivo": "98%", "claro": "98%", "oi": "60%", "tim": "95%"}},
            "cobertura_5g": "Sim (Centro urbano)",
            "zonas_sombra": "Rural profundo",
            "velocidade_media_mbps": 25,
            "latencia_ms": 30,
            "recomendacoes": ["5G para centros operacionais", "Starlink para periferias"]
        }}
    ],
    "oportunidades_venda": [
        {{"tipo": "Starlink", "estimativa_usuarios": 15, "valor_mensal": "R$ 600/unidade"}},
        {{"tipo": "Tower privada 4G", "investimento": "R$ 2.5M", "ROI_anos": 3}}
    ],
    "score_criticidade_telecom": "Alto"
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[CONECTIVIDADE] ✅ Análise concluída")
            return data
        except Exception as e:
            logger.error(f"[CONECTIVIDADE] ❌ Erro: {e}")
            return {"analise_por_municipio": [], "oportunidades_venda": [], "status": "erro"}
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse seguro de respostas JSON da IA."""
        try:
            # Remove markdown code fences
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            logger.warning("Falha ao parsear JSON, retornando estrutura vazia")
            return {}
