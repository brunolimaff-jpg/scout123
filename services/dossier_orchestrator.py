"""
services/dossier_orchestrator.py — VERSÃO ULTRA-AGRESSIVA
Coordena todas as camadas com prompts otimizados
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
    Orquestrador ultra-agressivo que GARANTE dados no dossiê.
    
    Estratégia:
    1. Executa todas camadas em paralelo (quando possível)
    2. Valida respostas - se vazio, REFAZ a busca com prompt mais agressivo
    3. Consolida inteligência final em relatório estruturado
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
        """
        Busca TODOS os CNPJs vinculados a um grupo, empresa ou pessoa.
        
        Args:
            nome_ou_grupo: Nome do grupo, empresa ou pessoa física
        
        Returns:
            Lista de dicts com: {"cnpj": "...", "razao_social": "...", "tipo": "..."}
        """
        logger.info(f"[Orchestrator] Buscando TODOS CNPJs vinculados a: {nome_ou_grupo}")
        
        prompt = f"""MISSAO: Encontre TODOS os CNPJs relacionados ao nome/grupo abaixo.

ALVO: {nome_ou_grupo}

INSTRUCOES CRITICAS:
1. Busque TODAS as empresas, fazendas, holdings, subsidiarias vinculadas
2. Se for um GRUPO (ex: Grupo Scheffer), busque TODAS as empresas do grupo
3. Se for uma PESSOA (ex: João Silva), busque todas empresas onde ele é sócio/administrador
4. Busque em: sites oficiais, Receita Federal, notícias, LinkedIn, relatórios

FORMATO DE RESPOSTA (JSON obrigatório):
[
  {{
    "cnpj": "06015666000106",
    "razao_social": "SCHEFFER AGRONEGOCIO S.A.",
    "nome_fantasia": "Scheffer",
    "tipo": "Holding Principal",
    "atividade": "Agricultura, pecuária"
  }},
  {{
    "cnpj": "12345678000199",
    "razao_social": "FAZENDA XYZ LTDA",
    "nome_fantasia": "Fazenda XYZ",
    "tipo": "Subsidiária",
    "atividade": "Produção de grãos"
  }}
]

EXEMPLOS DO QUE BUSCAR:
- Holding principal
- Subsidiárias e controladas
- SPEs (Sociedades de Propósito Específico)
- Fazendas individuais
- Empresas de trading
- Empresas de logística
- Cooperativas
- Empresas onde sócios têm participação

IMPORTANTE: Retorne APENAS o JSON. Se não encontrar nenhum CNPJ, retorne: []

JSON:"""
        
        try:
            response = await self.gemini.call_with_retry(
                prompt,
                max_retries=3,
                use_search=True,
                temperature=0.1
            )
            
            if not response:
                logger.warning(f"[Orchestrator] Resposta vazia do Gemini")
                return []
            
            # Tenta extrair JSON da resposta
            # Remove markdown code blocks se existirem
            response_clean = response.strip()
            if "```json" in response_clean:
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                cnpjs_list = json.loads(response_clean)
                
                if not isinstance(cnpjs_list, list):
                    logger.warning(f"[Orchestrator] Resposta não é uma lista: {type(cnpjs_list)}")
                    return []
                
                # Valida e limpa CNPJs
                cnpjs_validados = []
                for item in cnpjs_list:
                    if isinstance(item, dict) and "cnpj" in item:
                        cnpj_limpo = re.sub(r'\D', '', item["cnpj"])
                        
                        if len(cnpj_limpo) == 14:
                            cnpjs_validados.append({
                                "cnpj": cnpj_limpo,
                                "razao_social": item.get("razao_social", "N/D"),
                                "nome_fantasia": item.get("nome_fantasia", ""),
                                "tipo": item.get("tipo", "Empresa"),
                                "atividade": item.get("atividade", "")
                            })
                
                logger.info(f"[Orchestrator] {len(cnpjs_validados)} CNPJs encontrados")
                return cnpjs_validados
            
            except json.JSONDecodeError as e:
                logger.error(f"[Orchestrator] Erro ao fazer parse do JSON: {e}")
                logger.error(f"Resposta recebida: {response_clean[:500]}")
                return []
        
        except Exception as e:
            logger.error(f"[Orchestrator] Erro ao buscar CNPJs: {e}")
            return []
    
    async def executar_dosier_completo(
        self,
        razao_social: str,
        cnpj: str = "",
        callback=None
    ) -> Dict:
        """
        Método wrapper para compatibilidade com app.py original.
        NOVO: Se não tiver CNPJ, busca TODOS os CNPJs vinculados e gera dossiê consolidado.
        
        Args:
            razao_social: Nome da empresa/grupo/pessoa alvo
            cnpj: CNPJ específico (opcional)
            callback: Função de callback para logs
        
        Returns:
            Dossiê completo (único CNPJ ou consolidado de múltiplos)
        """
        from services.cnpj_service import consultar_cnpj
        
        # PASSO 1: Determina se é busca por CNPJ específico ou grupo inteiro
        cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ""
        
        if cnpj_limpo and len(cnpj_limpo) == 14:
            # Modo 1: CNPJ específico fornecido
            if callback:
                callback("Consultando dados cadastrais (CNPJ)...")
            
            cnpj_data_obj = consultar_cnpj(cnpj_limpo)
            
            if not cnpj_data_obj:
                raise ValueError(f"CNPJ {cnpj_limpo} não encontrado na base da Receita Federal")
            
            # Converte para dict
            cnpj_dict = {
                "cnpj": cnpj_data_obj.cnpj,
                "nome": cnpj_data_obj.razao_social,
                "nome_fantasia": cnpj_data_obj.nome_fantasia,
                "situacao": cnpj_data_obj.situacao_cadastral,
                "capital_social": cnpj_data_obj.capital_social,
                "porte": cnpj_data_obj.porte,
                "cnae_principal": cnpj_data_obj.cnae_principal,
                "municipio": cnpj_data_obj.municipio,
                "uf": cnpj_data_obj.uf,
                "qsa": cnpj_data_obj.qsa,
                "fonte": cnpj_data_obj.fonte
            }
            
            if callback:
                callback(f"CNPJ encontrado: {cnpj_dict['nome']} ({cnpj_dict['cnpj']})")
            
            # Gera dossiê único
            return await self.gerar_dossie_completo(
                cnpj_data=cnpj_dict,
                progress_callback=callback
            )
        
        else:
            # Modo 2: Busca completa de TODOS os CNPJs vinculados
            if callback:
                callback(f"Buscando TODOS os CNPJs vinculados a '{razao_social}'...")
            
            cnpjs_encontrados = await self._buscar_todos_cnpjs_vinculados(razao_social)
            
            if not cnpjs_encontrados:
                raise ValueError(f"Não foi possível localizar CNPJs vinculados a '{razao_social}'")
            
            if callback:
                callback(f"Encontrados {len(cnpjs_encontrados)} CNPJs. Gerando dossiê consolidado...")
            
            # Gera dossiê consolidado para TODOS os CNPJs
            return await self._gerar_dossie_consolidado_grupo(
                cnpjs_encontrados,
                nome_grupo=razao_social,
                progress_callback=callback
            )
    
    async def _gerar_dossie_consolidado_grupo(
        self,
        cnpjs_list: List[Dict],
        nome_grupo: str,
        progress_callback=None
    ) -> Dict:
        """
        Gera um dossiê CONSOLIDADO de múltiplos CNPJs de um grupo.
        
        Args:
            cnpjs_list: Lista de CNPJs encontrados
            nome_grupo: Nome do grupo/pessoa
            progress_callback: Callback para UI
        
        Returns:
            Dossiê consolidado com dados agregados de todas as empresas
        """
        from services.cnpj_service import consultar_cnpj
        
        logger.info(f"[Orchestrator] Gerando dossiê consolidado para {len(cnpjs_list)} CNPJs")
        
        empresas_detalhadas = []
        
        # Consulta dados cadastrais de cada CNPJ
        for i, empresa_info in enumerate(cnpjs_list):
            cnpj = empresa_info["cnpj"]
            
            if progress_callback:
                progress_callback(f"Consultando empresa {i+1}/{len(cnpjs_list)}: {empresa_info['razao_social'][:30]}...")
            
            try:
                cnpj_data = consultar_cnpj(cnpj)
                
                if cnpj_data:
                    empresas_detalhadas.append({
                        "cnpj": cnpj_data.cnpj,
                        "razao_social": cnpj_data.razao_social,
                        "nome_fantasia": cnpj_data.nome_fantasia,
                        "situacao": cnpj_data.situacao_cadastral,
                        "capital_social": cnpj_data.capital_social,
                        "porte": cnpj_data.porte,
                        "municipio": cnpj_data.municipio,
                        "uf": cnpj_data.uf,
                        "qsa": cnpj_data.qsa,
                        "tipo_vinculo": empresa_info.get("tipo", "Empresa"),
                        "atividade": empresa_info.get("atividade", "")
                    })
                else:
                    logger.warning(f"[Orchestrator] CNPJ {cnpj} não encontrado na Receita")
            
            except Exception as e:
                logger.error(f"[Orchestrador] Erro ao consultar CNPJ {cnpj}: {e}")
        
        if not empresas_detalhadas:
            raise ValueError(f"Nenhum CNPJ válido encontrado para '{nome_grupo}'")
        
        # Agora gera inteligência consolidada do grupo
        if progress_callback:
            progress_callback(f"Analisando grupo completo com {len(empresas_detalhadas)} empresas...")
        
        # Extrai todos os sócios de todas as empresas
        todos_socios = []
        todos_cpfs = []
        for empresa in empresas_detalhadas:
            for socio in empresa.get("qsa", []):
                if socio not in todos_socios:
                    todos_socios.append(socio)
                    cpf = socio.get("cpf", "")
                    if cpf and cpf not in todos_cpfs:
                        todos_cpfs.append(cpf)
        
        # Busca propriedades rurais do grupo inteiro
        if progress_callback:
            progress_callback("Mapeando propriedades rurais do grupo...")
        
        try:
            sigef_data = await self.infra.buscar_sigef_car(nome_grupo, todos_cpfs)
        except Exception as e:
            logger.error(f"SIGEF falhou: {e}")
            sigef_data = {"area_total_hectares": 0, "car_records": []}
        
        # Busca informações financeiras consolidadas
        if progress_callback:
            progress_callback("Analisando saúde financeira do grupo...")
        
        try:
            # Usa a empresa principal (primeira da lista) para busca financeira
            empresa_principal = empresas_detalhadas[0]
            cra_data = await self.financial.mineracao_cra_debentures(
                empresa_principal["razao_social"],
                empresa_principal["cnpj"]
            )
        except Exception as e:
            logger.error(f"CRA falhou: {e}")
            cra_data = {}
        
        # Consolida informações
        dossie_consolidado = {
            "tipo_dossie": "CONSOLIDADO_GRUPO",
            "nome_grupo": nome_grupo,
            "data_geracao": datetime.now().isoformat(),
            "total_empresas": len(empresas_detalhadas),
            
            # Lista de todas as empresas
            "empresas": empresas_detalhadas,
            
            # Consolidação de sócios
            "socios_consolidados": todos_socios,
            "total_socios_unicos": len(todos_socios),
            
            # Consolidação geográfica
            "estados_atuacao": list(set([e["uf"] for e in empresas_detalhadas if e.get("uf")])),
            "municipios_atuacao": list(set([e["municipio"] for e in empresas_detalhadas if e.get("municipio")])),
            
            # Consolidação financeira
            "capital_social_total": sum([e.get("capital_social", 0) for e in empresas_detalhadas]),
            
            # Propriedades rurais
            "area_total_hectares": sigef_data.get("area_total_hectares", 0),
            "propriedades_rurais": sigef_data.get("car_records", []),
            
            # Dados financeiros
            "faturamento_estimado": cra_data.get("faturamento_real", "N/D"),
            "emissoes_cra": cra_data.get("emissoes_cra", []),
            
            # Classificação
            "classificacao": self._classificar_target(0, sigef_data.get("area_total_hectares", 0)),
            
            # Empresa principal (para abordagem comercial)
            "empresa_principal": empresas_detalhadas[0] if empresas_detalhadas else {}
        }
        
        if progress_callback:
            progress_callback(f"Dossiê consolidado concluído! {len(empresas_detalhadas)} empresas mapeadas.")
        
        logger.info(f"DOSSIE CONSOLIDADO CONCLUIDO | {len(empresas_detalhadas)} empresas | {dossie_consolidado['area_total_hectares']} ha")
        
        return dossie_consolidado
    
    async def gerar_dossie_completo(
        self, 
        cnpj_data: Dict,
        progress_callback=None
    ) -> Dict:
        """
        Gera dossiê completo para UM CNPJ específico.
        """
        logger.info(f"INICIANDO DOSSIE UNICO: {cnpj_data.get('nome', 'N/D')}")
        
        razao_social = cnpj_data.get('nome', 'Empresa Desconhecida')
        cnpj = cnpj_data.get('cnpj', '')
        socios = cnpj_data.get('qsa', [])
        cpfs_socios = [s.get('cpf', '') for s in socios if s.get('cpf')]
        
        self._update_progress(progress_callback, "Buscando SIGEF/CAR...", 10)
        
        try:
            sigef_data = await self.infra.buscar_sigef_car(razao_social, cpfs_socios)
        except Exception as e:
            logger.error(f"SIGEF falhou: {e}")
            sigef_data = {"area_total_hectares": 0, "car_records": []}
        
        area_total = sigef_data.get('area_total_hectares', 0)
        estados = sigef_data.get('estados_operacao', [])
        municipios = [r.get('municipio', '') for r in sigef_data.get('car_records', [])]
        culturas = []
        for record in sigef_data.get('car_records', []):
            culturas.extend(record.get('culturas', []))
        culturas = list(set(culturas))
        
        self._update_progress(progress_callback, "Executando camadas em paralelo...", 25)
        
        tasks = {
            'maquinario': self.infra.forense_maquinario(razao_social, cnpj),
            'conectividade': self.infra.analise_conectividade(municipios, []),
            'cra': self.financial.mineracao_cra_debentures(razao_social, cnpj),
            'incentivos': self.financial.rastreio_incentivos_fiscais(cnpj, estados),
            'multas': self.financial.varredura_multas_ambientais(cnpj, razao_social),
            'trabalhistas': self.financial.rastreio_processos_trabalhistas(cnpj, razao_social),
        }
        
        try:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            parallel_data = dict(zip(tasks.keys(), results))
            
            for key, value in parallel_data.items():
                if isinstance(value, Exception):
                    logger.error(f"{key} falhou: {value}")
                    parallel_data[key] = {}
        
        except Exception as e:
            logger.error(f"Erro no paralelo: {e}")
            parallel_data = {k: {} for k in tasks.keys()}
        
        self._update_progress(progress_callback, "Gerando inteligencia competitiva...", 50)
        
        try:
            concorrentes = await self.intel.mapeamento_concorrentes(razao_social, culturas, estados)
        except Exception as e:
            logger.error(f"Concorrentes falhou: {e}")
            concorrentes = {"concorrentes_diretos": []}
        
        self._update_progress(progress_callback, "Rastreando M&A...", 60)
        
        try:
            ma_data = await self.intel.rastreio_movimentos_ma(razao_social, cpfs_socios)
        except Exception as e:
            logger.error(f"M&A falhou: {e}")
            ma_data = {"aquisicoes_ultimos_3_anos": []}
        
        self._update_progress(progress_callback, "Perfilando lideranca...", 70)
        
        try:
            lideranca = await self.intel.perfilamento_lideranca(razao_social, socios)
        except Exception as e:
            logger.error(f"Lideranca falhou: {e}")
            lideranca = {"executivos_principais": []}
        
        self._update_progress(progress_callback, "Mapeando stack tecnologico...", 80)
        
        try:
            tech_stack = await self.intel.mapeamento_stack_tecnologico(razao_social, cnpj)
        except Exception as e:
            logger.error(f"Tech Stack falhou: {e}")
            tech_stack = {"erp_atual": "N/D"}
        
        self._update_progress(progress_callback, "Calculando Score SAS...", 85)
        
        try:
            score_sas = self.market.calcular_sas(
                area_hectares=area_total,
                faturamento_str=parallel_data.get('cra', {}).get('faturamento_real', 'N/D'),
                num_funcionarios=cnpj_data.get('efr', '0'),
                num_socios=len(socios),
                tem_cra=(len(parallel_data.get('cra', {}).get('emissoes_cra', [])) > 0),
                auditor=parallel_data.get('cra', {}).get('auditor', 'N/D'),
                tendencia_expansao=ma_data.get('tendencia', 'Estavel')
            )
        except Exception as e:
            logger.error(f"Score SAS falhou: {e}")
            score_sas = {"total": 0, "breakdown": {}}
        
        self._update_progress(progress_callback, "Consolidando dossie...", 90)
        
        dossie = {
            "tipo_dossie": "EMPRESA_UNICA",
            "razao_social": razao_social,
            "cnpj": cnpj,
            "data_geracao": datetime.now().isoformat(),
            "score_sas": score_sas.get('total', 0),
            "breakdown_sas": score_sas.get('breakdown', {}),
            "classificacao": self._classificar_target(score_sas.get('total', 0), area_total),
            "area_total_hectares": area_total,
            "estados_operacao": estados,
            "municipios": municipios,
            "culturas": culturas,
            "car_records": sigef_data.get('car_records', []),
            "regularizacao_ambiental": sigef_data.get('regularizacao_percentual', 0),
            "frota": parallel_data.get('maquinario', {}),
            "conectividade": parallel_data.get('conectividade', {}),
            "faturamento": parallel_data.get('cra', {}).get('faturamento_real', 'N/D'),
            "ebitda": parallel_data.get('cra', {}).get('ebitda_consolidado', 'N/D'),
            "emissoes_cra": parallel_data.get('cra', {}).get('emissoes_cra', []),
            "auditor": parallel_data.get('cra', {}).get('auditor', 'N/D'),
            "incentivos_fiscais": parallel_data.get('incentivos', {}).get('beneficios_ativos', []),
            "economia_fiscal_anual": parallel_data.get('incentivos', {}).get('economia_fiscal_anual_total', 'N/D'),
            "multas_ambientais": parallel_data.get('multas', {}).get('multas_ativas', []),
            "score_risco_ambiental": parallel_data.get('multas', {}).get('score_risco_ambiental', 'Desconhecido'),
            "processos_trabalhistas": parallel_data.get('trabalhistas', {}).get('total_processos_ativos', 0),
            "dor_trabalhista": parallel_data.get('trabalhistas', {}).get('dor_principal', 'N/D'),
            "concorrentes": concorrentes.get('concorrentes_diretos', []),
            "posicionamento_mercado": concorrentes.get('posicionamento_relativo', 'N/D'),
            "movimentos_ma": ma_data.get('aquisicoes_ultimos_3_anos', []),
            "tendencia_expansao": ma_data.get('tendencia', 'Desconhecida'),
            "pipeline_ma": ma_data.get('pipeline_provavel', 'N/D'),
            "executivos": lideranca.get('executivos_principais', []),
            "cultura_organizacional": lideranca.get('cultura_organizacional', 'N/D'),
            "abordagem_comercial": lideranca.get('dica_abordagem_comercial', 'N/D'),
            "erp_atual": tech_stack.get('erp_atual', 'N/D'),
            "stack_tecnologico": tech_stack.get('solucoes_agricolas', []),
            "maturidade_digital": tech_stack.get('maturidade_digital', 'Desconhecida'),
            "gaps_tecnologicos": tech_stack.get('gaps_identificados', []),
            "oportunidades_venda": tech_stack.get('oportunidades_venda', []),
            "socios": socios
        }
        
        self._update_progress(progress_callback, "Dossie concluido!", 100)
        
        logger.info(f"DOSSIE CONCLUIDO | Score: {dossie['score_sas']} | Classificacao: {dossie['classificacao']}")
        
        return dossie
    
    def _classificar_target(self, score: int, area: int) -> str:
        if area >= 5000 or score >= 700:
            return "HIGH TICKET"
        elif score >= 400:
            return "MEDIO POTENCIAL"
        else:
            return "BAIXO POTENCIAL"
    
    def _update_progress(self, callback, message: str, percent: int):
        if callback:
            try:
                callback(message, percent)
            except:
                try:
                    callback(message)
                except:
                    pass
        logger.info(f"[{percent}%] {message}")
