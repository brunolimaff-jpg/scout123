"""
services/dossier_orchestrator.py — VERSÃO CORRIGIDA E ESTRUTURADA
Garante que o dicionário de saída corresponda ao que app.py e export_handler esperam.
"""
import asyncio
import logging
import re
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DossierOrchestrator:
    """
    Orquestrador que coordena as camadas e estrutura o dossiê final
    no formato aninhado esperado pelo ExportHandler e App.
    """
    
    def __init__(
        self, 
        gemini_service,
        infrastructure_layer,
        financial_layer,
        intelligence_layer,
        market_estimator
    ):
        self.gemini = gemini_service
        self.infra = infrastructure_layer
        self.financial = financial_layer
        self.intel = intelligence_layer
        self.market = market_estimator
    
    async def _buscar_todos_cnpjs_vinculados(self, nome_ou_grupo: str) -> List[Dict]:
        """Busca TODOS os CNPJs vinculados a um grupo."""
        logger.info(f"[Orchestrator] Buscando TODOS CNPJs vinculados a: {nome_ou_grupo}")
        
        prompt = f"""MISSAO: Encontre TODOS os CNPJs relacionados ao nome/grupo abaixo.
ALVO: {nome_ou_grupo}
INSTRUCOES: Busque holding, filiais e empresas relacionadas.
FORMATO JSON: [{{"cnpj": "...", "razao_social": "...", "tipo": "..."}}]
"""
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3, use_search=True, temperature=0.1)
            if not response: return []
            
            clean = response.replace("```json", "").replace("```", "").strip()
            # Tenta extrair lista do JSON
            try:
                lista = json.loads(clean)
                if isinstance(lista, list): return lista
            except:
                pass
                
            # Regex fallback
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            if match: return json.loads(match.group(0))
            
            return []
        except Exception as e:
            logger.error(f"[Orchestrator] Erro ao buscar CNPJs: {e}")
            return []

    async def executar_dosier_completo(self, razao_social: str, cnpj: str = "", callback=None) -> Dict:
        """Ponto de entrada principal."""
        from services.cnpj_service import consultar_cnpj
        
        cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ""
        
        if cnpj_limpo and len(cnpj_limpo) == 14:
            if callback: callback("Consultando dados cadastrais (CNPJ)...")
            cnpj_data_obj = consultar_cnpj(cnpj_limpo)
            if not cnpj_data_obj:
                raise ValueError(f"CNPJ {cnpj_limpo} não encontrado")
            
            cnpj_dict = {
                "cnpj": cnpj_data_obj.cnpj,
                "nome": cnpj_data_obj.razao_social,
                "qsa": cnpj_data_obj.qsa,
                "municipio": cnpj_data_obj.municipio,
                "uf": cnpj_data_obj.uf,
                "capital_social": cnpj_data_obj.capital_social
            }
            return await self.gerar_dossie_completo(cnpj_dict, progress_callback=callback)
            
        else:
            if callback: callback(f"Buscando estrutura corporativa de '{razao_social}'...")
            cnpjs = await self._buscar_todos_cnpjs_vinculados(razao_social)
            if not cnpjs:
                 # Fallback: Tenta tratar como empresa única se não achar lista
                 if callback: callback(f"Estrutura não encontrada, tentando busca direta...")
                 return await self.gerar_dossie_completo({"nome": razao_social, "cnpj": ""}, progress_callback=callback)
                 
            if callback: callback(f"Encontrados {len(cnpjs)} CNPJs. Consolidando...")
            return await self._gerar_dossie_consolidado_grupo(cnpjs, razao_social, progress_callback=callback)

    async def _gerar_dossie_consolidado_grupo(self, cnpjs_list: List[Dict], nome_grupo: str, progress_callback=None) -> Dict:
        """Gera dossiê consolidado com estrutura CORRETA."""
        
        # 1. Mapeamento de Sócios e Dados Básicos
        todos_socios = []
        cpfs_unicos = []
        capital_total = 0
        
        # Pega a empresa principal (assumindo a primeira ou a que tem 'holding' no nome)
        empresa_principal = cnpjs_list[0]
        
        # 2. Infraestrutura (SIGEF/CAR) - Agrupado
        if progress_callback: progress_callback("Mapeando terras e ativos (Consolidado)...")
        
        try:
            # Passa lista vazia de CPFs por enquanto para agilizar, ou extrairia de uma consulta detalhada
            sigef_data = await self.infra.buscar_sigef_car(nome_grupo, [])
        except Exception as e:
            logger.error(f"Erro Infra: {e}")
            sigef_data = {"area_total_hectares": 0}

        area_total = sigef_data.get("area_total_hectares", 0)

        # 3. Financeiro (CRA/Debêntures)
        if progress_callback: progress_callback("Analisando saúde financeira...")
        try:
            cra_data = await self.financial.mineracao_cra_debentures(nome_grupo, "")
        except:
            cra_data = {}

        # 4. Inteligência (Concorrentes/Tech)
        if progress_callback: progress_callback("Analisando mercado e tecnologia...")
        try:
            intel_data = await self.intel.mapeamento_concorrentes(nome_grupo, [], [])
            tech_data = await self.intel.mapeamento_stack_tecnologico(nome_grupo, "")
        except:
            intel_data = {}
            tech_data = {}

        # 5. Estruturação dos Dados para Cálculo SAS
        dados_para_sas = {
            "hectares_total": area_total,
            "funcionarios_estimados": 0, # Teria que estimar
            "numero_fazendas": len(sigef_data.get('car_records', [])),
            "capital_social_estimado": 0,
            "faturamento_estimado": cra_data.get("faturamento_real", 0),
            "culturas": [], # Extrair de SIGEF
            "tech_stack": tech_data,
            "cadeia_valor": {"exporta": False, "certificacoes": []} 
        }

        # 6. Cálculo SAS
        try:
            sas_result = self.market.calcular_sas(dados_para_sas)
            sas_score = sas_result.score
            sas_tier = sas_result.tier.value
        except Exception as e:
            logger.error(f"Erro SAS: {e}")
            sas_score = 0
            sas_tier = "N/D"

        # 7. Montagem do Dicionário Final (ESTRUTURA ANINHADA OBRIGATÓRIA)
        dossie = {
            "empresa_alvo": nome_grupo, # CHAVE CRÍTICA PARA EXPORT_HANDLER
            "tipo_dossie": "CONSOLIDADO",
            "sas_score": sas_score,
            "sas_tier": sas_tier,
            
            "dados_operacionais": {
                "area_total": area_total, # CHAVE CRÍTICA
                "hectares_total": area_total,
                "regioes_atuacao": sigef_data.get("estados_operacao", []),
                "culturas": [],
                "numero_fazendas": len(sigef_data.get('car_records', []))
            },
            
            "dados_financeiros": {
                "faturamento_estimado": cra_data.get("faturamento_real", "N/D"),
                "capital_social_estimado": 0,
                "ebitda_ajustado": cra_data.get("ebitda_consolidado", "N/D")
            },
            
            "tech_stack": {
                "erp_principal": tech_data.get("erp_atual", "N/D"),
                "maturidade_ti": tech_data.get("maturidade_digital", "N/D")
            },
            
            "analise_estrategica": {
                "quem_e_empresa": f"Grupo identificado com área de {area_total} hectares.",
                "complexidade_dores": intel_data.get("posicionamento_relativo", "Análise em processamento"),
                "arsenal_recomendado": "Solução completa Senior Agro (ERP + Gestão Agrícola)",
                "plano_ataque": "Abordagem consultiva focada em eficiência operacional."
            },
            
            # Dados brutos para abas extras
            "sigef_car": sigef_data,
            "cra_debentures": cra_data,
            "concorrentes": intel_data,
            "empresas_grupo": cnpjs_list
        }
        
        if progress_callback: progress_callback("Dossiê consolidado concluído.")
        return dossie

    async def gerar_dossie_completo(self, cnpj_data: Dict, progress_callback=None) -> Dict:
        """Gera dossiê único com estrutura CORRETA."""
        razao_social = cnpj_data.get('nome', 'Empresa')
        
        # 1. Execução Paralela
        if progress_callback: progress_callback("Executando varredura profunda...")
        
        # Dispara tasks
        t_sigef = self.infra.buscar_sigef_car(razao_social, [])
        t_cra = self.financial.mineracao_cra_debentures(razao_social, cnpj_data.get('cnpj', ''))
        t_tech = self.intel.mapeamento_stack_tecnologico(razao_social, cnpj_data.get('cnpj', ''))
        t_intel = self.intel.mapeamento_concorrentes(razao_social, [], [])
        
        results = await asyncio.gather(t_sigef, t_cra, t_tech, t_intel, return_exceptions=True)
        
        # Processa resultados
        sigef_data = results[0] if not isinstance(results[0], Exception) else {}
        cra_data = results[1] if not isinstance(results[1], Exception) else {}
        tech_data = results[2] if not isinstance(results[2], Exception) else {}
        intel_data = results[3] if not isinstance(results[3], Exception) else {}
        
        # 2. Cálculo SAS
        area_total = sigef_data.get('area_total_hectares', 0)
        
        dados_sas = {
            "hectares_total": area_total,
            "faturamento_estimado": cra_data.get("faturamento_real", 0),
            "capital_social_estimado": cnpj_data.get("capital_social", 0),
            "tech_stack": tech_data,
            "funcionarios_estimados": 0 # Pode vir de outra layer
        }
        
        try:
            sas_result = self.market.calcular_sas(dados_sas)
            sas_score = sas_result.score
            sas_tier = sas_result.tier.value
            sas_recomendacao = sas_result.recomendacao_comercial
        except Exception as e:
            logger.error(f"Erro calculo SAS: {e}")
            sas_score = 0
            sas_tier = "N/D"
            sas_recomendacao = ""

        # 3. Montagem Final (ESTRUTURA ANINHADA)
        dossie = {
            "empresa_alvo": razao_social, # CHAVE CRÍTICA
            "cnpj": cnpj_data.get('cnpj', ''),
            "sas_score": sas_score,
            "sas_tier": sas_tier,
            
            "dados_operacionais": {
                "area_total": area_total,
                "hectares_total": area_total,
                "regioes_atuacao": sigef_data.get("estados_operacao", []),
                "culturas": [],
                "numero_fazendas": len(sigef_data.get('car_records', []))
            },
            
            "dados_financeiros": {
                "faturamento_estimado": cra_data.get("faturamento_real", "N/D"),
                "capital_social_estimado": cnpj_data.get("capital_social", 0),
                "ebitda_ajustado": cra_data.get("ebitda_consolidado", "N/D")
            },
            
            "tech_stack": {
                "erp_principal": tech_data.get("erp_atual", "N/D"),
                "maturidade_ti": tech_data.get("maturidade_digital", "N/D")
            },
            
            "analise_estrategica": {
                "quem_e_empresa": f"Empresa com {area_total} ha mapeados.",
                "complexidade_dores": intel_data.get("posicionamento_relativo", ""),
                "arsenal_recomendado": sas_recomendacao,
                "plano_ataque": "Verificar oportunidades em digitalização e gestão."
            },
            
            # Dados brutos
            "sigef_car": sigef_data,
            "cra_debentures": cra_data,
            "tech_stack_identificado": tech_data
        }
        
        if progress_callback: progress_callback("Dossiê gerado com sucesso!")
        return dossie
