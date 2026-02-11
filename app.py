"""
services/infrastructure_layer.py — VERSÃO ULTRA DEEP (RAIO-X FÍSICO)
Foca em Licenças Ambientais, Relatórios GRI e Ativos Logísticos para detalhar a operação.
"""
import logging
import re
import json
import asyncio
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class InfrastructureLayer:
    """
    Camada de Mapeamento Físico e Logístico.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    async def buscar_sigef_car(self, empresa: str, cnpjs: List[str]) -> Dict:
        """Wrapper de compatibilidade."""
        return await self.mapeamento_geografico_completo(empresa)

    async def mapeamento_geografico_completo(self, empresa: str) -> Dict:
        """
        Busca profunda de ativos: Fazendas, Indústria, Logística e Energia.
        """
        logger.info(f"[INFRA] Iniciando Varredura Profunda: {empresa}")
        
        prompt = f"""
        ATUE COMO: Auditor de Ativos Agrícolas e Engenheiro Civil.
        ALVO: {empresa}
        
        MISSÃO: Mapear TODO o patrimônio físico e logístico da empresa. Quero DETALHES TÉCNICOS.
        Não aceite respostas genéricas. Busque em Relatórios de Sustentabilidade, Licenças Ambientais (SEMA/IBAMA) e Notícias Corporativas.
        
        EXTRAIA AS SEGUINTES INFORMAÇÕES (Seja exaustivo):
        
        1. 🏢 CORPORATIVO (QG & Filiais):
           - Endereço completo da Matriz (Cidade, Bairro, Edifício).
           - Possui escritório comercial em capitais (SP, Cuiabá)?
           
        2. 🌾 LISTA DE FAZENDAS (Unidades Produtivas):
           - Liste NOMES REAIS das fazendas.
           - Município/UF de cada uma.
           - Atividade (Soja, Algodão, Pecuária, Integração).
           - Área individual (se disponível em notícias).
           
        3. 🏭 PARQUE INDUSTRIAL & BIO (Além dos Silos):
           - Biofábricas (Produção On-Farm)? Capacidade?
           - Usinas Fotovoltaicas (Energia Solar)? Potência (MW)?
           - Algodoeiras/Fiações Próprias?
           - Fábricas de Fertilizantes/Fósforo?
           
        4. 🚚 LOGÍSTICA & FROTA (O fluxo do dinheiro):
           - Frota Rodoviária: Quantidade estimada de caminhões/carretas? Marca predominante (Volvo/Scania)?
           - Frota Aérea (Hangar): Possuem aviões agrícolas (Air Tractor)? Executivos (King Air/Pilatus)? Onde fica o hangar?
           - Maquinário: Alguma grande aquisição recente (ex: "Comprou 50 colheitadeiras John Deere")?

        RETORNE APENAS JSON NESTE FORMATO:
        {{
            "resumo_territorial": {{
                "area_total_ha": 0,
                "estados": ["MT", "PA", etc],
                "total_unidades": 0
            }},
            "corporativo": {{
                "matriz_endereco": "Logradouro, Numero, Cidade - UF",
                "escritorios_regionais": ["Cidade A", "Cidade B"]
            }},
            "lista_fazendas": [
                {{"nome": "Fazenda X", "municipio": "Cidade-UF", "detalhe": "Produção de Sementes / 50.000 ha"}}
            ],
            "complexo_industrial": [
                {{"tipo": "Biofábrica", "detalhe": "Capacidade 2.6M litros/ano"}},
                {{"tipo": "Energia", "detalhe": "Usina Solar Fotovoltaica 1.5MW"}}
            ],
            "logistica_bimodal": {{
                "frota_rodoviaria": "Ex: +150 Carretas Volvo FH 540",
                "frota_aerea": "Ex: Hangar em Sapezal com 3 Air Tractor e 1 King Air",
                "patio_maquinas": "Ex: Frota 100% conectada John Deere"
            }}
        }}
        """
        
        try:
            # Temperatura 0.1 para buscar fatos, não inventar
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            
            if match:
                dados = json.loads(match.group(0))
                
                # Tratamento de erro para área total se vier zerada
                if dados.get("resumo_territorial", {}).get("area_total_ha") == 0:
                     nums = re.findall(r'(\d{2,3}[\.,]\d{3})', response)
                     if nums:
                         try:
                             val = float(nums[0].replace(".", "").replace(",", "."))
                             # Filtra valores absurdamente pequenos ou grandes demais p/ ser área total se for ambíguo
                             if val > 1000: 
                                dados["resumo_territorial"]["area_total_ha"] = val
                         except: pass
                
                return dados
            
            return {}

        except Exception as e:
            logger.error(f"[INFRA] Erro deep scan: {e}")
            return {}
