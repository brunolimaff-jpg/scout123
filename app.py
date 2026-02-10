"""
RADAR FOX-3 - Interface Principal
Sistema de Inteligência de Mercado Ultra-Profundo para Agronegócio
VERSÃO CORRIGIDA: Tratamento defensivo de imports opcionais
"""

import streamlit as st
import asyncio
import logging
from datetime import datetime
import pandas as pd
import json

# Importações de serviços
from services.gemini_service import GeminiService
from services.dossier_orchestrator import DossierOrchestrator
from utils.export_handler import ExportHandler

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIGURAÇÃO DE PÁGINA ==========
st.set_page_config(
    page_title="RADAR FOX-3 | Intelligence System",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS CUSTOMIZADO ==========
st.markdown("""
<style>
    /* Tema claro profissional */
    .main {
        background-color: #ffffff;
        color: #0f172a;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Cabeçalhos */
    h1 {
        color: #0f172a;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    h2 {
        color: #1e40af;
        font-weight: 700;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 8px;
        margin-top: 30px;
    }
    
    h3 {
        color: #475569;
        font-weight: 600;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        margin: 10px 0;
    }
    
    /* Alertas */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid #ef4444;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #0f172a;
        color: white;
    }
    
    /* Botões */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
    }
    
    /* Progresso */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
    }
    
    /* Tabelas */
    .dataframe {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown("""
<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); border-radius: 12px; margin-bottom: 30px;'>
    <h1 style='color: white; margin: 0; font-size: 2.8em;'>🔴 RADAR FOX-3</h1>
    <p style='color: #94a3b8; margin: 10px 0 0 0; font-size: 1.2em;'>Intelligence System | Versão 2.0</p>
</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🎯 Configuração de Missão")
    
    # Inputs
    empresa_alvo = st.text_input(
        "Empresa Alvo",
        placeholder="Ex: Grupo Scheffer",
        help="Razão social ou nome fantasia"
    )
    
    cnpj_input = st.text_input(
        "CNPJ (opcional)",
        placeholder="XX.XXX.XXX/0001-XX",
        help="Se não informado, será buscado automaticamente"
    )
    
    # API Key (pega do secrets ou input manual)
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    
    if not api_key:
        api_key = st.text_input(
            "🔑 Google API Key",
            type="password",
            help="Obtenha em: https://aistudio.google.com/app/apikey"
        )
    else:
        st.success("✅ API Key carregada dos Secrets do Streamlit Cloud")
    
    st.markdown("---")
    
    # Configurações avançadas
    with st.expander("⚙️ Configurações Avançadas"):
        max_retries = st.slider("Max Retries", 1, 5, 3)
        timeout_seconds = st.slider("Timeout (s)", 30, 120, 60)
    
    st.markdown("---")
    
    # Botão de disparo
    disparar_fox3 = st.button(
        "🚀 DISPARAR FOX-3",
        type="primary",
        use_container_width=True
    )
    
    st.markdown("---")
    st.markdown("### 📋 Status")
    status_placeholder = st.empty()
    progress_placeholder = st.empty()

# ========== ÁREA PRINCIPAL ==========

# Estado da sessão
if 'dossie_completo' not in st.session_state:
    st.session_state.dossie_completo = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

# ========== EXECUÇÃO DO DOSSIÊ ==========
if disparar_fox3:
    if not empresa_alvo:
        st.error("❌ Por favor, informe a empresa alvo!")
        st.stop()
    
    if not api_key:
        st.error("❌ Por favor, informe a API Key do Google Gemini!")
        st.stop()
    
    # Inicializa serviços (TODAS AS CAMADAS)
    from services.infrastructure_layer import InfrastructureLayer
    from services.financial_layer import FinancialLayer
    from services.intelligence_layer import IntelligenceLayer
    from services.market_estimator import MarketEstimator
    
    gemini_service = GeminiService(api_key=api_key)
    infrastructure_layer = InfrastructureLayer(gemini_service)
    financial_layer = FinancialLayer(gemini_service)
    intelligence_layer = IntelligenceLayer(gemini_service)
    market_estimator = MarketEstimator()
    
    orchestrator = DossierOrchestrator(
        gemini_service,
        infrastructure_layer,
        financial_layer,
        intelligence_layer,
        market_estimator
    )
    
    # Limpa logs anteriores
    st.session_state.logs = []
    
    # Callback para logs em tempo real
    def callback_log(mensagem: str):
        st.session_state.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "mensagem": mensagem
        })
        status_placeholder.info(f"🔄 {mensagem}")
    
    # Container de logs
    with st.expander("📡 Logs de Execução (Tempo Real)", expanded=True):
        log_container = st.empty()
    
    # Barra de progresso
    progress_bar = progress_placeholder.progress(0)
    
    try:
        # Executa dossiê
        with st.spinner("🔴 **FOX-3 ATIVO** | Executando inteligência profunda..."):
            # Converte para síncrono para Streamlit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            dossie_completo = loop.run_until_complete(
                orchestrator.executar_dosier_completo(
                    razao_social=empresa_alvo,
                    cnpj=cnpj_input if cnpj_input else "",
                    callback=callback_log
                )
            )
            
            loop.close()
        
        # Salva no estado
        st.session_state.dossie_completo = dossie_completo
        
        # Atualiza logs
        with log_container:
            for log in st.session_state.logs:
                st.text(f"[{log['timestamp']}] {log['mensagem']}")
        
        progress_bar.progress(100)
        status_placeholder.success("✅ **DOSSIÊ COMPLETO GERADO COM SUCESSO!**")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ **Erro crítico durante execução:** {str(e)}")
        logger.error(f"Erro fatal: {e}", exc_info=True)
        st.stop()

# ========== EXIBIÇÃO DO DOSSIÊ ==========
if st.session_state.dossie_completo:
    dossie = st.session_state.dossie_completo
    
    # ========== SCORECARD PRINCIPAL ==========
    st.markdown("---")
    st.markdown("## 📊 Scorecard Executivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_sas = dossie.get('sas_score', 0)
        tier_sas = dossie.get('sas_tier', 'N/D')
        st.metric("Score SAS", f"{score_sas}", tier_sas)
    
    with col2:
        area_total = dossie.get('dados_operacionais', {}).get('area_total', 0)
        st.metric("Área Total", f"{area_total:,} ha", "Mapeado")
    
    with col3:
        faturamento = dossie.get('dados_financeiros', {}).get('faturamento_estimado', 'N/D')
        st.metric("Faturamento", faturamento, "CRA/Auditado")
    
    with col4:
        erp = dossie.get('tech_stack', {}).get('erp_principal', 'N/D')
        st.metric("ERP Atual", erp, "Identificado")
    
    # ========== ALERTAS CRÍTICOS ==========
    validacoes = dossie.get('validacoes_criticas', {})
    alertas = validacoes.get('alertas', [])
    
    if alertas:
        st.markdown("---")
        st.markdown("## ⚠️ Alertas Críticos")
        
        for alerta in alertas:
            with st.expander(f"🚨 [{alerta.get('tipo', 'ALERTA')}] - Severidade: {alerta.get('severidade', 'ALTA')}", expanded=True):
                st.warning(f"**Mensagem:** {alerta.get('mensagem', 'N/D')}")
                st.info(f"**Causa Possível:** {alerta.get('causa_possivel', 'N/D')}")
                st.success(f"**Ação Recomendada:** {alerta.get('acao', 'N/D')}")
    
    # ========== CAMADA 1: INFRAESTRUTURA ==========
    st.markdown("---")
    st.markdown("## 1️⃣ Infraestrutura (Hard Assets)")
    
    tab1, tab2, tab3 = st.tabs(["🌍 SIGEF/CAR", "🚜 Maquinário", "📡 Conectividade"])
    
    with tab1:
        sigef_car = dossie.get('sigef_car', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Área Total", f"{sigef_car.get('area_total_hectares', 0):,} ha")
        with col_b:
            st.metric("Regularização", f"{sigef_car.get('regularizacao_percentual', 0)}%")
        with col_c:
            st.metric("Registros CAR", len(sigef_car.get('car_records', [])))
        
        # Tabela de propriedades
        car_records = sigef_car.get('car_records', [])
        if car_records:
            df_car = pd.DataFrame(car_records)
            st.dataframe(df_car, use_container_width=True)
    
    with tab2:
        maquinario = dossie.get('maquinario', {})
        frota = maquinario.get('frota_estimada_total', {})
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Tratores", frota.get('tratores', 0))
        with col_b:
            st.metric("Colheitadeiras", frota.get('colheitadeiras', 0))
        with col_c:
            st.metric("Plantadeiras", frota.get('plantadeiras', 0))
        with col_d:
            st.metric("Valor Estimado", maquinario.get('valor_estimado_frota', 'N/D'))
        
        # Detalhamento
        maq_confirmado = maquinario.get('maquinario_confirmado', [])
        if maq_confirmado:
            df_maq = pd.DataFrame(maq_confirmado)
            st.dataframe(df_maq, use_container_width=True)
    
    with tab3:
        conectividade = dossie.get('conectividade', {})
        analise_mun = conectividade.get('analise_por_municipio', [])
        
        if analise_mun:
            for mun in analise_mun:
                with st.expander(f"📍 {mun.get('municipio', 'N/D')}, {mun.get('uf', 'N/D')}"):
                    st.write(f"**Cobertura 4G:** {mun.get('cobertura_4g', {})}")
                    st.write(f"**Cobertura 5G:** {mun.get('cobertura_5g', 'Não')}")
                    st.write(f"**Zonas de Sombra:** {mun.get('zonas_sombra', 'N/D')}")
                    st.write(f"**Recomendações:** {', '.join(mun.get('recomendacoes', []))}")
    
    # ========== CAMADA 2: FINANCEIRO ==========
    st.markdown("---")
    st.markdown("## 2️⃣ Financeiro & Jurídico (Follow the Money)")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💰 CRA/Debêntures", "🏛️ Incentivos", "🌳 Ambiental", "⚖️ Trabalhista"])
    
    with tab1:
        cra = dossie.get('cra_debentures', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Faturamento Real", cra.get('faturamento_real', 'N/D'))
        with col_b:
            st.metric("EBITDA Consolidado", cra.get('ebitda_consolidado', 'N/D'))
        with col_c:
            st.metric("D/EBITDA", f"{cra.get('indice_dps', 'N/D')}x")
        
        emissoes = cra.get('emissoes_cra', [])
        if emissoes:
            df_cra = pd.DataFrame(emissoes)
            st.dataframe(df_cra, use_container_width=True)
    
    with tab2:
        incentivos = dossie.get('incentivos_fiscais', {})
        
        st.metric("Economia Fiscal Anual", incentivos.get('economia_fiscal_anual_total', 'N/D'))
        
        beneficios = incentivos.get('beneficios_ativos', [])
        if beneficios:
            df_inc = pd.DataFrame(beneficios)
            st.dataframe(df_inc, use_container_width=True)
    
    with tab3:
        multas = dossie.get('multas_ambientais', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Débitos Totais", multas.get('debitos_ambientais_total', 'N/D'))
        with col_b:
            st.metric("Propriedades Embargadas", multas.get('propriedades_embargadas', 0))
        with col_c:
            st.metric("Score de Risco", multas.get('score_risco_ambiental', 'N/D'))
        
        multas_ativas = multas.get('multas_ativas', [])
        if multas_ativas:
            df_multas = pd.DataFrame(multas_ativas)
            st.dataframe(df_multas, use_container_width=True)
    
    with tab4:
        trt = dossie.get('processos_trabalhistas', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Processos Ativos", trt.get('total_processos_ativos', 0))
        with col_b:
            st.metric("Valor Reclamado", trt.get('valor_total_reclamado', 'N/D'))
        with col_c:
            st.metric("Em Execução", trt.get('em_execucao', 0))
        
        st.write(f"**Padrão Identificado:** {trt.get('padrão_identificado', 'N/D')}")
        st.write(f"**Dor Principal:** {trt.get('dor_principal', 'N/D')}")
    
    # ========== CAMADA 3: SUPPLY CHAIN ==========
    st.markdown("---")
    st.markdown("## 3️⃣ Cadeia de Suprimentos")
    
    tab1, tab2 = st.tabs(["🚢 Exportação", "🧪 Bioinsumos"])
    
    with tab1:
        exportacao = dossie.get('exportacao', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Volume Exportado 2024", exportacao.get('volume_total_exportado_2024', 'N/D'))
        with col_b:
            st.metric("Receita Exportação", exportacao.get('receita_exportacao_2024', 'N/D'))
        with col_c:
            st.metric("Crescimento YoY", exportacao.get('crescimento_yoy', 'N/D'))
        
        exp_anos = exportacao.get('exportacoes_ultimos_3_anos', [])
        if exp_anos:
            df_exp = pd.DataFrame(exp_anos)
            st.dataframe(df_exp, use_container_width=True)
    
    with tab2:
        bioinsumos = dossie.get('bioinsumos', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Biofábricas", bioinsumos.get('total_biofabricas', 0))
        with col_b:
            st.metric("Capacidade Produção", bioinsumos.get('capacidade_producao_total', 'N/D'))
        with col_c:
            st.metric("Maturidade", bioinsumos.get('maturidade_bioinsumos', 'N/D'))
        
        biofab = bioinsumos.get('biofabricas', [])
        if biofab:
            df_bio = pd.DataFrame(biofab)
            st.dataframe(df_bio, use_container_width=True)
    
    # ========== CAMADA 4: TECH & PESSOAS ==========
    st.markdown("---")
    st.markdown("## 4️⃣ Tecnologia & Pessoas")
    
    tab1, tab2, tab3 = st.tabs(["💻 Tech Stack", "📧 Contatos", "👥 RH"])
    
    with tab1:
        tech = dossie.get('tech_stack_identificado', {})
        stack_consol = tech.get('stack_consolidado', {})
        
        st.write(f"**ERP Principal:** {stack_consol.get('ERP_Principal', 'N/D')}")
        st.write(f"**Banco de Dados:** {', '.join(stack_consol.get('Banco_Dados', []))}")
        st.write(f"**BI/Analytics:** {', '.join(stack_consol.get('BI_Analytics', []))}")
        st.write(f"**Cloud:** {', '.join(stack_consol.get('Cloud', []))}")
        st.write(f"**Maturidade TI:** {tech.get('maturidade_ti', 'N/D')}")
        
        vagas = tech.get('vagas_ativas', [])
        if vagas:
            df_vagas = pd.DataFrame(vagas)
            st.dataframe(df_vagas, use_container_width=True)
    
    with tab2:
        emails = dossie.get('emails_decisores', {})
        
        st.metric("Contatos Validados", emails.get('total_emails_validados', 0))
        st.write(f"**Padrão de E-mail:** {emails.get('padrao_email_identificado', 'N/D')}")
        
        emails_list = emails.get('emails_validos_identificados', [])
        if emails_list:
            df_emails = pd.DataFrame(emails_list)
            st.dataframe(df_emails, use_container_width=True)
    
    with tab3:
        funcionarios = dossie.get('estimativa_funcionarios', {})
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Estimado", funcionarios.get('total_funcionarios_estimado', 'N/D'))
        with col_b:
            st.metric("Mão de Obra Direta", funcionarios.get('estimativa_mao_obra_direta', 'N/D'))
        with col_c:
            st.metric("Confiança", funcionarios.get('confianca', 'N/D'))
        
        st.info(f"**Cálculo Base:** {funcionarios.get('calculo_base', 'N/D')}")
    
    # ========== ANÁLISE ESTRATÉGICA ==========
    st.markdown("---")
    st.markdown("## 🎯 Análise Estratégica")
    
    analise = dossie.get('analise_estrategica', {})
    
    with st.expander("📋 QUEM É ESTA EMPRESA?", expanded=True):
        st.markdown(analise.get('quem_e_empresa', 'Análise indisponível'))
    
    with st.expander("🔥 DORES & COMPLEXIDADE", expanded=True):
        st.markdown(analise.get('complexidade_dores', 'Análise indisponível'))
    
    with st.expander("🛡️ ARSENAL RECOMENDADO", expanded=True):
        st.markdown(analise.get('arsenal_recomendado', 'Análise indisponível'))
    
    with st.expander("🚀 PLANO DE ATAQUE", expanded=True):
        st.markdown(analise.get('plano_ataque', 'Análise indisponível'))
    
    # ========== FAMILY OFFICE ==========
    family_office = dossie.get('family_office', {})
    socios_est = family_office.get('socios_estrutura', [])
    
    if socios_est:
        st.markdown("---")
        st.markdown("## 🏦 Family Office")
        
        st.metric("Patrimônio Total Estimado", family_office.get('patrimonio_total_estimado', 'N/D'))
        st.metric("Capacidade Investimento/Ano", family_office.get('capacidade_investimento_family_office', 'N/D'))
        
        for socio in socios_est:
            with st.expander(f"👤 {socio.get('nome', 'N/D')}"):
                holdings = socio.get('holdings_patrimoniais', [])
                if holdings:
                    for hold in holdings:
                        st.write(f"**Holding:** {hold.get('razao_social', 'N/D')}")
                        participacoes = hold.get('participacoes', [])
                        if participacoes:
                            df_part = pd.DataFrame(participacoes)
                            st.dataframe(df_part, use_container_width=True)
    
    # ========== DOWNLOADS (CORRIGIDO COM TRATAMENTO DE ERROS) ==========
    st.markdown("---")
    st.markdown("## 📥 Downloads")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📄 Gerar PDF", use_container_width=True):
            try:
                pdf_buffer = ExportHandler.generate_pdf(dossie)
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_buffer,
                    file_name=f"RADAR_FOX3_{empresa_alvo.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF gerado!")
            except ImportError as e:
                st.error(f"❌ {str(e)}")
                st.info("💡 **Solução**: Adicione `reportlab>=4.0.0` ao requirements.txt e faça redeploy.")
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {e}")
    
    with col2:
        if st.button("📊 Gerar DOCX", use_container_width=True):
            try:
                docx_buffer = ExportHandler.generate_docx(dossie)
                st.download_button(
                    label="⬇️ Download DOCX",
                    data=docx_buffer,
                    file_name=f"RADAR_FOX3_{empresa_alvo.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                st.success("✅ DOCX gerado!")
            except ImportError as e:
                st.error(f"❌ {str(e)}")
                st.info("💡 **Solução**: Adicione `python-docx>=1.1.0` ao requirements.txt e faça redeploy.")
            except Exception as e:
                st.error(f"❌ Erro ao gerar DOCX: {e}")
    
    with col3:
        if st.button("💾 Exportar JSON Bruto", use_container_width=True):
            try:
                json_buffer = ExportHandler.generate_json(dossie)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_buffer,
                    file_name=f"RADAR_FOX3_{empresa_alvo.replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True
                )
                st.success("✅ JSON gerado!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar JSON: {e}")

# ========== INSTRUÇÕES INICIAIS ==========
else:
    st.markdown("---")
    st.markdown("## 🎯 Como Usar o RADAR FOX-3")
    
    st.info("""
    **O RADAR FOX-3 é um sistema de inteligência de mercado ultra-profundo para o agronegócio.**
    
    ### 📋 Passo a Passo:
    
    1. **Configure a Missão** (Sidebar):
       - Informe a empresa alvo (razão social)
       - Opcionalmente, informe o CNPJ
       - Insira sua Google API Key (Gemini 1.5 Pro)
    
    2. **Dispare o FOX-3**:
       - Clique em "🚀 DISPARAR FOX-3"
       - Aguarde a execução (5-10 minutos)
       - Acompanhe os logs em tempo real
    
    3. **Analise o Dossiê**:
       - 5 camadas de inteligência estruturada
       - Alertas críticos automáticos
       - Score SAS (0-1000 pontos)
       - Análise estratégica personalizada
    
    4. **Exporte os Resultados**:
       - PDF profissional
       - DOCX editável
       - JSON bruto
    
    ### 🔥 O que o FOX-3 faz:
    
    - ✅ **Infraestrutura:** SIGEF/CAR, frota, conectividade
    - ✅ **Financeiro:** CRA, incentivos, multas, processos
    - ✅ **Supply Chain:** Exportação, bioinsumos
    - ✅ **Tech & Pessoas:** Stack, e-mails, RH
    - ✅ **Validação:** Agente crítico, PDFs, Family Office
    
    ### ⚠️ Importante:
    
    - Requer API Key do Google Gemini 1.5 Pro
    - Tempo médio de execução: 5-10 minutos
    - Custo estimado: $2-5 por dossiê (tokens Gemini)
    - Dados provenientes de fontes públicas e OSINT
    """)
    
    st.markdown("---")
    st.markdown("### 📚 Documentação Técnica")
    
    with st.expander("🏗️ Arquitetura do Sistema"):
        st.markdown("""
        **Pipeline de 17 Passos:**
        
        1. Validação CNPJ + QSA
        2. Rastreio SIGEF/CAR
        3. Forense de Maquinário
        4. Análise Conectividade
        5. Mineração CRA/Debêntures
        6. Incentivos Fiscais
        7. Multas Ambientais
        8. Processos Trabalhistas
        9. Análise de Exportação
        10. Rastreio de Bioinsumos
        11. Scraping de Tech Stack
        12. Mapeamento de E-mails
        12.5. Estimativa de Funcionários
        13. Validação Adversária
        14. Parsing de PDFs
        15. Family Office
        16. Análise Estratégica
        17. Cálculo do Score SAS
        """)
    
    with st.expander("📊 Score SAS (Senior Agriculture Score)"):
        st.markdown("""
        **Metodologia de Pontuação (0-1000 pontos):**
        
        - **Músculo (Porte):** 300 pontos
          - Baseado em área total (hectares)
        
        - **Complexidade (Sofisticação):** 250 pontos
          - Biofábricas, exportação, verticalização
        
        - **Gente (Gestão/Finanças):** 250 pontos
          - Balanço auditado, processos, decisores
        
        - **Momento (Tech/Mercado):** 200 pontos
          - ERP, vagas de TI, conectividade
        
        **Tiers:**
        - 🔴 Diamante: 800-1000 pts
        - 🟡 Ouro: 600-799 pts
        - 🔵 Prata: 400-599 pts
        - 🟤 Bronze: 0-399 pts
        """)

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 20px;'>
    <p><strong>RADAR FOX-3 v2.0</strong> | Intelligence System for Agriculture</p>
    <p>Desenvolvido para <strong>Senior Sistemas | GAtec</strong></p>
    <p>⚠️ <em>Confidencial - Uso Restrito</em></p>
</div>
""", unsafe_allow_html=True)
