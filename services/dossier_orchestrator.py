"""
RADAR FOX-3 - Orchestrator v2.0
Pipeline de 15 passos com 5 camadas de inteligência estruturada.
"""

import asyncio
import logging
from typing import Callable, Optional, Dict, List
from datetime import datetime
import json

# Importações de camadas
from services.cnpj_service import CNPJService
from services.infrastructure_layer import InfrastructureLayer
from services.financial_layer import FinancialLayer
from services.supply_chain_layer import SupplyChainLayer
from services.tech_people_layer import TechPeopleLayer
from services.critical_validator import CriticalValidator
from services.family_office_layer import FamilyOfficeLayer
from services.gemini_service import GeminiService
from services.market_estimator import MarketEstimator
from services.data_validator import safe_float, safe_int, safe_str

logger = logging.getLogger(__name__)

class DossierOrchestrator:
    """
    Orquestrador central do RADAR FOX-3.
    Executa 15 passos estruturados em 5 camadas:
    
    CAMADA 1: Infraestrutura (Hard Assets)
    - SIGEF/CAR
    - Maquinário
    - Conectividade
    
    CAMADA 2: Financeira (Follow the Money)
    - CRA/Debêntures
    - Incentivos Fiscais
    - Multas Ambientais
    - Processos Trabalhistas
    
    CAMADA 3: Supply Chain
    - Exportação
    - Bioinsumos
    
    CAMADA 4: Tecnologia & Pessoas
    - Tech Stack
    - E-mails/Decisores
    - Funcionários
    
    CAMADA 5: Validação Adversária
    - Crítico
    - PDFs
    - Family Office
    """
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini = gemini_service
        
        # Inicializa camadas
        self.cnpj_service = CNPJService(gemini_service)
        self.infra = InfrastructureLayer(gemini_service)
        self.financial = FinancialLayer(gemini_service)
        self.supply_chain = SupplyChainLayer(gemini_service)
        self.tech_people = TechPeopleLayer(gemini_service)
        self.critical = CriticalValidator(gemini_service)
        self.family_office = FamilyOfficeLayer(gemini_service)
        self.estimator = MarketEstimator()
    
    async def executar_dosier_completo(
        self, 
        razao_social: str, 
        cnpj: str, 
        callback: Optional[Callable] = None
    ) -> Dict:
        """
        Pipeline completo de 15 passos.
        
        Args:
            razao_social: Nome da empresa alvo
            cnpj: CNPJ da empresa
            callback: Função para logs de progresso
        
        Returns:
            Dossiê completo estruturado
        """
        
        logger.info(f"[ORCHESTRATOR] Iniciando dossiê completo para {razao_social}")
        
        dossie = {
            "empresa_alvo": razao_social,
            "cnpj": cnpj,
            "data_geracao": datetime.now().isoformat(),
            "versao": "2.0 - Intelligence System"
        }
        
        try:
            # ========== PASSO 1: VALIDAÇÃO CNPJ + QSA ==========
            self._log_passo(callback, 1, "🔍 Validando CNPJ e extraindo QSA...")
            qsa_data = await self.cnpj_service.obter_cnpj_e_qsa(cnpj)
            dossie['dados_cadastrais'] = qsa_data
            
            # Extrai CPFs e nomes de sócios para uso posterior
            cpfs_socios = [s.get('cpf', '') for s in qsa_data.get('quadro_societario', []) if s.get('cpf')]
            nomes_socios = [s.get('nome', '') for s in qsa_data.get('quadro_societario', []) if s.get('nome')]
            
            logger.info(f"[QSA] {len(nomes_socios)} sócios identificados")
            
            # ========== CAMADA 1: INFRAESTRUTURA (Hard Assets) ==========
            
            # PASSO 2: SIGEF/CAR
            self._log_passo(callback, 2, "🌍 Rastreando SIGEF/CAR (propriedades rurais)...")
            sigef_car = await self.infra.buscar_sigef_car(razao_social, cpfs_socios)
            dossie['sigef_car'] = sigef_car
            
            area_total = safe_int(sigef_car.get('area_total_hectares', 0))
            logger.info(f"[SIGEF/CAR] {area_total:,} ha mapeados")
            
            # PASSO 3: MAQUINÁRIO
            self._log_passo(callback, 3, "🚜 Forense de maquinário (frota agrícola)...")
            maquinario = await self.infra.forense_maquinario(razao_social, cnpj)
            dossie['maquinario'] = maquinario
            
            tratores = safe_int(maquinario.get('frota_estimada_total', {}).get('tratores', 0))
            logger.info(f"[MAQUINÁRIO] ~{tratores} tratores estimados")
            
            # PASSO 4: CONECTIVIDADE
            municipios = [r.get('municipio', '') for r in sigef_car.get('car_records', []) if r.get('municipio')]
            if municipios:
                self._log_passo(callback, 4, "📡 Analisando conectividade 4G/5G (Anatel)...")
                coordenadas = []  # Pode ser expandido com lat/long real
                conectividade = await self.infra.analise_conectividade(municipios, coordenadas)
                dossie['conectividade'] = conectividade
            else:
                logger.warning("[CONECTIVIDADE] Sem municípios para analisar")
                dossie['conectividade'] = {"analise_por_municipio": [], "status": "sem_dados"}
            
            # ========== CAMADA 2: FINANCEIRA & JURÍDICA (Follow the Money) ==========
            
            # PASSO 5: CRA/DEBÊNTURES
            self._log_passo(callback, 5, "💰 Minerando CRA/Debêntures (dados auditados)...")
            cra = await self.financial.mineracao_cra_debentures(razao_social, cnpj)
            dossie['cra_debentures'] = cra
            
            faturamento_real = safe_str(cra.get('faturamento_real', 'N/D'))
            logger.info(f"[CRA] Faturamento identificado: {faturamento_real}")
            
            # PASSO 6: INCENTIVOS FISCAIS
            estados_operacao = list(set([r.get('uf', '') for r in sigef_car.get('car_records', []) if r.get('uf')]))
            if estados_operacao:
                self._log_passo(callback, 6, "🏛️ Rastreando incentivos fiscais (SUDAM/SUDENE)...")
                incentivos = await self.financial.rastreio_incentivos_fiscais(cnpj, estados_operacao)
                dossie['incentivos_fiscais'] = incentivos
            else:
                dossie['incentivos_fiscais'] = {"beneficios_ativos": [], "status": "sem_estados"}
            
            # PASSO 7: MULTAS AMBIENTAIS
            self._log_passo(callback, 7, "🌳 Varredura de multas ambientais (Ibama/SEMA)...")
            multas = await self.financial.varredura_multas_ambientais(cnpj, razao_social)
            dossie['multas_ambientais'] = multas
            
            # PASSO 8: PROCESSOS TRABALHISTAS
            self._log_passo(callback, 8, "⚖️ Rastreando processos trabalhistas (TRT)...")
            trt = await self.financial.rastreio_processos_trabalhistas(cnpj, razao_social)
            dossie['processos_trabalhistas'] = trt
            
            total_processos = safe_int(trt.get('total_processos_ativos', 0))
            logger.info(f"[TRT] {total_processos} processos ativos")
            
            # ========== CAMADA 3: SUPPLY CHAIN ==========
            
            # PASSO 9: EXPORTAÇÃO
            self._log_passo(callback, 9, "🚢 Analisando exportações (Comexstat)...")
            exportacao = await self.supply_chain.analise_exportacao(razao_social, cnpj)
            dossie['exportacao'] = exportacao
            
            # PASSO 10: BIOINSUMOS
            self._log_passo(callback, 10, "🧪 Rastreando bioinsumos (MAPA/Biofábricas)...")
            bioinsumos = await self.supply_chain.analise_bioinsumos(razao_social, cnpj)
            dossie['bioinsumos'] = bioinsumos
            
            total_biofabricas = safe_int(bioinsumos.get('total_biofabricas', 0))
            logger.info(f"[BIOINSUMOS] {total_biofabricas} biofábricas identificadas")
            
            # ========== CAMADA 4: TECNOLOGIA & PESSOAS ==========
            
            # PASSO 11: TECH STACK (Vagas)
            self._log_passo(callback, 11, "💻 Scraping de tech stack (vagas de emprego)...")
            tech_stack = await self.tech_people.scraping_vagas_tech_stack(razao_social, cnpj)
            dossie['tech_stack_identificado'] = tech_stack
            
            erp_principal = safe_str(tech_stack.get('stack_consolidado', {}).get('ERP_Principal', 'N/D'))
            logger.info(f"[TECH STACK] ERP: {erp_principal}")
            
            # PASSO 12: E-MAILS & DECISORES
            self._log_passo(callback, 12, "📧 Mapeando e-mails e decisores...")
            dominio_email = f"{razao_social.lower().replace(' ', '').replace('-', '')}.com.br"
            emails = await self.tech_people.mapeamento_emails_e_decisores(razao_social, dominio_email)
            dossie['emails_decisores'] = emails
            
            total_emails = safe_int(emails.get('total_emails_validados', 0))
            logger.info(f"[E-MAILS] {total_emails} contatos validados")
            
            # PASSO 12.5: ESTIMATIVA DE FUNCIONÁRIOS
            self._log_passo(callback, 12.5, "👥 Estimando força de trabalho...")
            culturas = sigef_car.get('car_records', [{}])[0].get('culturas', ['Soja', 'Milho'])
            pecuaria_ha = 0  # Pode ser extraído de CAR se disponível
            
            funcionarios_est = await self.tech_people.estimar_funcionarios(
                razao_social, 
                area_total,
                culturas,
                pecuaria_ha
            )
            dossie['estimativa_funcionarios'] = funcionarios_est
            
            # ========== CAMADA 5: VALIDAÇÃO ADVERSÁRIA ==========
            
            # PASSO 13: VALIDAÇÃO CRÍTICA
            self._log_passo(callback, 13, "🔬 Validação adversária (agente crítico)...")
            
            # Consolida dados operacionais e financeiros para validação
            dossie['dados_operacionais'] = {
                "area_total": area_total,
                "culturas": culturas,
                "funcionarios_estimados": safe_int(funcionarios_est.get('total_funcionarios_estimado', 0))
            }
            
            dossie['dados_financeiros'] = {
                "faturamento_estimado": faturamento_real,
                "ebitda_ajustado": safe_str(cra.get('ebitda_consolidado', 'N/D')),
                "divida_total": safe_str(cra.get('indice_dps', 0)),
                "capital_social": safe_str(qsa_data.get('capital_social', 'N/D')),
                "total_processos_trabalhistas": total_processos,
                "debitos_ambientais_total": safe_str(multas.get('debitos_ambientais_total', 'N/D'))
            }
            
            dossie['tech_stack'] = {
                "erp_principal": erp_principal,
                "sistemas_campo": tech_stack.get('stack_consolidado', {}).get('Desenvolvimento', []),
                "maturidade_ti": safe_str(tech_stack.get('maturidade_ti', 'N/D'))
            }
            
            validacoes = await self.critical.validar_consistencia_dados(dossie)
            dossie['validacoes_criticas'] = validacoes
            
            # PASSO 14: PARSING DE PDFs
            self._log_passo(callback, 14, "📄 Extraindo PDFs e documentos primários...")
            pdfs_docs = await self.critical.extrair_pdfs_documentos(razao_social)
            dossie['documentos_primarios'] = pdfs_docs
            
            # PASSO 15: FAMILY OFFICE
            if cpfs_socios and nomes_socios:
                self._log_passo(callback, 15, "🏦 Mapeando Family Office dos sócios...")
                family_office = await self.family_office.mapear_family_office(cpfs_socios, nomes_socios)
                dossie['family_office'] = family_office
            else:
                dossie['family_office'] = {"socios_estrutura": [], "status": "sem_socios"}
            
            # ========== ANÁLISE ESTRATÉGICA ==========
            self._log_passo(callback, 16, "🎯 Gerando análise estratégica...")
            analise = await self._gerar_analise_estrategica(dossie, razao_social)
            dossie['analise_estrategica'] = analise
            
            # ========== CÁLCULO DO SCORE SAS ==========
            self._log_passo(callback, 17, "📊 Calculando Score SAS...")
            sas_result = self._calcular_sas_score(dossie)
            dossie['sas_score'] = sas_result.get('score', 0)
            dossie['sas_tier'] = sas_result.get('tier', 'Bronze')
            dossie['sas_breakdown'] = sas_result.get('breakdown', {})
            
            logger.info(f"[DOSSIÊ COMPLETO] Score SAS: {dossie['sas_score']} ({dossie['sas_tier']})")
            
            return dossie
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Erro fatal: {e}", exc_info=True)
            dossie['erro'] = str(e)
            dossie['status'] = 'erro_critico'
            return dossie
    
    def _log_passo(self, callback: Optional[Callable], num_passo: float, mensagem: str):
        """Log unificado com callback."""
        log_msg = f"[PASSO {num_passo:.1f}] {mensagem}"
        logger.info(log_msg)
        if callback:
            callback(log_msg)
    
    async def _gerar_analise_estrategica(self, dossie: Dict, razao_social: str) -> Dict:
        """
        Gera análise estratégica em 4 seções baseada nas 5 camadas.
        """
        logger.info("[ANÁLISE ESTRATÉGICA] Sintetizando inteligência...")
        
        # Consolida contexto
        area_total = safe_int(dossie.get('dados_operacionais', {}).get('area_total', 0))
        faturamento = safe_str(dossie.get('dados_financeiros', {}).get('faturamento_estimado', 'N/D'))
        erp = safe_str(dossie.get('tech_stack', {}).get('erp_principal', 'N/D'))
        processos_trab = safe_int(dossie.get('processos_trabalhistas', {}).get('total_processos_ativos', 0))
        biofabricas = safe_int(dossie.get('bioinsumos', {}).get('total_biofabricas', 0))
        multas = safe_str(dossie.get('multas_ambientais', {}).get('debitos_ambientais_total', 'N/D'))
        
        prompt = f"""Você é um estrategista comercial sênior da Senior Sistemas voltado ao agronegócio.

ALVO: {razao_social}

INTELIGÊNCIA CONSOLIDADA:
- Área Total: {area_total:,} ha
- Faturamento Auditado: {faturamento}
- ERP Atual: {erp}
- Processos Trabalhistas: {processos_trab}
- Biofábricas: {biofabricas}
- Multas Ambientais: {multas}

GERE ANÁLISE TÁTICA EM 4 SEÇÕES:

1. QUEM É ESTA EMPRESA? (Reconhecimento do Alvo)
   - Porte, sofisticação, modelo de negócio
   - Verticalização e integração
   - Posição de mercado

2. DORES & COMPLEXIDADE
   - Problemas operacionais identificados
   - Gargalos tecnológicos
   - Riscos (trabalhistas, ambientais, financeiros)
   - Áreas críticas de melhoria

3. ARSENAL RECOMENDADO (Fit com Senior/GAtec)
   - Produtos Senior aplicáveis
   - Módulos prioritários
   - Valor agregado por solução
   - ROI esperado

4. PLANO DE ATAQUE
   - Stakeholders-chave para abordagem
   - Mensagem de valor personalizada
   - Próximos passos táticos
   - Timeline sugerido

RETORNE JSON:
{{
    "quem_e_empresa": "Texto markdown de 3-5 parágrafos",
    "complexidade_dores": "Texto markdown listando dores e evidências",
    "arsenal_recomendado": "Texto markdown com produtos Senior + argumentação",
    "plano_ataque": "Texto markdown com roadmap comercial passo a passo"
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            return data
        except Exception as e:
            logger.error(f"[ANÁLISE ESTRATÉGICA] Erro: {e}")
            return {
                "quem_e_empresa": "Análise indisponível",
                "complexidade_dores": "Análise indisponível",
                "arsenal_recomendado": "Análise indisponível",
                "plano_ataque": "Análise indisponível"
            }
    
    def _calcular_sas_score(self, dossie: Dict) -> Dict:
        """
        Calcula Score SAS (Senior Agriculture Score) baseado nas 5 camadas.
        
        Dimensões:
        - Músculo (Porte): 300 pontos
        - Complexidade (Sofisticação): 250 pontos
        - Gente (Gestão/Finanças): 250 pontos
        - Momento (Tech/Mercado): 200 pontos
        
        Total: 1000 pontos
        """
        logger.info("[SAS SCORE] Calculando...")
        
        score_musculo = 0
        score_complexidade = 0
        score_gente = 0
        score_momento = 0
        
        # === MÚSCULO (Porte) - 300 pts ===
        area_total = safe_int(dossie.get('dados_operacionais', {}).get('area_total', 0))
        if area_total >= 200000:
            score_musculo = 300
        elif area_total >= 100000:
            score_musculo = 250
        elif area_total >= 50000:
            score_musculo = 200
        elif area_total >= 20000:
            score_musculo = 150
        elif area_total >= 10000:
            score_musculo = 100
        else:
            score_musculo = 50
        
        # === COMPLEXIDADE (Sofisticação) - 250 pts ===
        biofabricas = safe_int(dossie.get('bioinsumos', {}).get('total_biofabricas', 0))
        complexidade_pts = 0
        
        if biofabricas >= 3:
            complexidade_pts += 80
        elif biofabricas >= 1:
            complexidade_pts += 50
        
        # Verticalização
        volume_exportado = safe_str(dossie.get('exportacao', {}).get('volume_total_exportado_2024', '0'))
        if '000 ton' in volume_exportado or 'mil ton' in volume_exportado:
            complexidade_pts += 60
        
        # Incentivos fiscais
        economia_fiscal = safe_str(dossie.get('incentivos_fiscais', {}).get('economia_fiscal_anual_total', 'R$ 0'))
        if 'milhões' in economia_fiscal or 'bilhão' in economia_fiscal:
            complexidade_pts += 50
        
        # Máquinas modernas
        tratores = safe_int(dossie.get('maquinario', {}).get('frota_estimada_total', {}).get('tratores', 0))
        if tratores >= 100:
            complexidade_pts += 60
        elif tratores >= 50:
            complexidade_pts += 40
        
        score_complexidade = min(complexidade_pts, 250)
        
        # === GENTE (Gestão/Finanças) - 250 pts ===
        gente_pts = 0
        
        # Balanço auditado (CRA)
        faturamento = safe_str(dossie.get('dados_financeiros', {}).get('faturamento_estimado', 'N/D'))
        if faturamento != 'N/D' and 'bilhão' in faturamento.lower():
            gente_pts += 100
        elif faturamento != 'N/D' and 'milhões' in faturamento.lower():
            gente_pts += 60
        
        # Processos trabalhistas baixos
        processos = safe_int(dossie.get('processos_trabalhistas', {}).get('total_processos_ativos', 0))
        if processos < 50:
            gente_pts += 50
        elif processos < 100:
            gente_pts += 30
        
        # Multas ambientais baixas
        multas = safe_str(dossie.get('multas_ambientais', {}).get('debitos_ambientais_total', 'N/D'))
        if multas == 'N/D' or 'R$ 0' in multas:
            gente_pts += 50
        elif 'milhão' in multas:
            gente_pts += 20
        
        # Decisores mapeados
        emails = safe_int(dossie.get('emails_decisores', {}).get('total_emails_validados', 0))
        if emails >= 20:
            gente_pts += 50
        elif emails >= 10:
            gente_pts += 30
        
        score_gente = min(gente_pts, 250)
        
        # === MOMENTO (Tech/Mercado) - 200 pts ===
        momento_pts = 0
        
        # ERP moderno
        erp = safe_str(dossie.get('tech_stack', {}).get('erp_principal', 'N/D'))
        if 'SAP' in erp or 'S/4HANA' in erp:
            momento_pts += 100
        elif 'Protheus' in erp or 'TOTVS' in erp:
            momento_pts += 60
        elif erp != 'N/D':
            momento_pts += 40
        
        # Vagas de TI ativas
        vagas = len(dossie.get('tech_stack_identificado', {}).get('vagas_ativas', []))
        if vagas >= 5:
            momento_pts += 50
        elif vagas >= 2:
            momento_pts += 30
        
        # Conectividade crítica
        oportunidades_telecom = len(dossie.get('conectividade', {}).get('oportunidades_venda', []))
        if oportunidades_telecom >= 2:
            momento_pts += 50
        
        score_momento = min(momento_pts, 200)
        
        # === SCORE TOTAL ===
        score_total = score_musculo + score_complexidade + score_gente + score_momento
        
        # === TIER ===
        if score_total >= 800:
            tier = "Diamante"
        elif score_total >= 600:
            tier = "Ouro"
        elif score_total >= 400:
            tier = "Prata"
        else:
            tier = "Bronze"
        
        return {
            "score": score_total,
            "tier": tier,
            "breakdown": {
                "musculo": score_musculo,
                "complexidade": score_complexidade,
                "gente": score_gente,
                "momento": score_momento
            }
        }
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse seguro de JSON."""
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            logger.warning("Falha ao parsear JSON de resposta")
            return {}
