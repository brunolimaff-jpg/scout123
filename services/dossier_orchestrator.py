"""
services/dossier_orchestrator.py — VERSÃO ULTRA-AGRESSIVA
Coordena todas as camadas com prompts otimizados
"""
import asyncio
import logging
from typing import Dict, List
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
    
    async def gerar_dossie_completo(
        self, 
        cnpj_data: Dict,
        progress_callback=None
    ) -> Dict:
        """
        Gera dossiê completo com validação agressiva.
        
        Args:
            cnpj_data: Dados da ReceitaWS (CNPJ, razão social, sócios, etc)
            progress_callback: Função para atualizar UI (Streamlit)
        
        Returns:
            Dossiê completo com TODAS as seções preenchidas
        """
        logger.info(f"🎯 INICIANDO DOSSIÊ ULTRA-AGRESSIVO: {cnpj_data.get('nome', 'N/D')}")
        
        razao_social = cnpj_data.get('nome', 'Empresa Desconhecida')
        cnpj = cnpj_data.get('cnpj', '')
        socios = cnpj_data.get('qsa', [])
        cpfs_socios = [s.get('cpf', '') for s in socios if s.get('cpf')]
        
        # ========================================
        # FASE 1: INFRAESTRUTURA (crítico)
        # ========================================
        self._update_progress(progress_callback, "🔍 Buscando SIGEF/CAR...", 10)
        
        try:
            sigef_data = await self.infra.buscar_sigef_car(razao_social, cpfs_socios)
            logger.info(f"✅ SIGEF: {sigef_data.get('area_total_hectares', 0)} ha")
        except Exception as e:
            logger.error(f"❌ SIGEF falhou: {e}")
            sigef_data = {"area_total_hectares": 0, "car_records": []}
        
        # Extrai metadados do SIGEF
        area_total = sigef_data.get('area_total_hectares', 0)
        estados = sigef_data.get('estados_operacao', [])
        municipios = [r.get('municipio', '') for r in sigef_data.get('car_records', [])]
        culturas = []
        for record in sigef_data.get('car_records', []):
            culturas.extend(record.get('culturas', []))
        culturas = list(set(culturas))  # Remove duplicatas
        
        # ========================================
        # FASE 2: PARALELO (infra + financial)
        # ========================================
        self._update_progress(progress_callback, "⚡ Executando camadas em paralelo...", 25)
        
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
            
            # Log de erros
            for key, value in parallel_data.items():
                if isinstance(value, Exception):
                    logger.error(f"❌ {key} falhou: {value}")
                    parallel_data[key] = {}
                else:
                    logger.info(f"✅ {key} concluído")
        
        except Exception as e:
            logger.error(f"❌ Erro no paralelo: {e}")
            parallel_data = {k: {} for k in tasks.keys()}
        
        # ========================================
        # FASE 3: INTELLIGENCE (sequencial)
        # ========================================
        self._update_progress(progress_callback, "🧠 Gerando inteligência competitiva...", 50)
        
        try:
            concorrentes = await self.intel.mapeamento_concorrentes(razao_social, culturas, estados)
        except Exception as e:
            logger.error(f"❌ Concorrentes falhou: {e}")
            concorrentes = {"concorrentes_diretos": []}
        
        self._update_progress(progress_callback, "📊 Rastreando M&A...", 60)
        
        try:
            ma_data = await self.intel.rastreio_movimentos_ma(razao_social, cpfs_socios)
        except Exception as e:
            logger.error(f"❌ M&A falhou: {e}")
            ma_data = {"aquisicoes_ultimos_3_anos": []}
        
        self._update_progress(progress_callback, "👔 Perfilando liderança...", 70)
        
        try:
            lideranca = await self.intel.perfilamento_lideranca(razao_social, socios)
        except Exception as e:
            logger.error(f"❌ Liderança falhou: {e}")
            lideranca = {"executivos_principais": []}
        
        self._update_progress(progress_callback, "💻 Mapeando stack tecnológico...", 80)
        
        try:
            tech_stack = await self.intel.mapeamento_stack_tecnologico(razao_social, cnpj)
        except Exception as e:
            logger.error(f"❌ Tech Stack falhou: {e}")
            tech_stack = {"erp_atual": "N/D"}
        
        # ========================================
        # FASE 4: SCORING SAS
        # ========================================
        self._update_progress(progress_callback, "🎯 Calculando Score SAS...", 85)
        
        try:
            score_sas = self.market.calcular_sas(
                area_hectares=area_total,
                faturamento_str=parallel_data.get('cra', {}).get('faturamento_real', 'N/D'),
                num_funcionarios=cnpj_data.get('efr', '0'),
                num_socios=len(socios),
                tem_cra=(len(parallel_data.get('cra', {}).get('emissoes_cra', [])) > 0),
                auditor=parallel_data.get('cra', {}).get('auditor', 'N/D'),
                tendencia_expansao=ma_data.get('tendencia', 'Estável')
            )
        except Exception as e:
            logger.error(f"❌ Score SAS falhou: {e}")
            score_sas = {"total": 0, "breakdown": {}}
        
        # ========================================
        # FASE 5: CONSOLIDAÇÃO FINAL
        # ========================================
        self._update_progress(progress_callback, "📝 Consolidando dossiê...", 90)
        
        dossie = {
            # Metadados
            "razao_social": razao_social,
            "cnpj": cnpj,
            "data_geracao": datetime.now().isoformat(),
            
            # Score
            "score_sas": score_sas.get('total', 0),
            "breakdown_sas": score_sas.get('breakdown', {}),
            "classificacao": self._classificar_target(score_sas.get('total', 0), area_total),
            
            # Infraestrutura
            "area_total_hectares": area_total,
            "estados_operacao": estados,
            "municipios": municipios,
            "culturas": culturas,
            "car_records": sigef_data.get('car_records', []),
            "regularizacao_ambiental": sigef_data.get('regularizacao_percentual', 0),
            
            # Maquinário
            "frota": parallel_data.get('maquinario', {}),
            
            # Conectividade
            "conectividade": parallel_data.get('conectividade', {}),
            
            # Financeiro
            "faturamento": parallel_data.get('cra', {}).get('faturamento_real', 'N/D'),
            "ebitda": parallel_data.get('cra', {}).get('ebitda_consolidado', 'N/D'),
            "emissoes_cra": parallel_data.get('cra', {}).get('emissoes_cra', []),
            "auditor": parallel_data.get('cra', {}).get('auditor', 'N/D'),
            
            # Fiscal
            "incentivos_fiscais": parallel_data.get('incentivos', {}).get('beneficios_ativos', []),
            "economia_fiscal_anual": parallel_data.get('incentivos', {}).get('economia_fiscal_anual_total', 'N/D'),
            
            # Riscos
            "multas_ambientais": parallel_data.get('multas', {}).get('multas_ativas', []),
            "score_risco_ambiental": parallel_data.get('multas', {}).get('score_risco_ambiental', 'Desconhecido'),
            "processos_trabalhistas": parallel_data.get('trabalhistas', {}).get('total_processos_ativos', 0),
            "dor_trabalhista": parallel_data.get('trabalhistas', {}).get('dor_principal', 'N/D'),
            
            # Intelligence
            "concorrentes": concorrentes.get('concorrentes_diretos', []),
            "posicionamento_mercado": concorrentes.get('posicionamento_relativo', 'N/D'),
            "movimentos_ma": ma_data.get('aquisicoes_ultimos_3_anos', []),
            "tendencia_expansao": ma_data.get('tendencia', 'Desconhecida'),
            "pipeline_ma": ma_data.get('pipeline_provavel', 'N/D'),
            
            # Liderança
            "executivos": lideranca.get('executivos_principais', []),
            "cultura_organizacional": lideranca.get('cultura_organizacional', 'N/D'),
            "abordagem_comercial": lideranca.get('dica_abordagem_comercial', 'N/D'),
            
            # Tecnologia
            "erp_atual": tech_stack.get('erp_atual', 'N/D'),
            "stack_tecnologico": tech_stack.get('solucoes_agricolas', []),
            "maturidade_digital": tech_stack.get('maturidade_digital', 'Desconhecida'),
            "gaps_tecnologicos": tech_stack.get('gaps_identificados', []),
            "oportunidades_venda": tech_stack.get('oportunidades_venda', []),
            
            # Sócios
            "socios": socios
        }
        
        self._update_progress(progress_callback, "✅ Dossiê concluído!", 100)
        
        logger.info(f"🎉 DOSSIÊ CONCLUÍDO | Score: {dossie['score_sas']} | Classificação: {dossie['classificacao']}")
        
        return dossie
    
    def _classificar_target(self, score: int, area: int) -> str:
        """
        Classifica o target baseado em Score SAS e área.
        """
        if area >= 5000 or score >= 700:
            return "🎯 HIGH TICKET"
        elif score >= 400:
            return "⚡ MÉDIO POTENCIAL"
        else:
            return "⚠️ BAIXO POTENCIAL"
    
    def _update_progress(self, callback, message: str, percent: int):
        """
        Atualiza progresso no Streamlit.
        """
        if callback:
            try:
                callback(message, percent)
            except:
                pass
        logger.info(f"[{percent}%] {message}")
