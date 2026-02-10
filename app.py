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
from services.cnpj_service import consultar_cnpj
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
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    
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
    
    # Limpa logs anteriores
    st.session_state.logs = []
    
    # Callback para logs em tempo real
    def callback_log(mensagem: str, percent: int = 0):
        st.session_state.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "mensagem": mensagem
        })
        status_placeholder.info(f"🔄 {mensagem}")
        if percent > 0:
            progress_placeholder.progress(percent)
    
    # Container de logs
    with st.expander("📡 Logs de Execução (Tempo Real)", expanded=True):
        log_container = st.empty()
    
    try:
        with st.spinner("🔴 **FOX-3 ATIVO** | Executando inteligência profunda..."):
            # PASSO 1: Buscar CNPJ
            callback_log("🔍 Consultando dados cadastrais (CNPJ)...", 5)
            
            cnpj_data = consultar_cnpj(cnpj_input if cnpj_input else empresa_alvo)
            
            if not cnpj_data:
                st.error(f"❌ Não foi possível localizar o CNPJ de '{empresa_alvo}'")
                st.stop()
            
            # Converte DadosCNPJ para dict
            cnpj_dict = {
                "cnpj": cnpj_data.cnpj,
                "nome": cnpj_data.razao_social,
                "nome_fantasia": cnpj_data.nome_fantasia,
                "situacao": cnpj_data.situacao_cadastral,
                "capital_social": cnpj_data.capital_social,
                "porte": cnpj_data.porte,
                "cnae_principal": cnpj_data.cnae_principal,
                "municipio": cnpj_data.municipio,
                "uf": cnpj_data.uf,
                "qsa": cnpj_data.qsa,
                "fonte": cnpj_data.fonte
            }
            
            callback_log(f"✅ CNPJ encontrado: {cnpj_dict['nome']} ({cnpj_dict['cnpj']})", 10)
            
            # PASSO 2: Inicializa serviços
            callback_log("⚙️ Inicializando camadas de inteligência...", 15)
            
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
            
            callback_log("✅ Camadas inicializadas", 20)
            
            # PASSO 3: Executa dossiê completo
            callback_log("🚀 Iniciando geração do dossiê...", 25)
            
            # Converte para síncrono para Streamlit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            dossie_completo = loop.run_until_complete(
                orchestrator.gerar_dossie_completo(
                    cnpj_data=cnpj_dict,
                    progress_callback=callback_log
                )
            )
            
            loop.close()
        
        # Salva no estado
        st.session_state.dossie_completo = dossie_completo
        
        # Atualiza logs
        with log_container:
            for log in st.session_state.logs:
                st.text(f"[{log['timestamp']}] {log['mensagem']}")
        
        progress_placeholder.progress(100)
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
        score_sas = dossie.get('score_sas', 0)
        tier_sas = dossie.get('classificacao', 'N/D')
        st.metric("Score SAS", f"{score_sas}", tier_sas)
    
    with col2:
        area_total = dossie.get('area_total_hectares', 0)
        st.metric("Área Total", f"{area_total:,} ha", "Mapeado")
    
    with col3:
        faturamento = dossie.get('faturamento', 'N/D')
        st.metric("Faturamento", faturamento, "CRA/Auditado")
    
    with col4:
        erp = dossie.get('erp_atual', 'N/D')
        st.metric("ERP Atual", erp, "Identificado")
    
    # ========== CAMADA 1: INFRAESTRUTURA ==========
    st.markdown("---")
    st.markdown("## 1️⃣ Infraestrutura (Hard Assets)")
    
    tab1, tab2, tab3 = st.tabs(["🌍 SIGEF/CAR", "🚜 Maquinário", "📡 Conectividade"])
    
    with tab1:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Área Total", f"{dossie.get('area_total_hectares', 0):,} ha")
        with col_b:
            st.metric("Regularização", f"{dossie.get('regularizacao_ambiental', 0)}%")
        with col_c:
            st.metric("Registros CAR", len(dossie.get('car_records', [])))
        
        # Tabela de propriedades
        car_records = dossie.get('car_records', [])
        if car_records:
            df_car = pd.DataFrame(car_records)
            st.dataframe(df_car, use_container_width=True)
    
    with tab2:
        frota = dossie.get('frota', {})
        frota_total = frota.get('frota_estimada_total', {})
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Tratores", frota_total.get('tratores', 0))
        with col_b:
            st.metric("Colheitadeiras", frota_total.get('colheitadeiras', 0))
        with col_c:
            st.metric("Plantadeiras", frota_total.get('plantadeiras', 0))
        with col_d:
            st.metric("Valor Estimado", frota.get('valor_estimado_frota', 'N/D'))
        
        # Detalhamento
        maq_confirmado = frota.get('maquinario_confirmado', [])
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
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Faturamento Real", dossie.get('faturamento', 'N/D'))
        with col_b:
            st.metric("EBITDA Consolidado", dossie.get('ebitda', 'N/D'))
        with col_c:
            st.metric("Auditor", dossie.get('auditor', 'N/D'))
        
        emissoes = dossie.get('emissoes_cra', [])
        if emissoes:
            df_cra = pd.DataFrame(emissoes)
            st.dataframe(df_cra, use_container_width=True)
    
    with tab2:
        st.metric("Economia Fiscal Anual", dossie.get('economia_fiscal_anual', 'N/D'))
        
        beneficios = dossie.get('incentivos_fiscais', [])
        if beneficios:
            df_inc = pd.DataFrame(beneficios)
            st.dataframe(df_inc, use_container_width=True)
    
    with tab3:
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Score de Risco", dossie.get('score_risco_ambiental', 'N/D'))
        with col_b:
            st.metric("Multas Ativas", len(dossie.get('multas_ambientais', [])))
        
        multas_ativas = dossie.get('multas_ambientais', [])
        if multas_ativas:
            df_multas = pd.DataFrame(multas_ativas)
            st.dataframe(df_multas, use_container_width=True)
    
    with tab4:
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Processos Ativos", dossie.get('processos_trabalhistas', 0))
        with col_b:
            st.write(f"**Dor Principal:** {dossie.get('dor_trabalhista', 'N/D')}")
    
    # ========== CAMADA 3: INTELLIGENCE ==========
    st.markdown("---")
    st.markdown("## 3️⃣ Inteligência Competitiva")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Concorrentes", "💼 M&A", "👔 Liderança", "💻 Tech"])
    
    with tab1:
        st.write(f"**Posicionamento:** {dossie.get('posicionamento_mercado', 'N/D')}")
        
        concorrentes = dossie.get('concorrentes', [])
        if concorrentes:
            df_conc = pd.DataFrame(concorrentes)
            st.dataframe(df_conc, use_container_width=True)
    
    with tab2:
        st.write(f"**Tendência:** {dossie.get('tendencia_expansao', 'N/D')}")
        st.write(f"**Pipeline:** {dossie.get('pipeline_ma', 'N/D')}")
        
        movimentos = dossie.get('movimentos_ma', [])
        if movimentos:
            df_ma = pd.DataFrame(movimentos)
            st.dataframe(df_ma, use_container_width=True)
    
    with tab3:
        st.write(f"**Cultura Organizacional:** {dossie.get('cultura_organizacional', 'N/D')}")
        st.info(f"**💡 Dica de Abordagem:** {dossie.get('abordagem_comercial', 'N/D')}")
        
        executivos = dossie.get('executivos', [])
        if executivos:
            df_exec = pd.DataFrame(executivos)
            st.dataframe(df_exec, use_container_width=True)
    
    with tab4:
        st.write(f"**ERP Atual:** {dossie.get('erp_atual', 'N/D')}")
        st.write(f"**Maturidade Digital:** {dossie.get('maturidade_digital', 'N/D')}")
        
        st.write("**Stack Tecnológico:**")
        for tech in dossie.get('stack_tecnologico', []):
            st.write(f"- {tech}")
        
        st.write("**Gaps Identificados:**")
        for gap in dossie.get('gaps_tecnologicos', []):
            st.write(f"- {gap}")
        
        st.success("**Oportunidades de Venda:**")
        for opp in dossie.get('oportunidades_venda', []):
            st.write(f"- {opp}")
    
    # ========== SÓCIOS ==========
    socios = dossie.get('socios', [])
    if socios:
        st.markdown("---")
        st.markdown("## 👥 Quadro Societário")
        
        df_socios = pd.DataFrame(socios)
        st.dataframe(df_socios, use_container_width=True)
    
    # ========== DOWNLOADS ==========
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
       - Infraestrutura, Financeiro, Intelligence
       - Score SAS (0-1000 pontos)
       - Classificação de potencial
    
    4. **Exporte os Resultados**:
       - PDF profissional
       - DOCX editável
       - JSON bruto
    
    ### ⚠️ Importante:
    
    - Requer API Key do Google Gemini 1.5 Pro
    - Tempo médio de execução: 5-10 minutos
    - Custo estimado: $2-5 por dossiê (tokens Gemini)
    - Dados provenientes de fontes públicas e OSINT
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
