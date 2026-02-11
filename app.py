"""
app.py — Interface Principal do Senior Scout 360 (Protocolo Bruno Lima)
Frontend Streamlit - Versão Blindada e Estável
"""
import streamlit as st
import asyncio
import logging
import json
import os
import time

# Configuração da Página (DEVE SER A PRIMEIRA CHAMADA)
st.set_page_config(
    page_title="RADAR FOX-3 | Senior Scout",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports dos serviços
from services.dossier_orchestrator import DossierOrchestrator
from services.gemini_service import GeminiService
from services.infrastructure_layer import InfrastructureLayer
from services.financial_layer import FinancialLayer
from services.intelligence_layer import IntelligenceLayer
from services.market_estimator import MarketEstimator
from utils.export_handler import ExportHandler

# Configuração de Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ESTILOS CSS PERSONALIZADOS (Cyberpunk Agro) ---
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    .stButton>button {
        width: 100%;
        background-color: #00ff41;
        color: #000000;
        font-weight: bold;
        border: none;
        height: 50px;
    }
    .stButton>button:hover {
        background-color: #00cc33;
        color: #000000;
    }
    .metric-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
    }
    h1, h2, h3 {
        color: #58a6ff;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        background-color: #21262d;
        border-left: 5px solid #00ff41;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE SERVIÇOS (SINGLETON) ---
@st.cache_resource
def get_services():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        gemini = GeminiService(api_key)
        
        infra = InfrastructureLayer(gemini)
        financial = FinancialLayer(gemini)
        intel = IntelligenceLayer(gemini)
        market = MarketEstimator()
        
        orchestrator = DossierOrchestrator(
            gemini_service=gemini,
            infrastructure_layer=infra,
            financial_layer=financial,
            intelligence_layer=intel,
            market_estimator=market
        )
        
        exporter = ExportHandler()
        
        return orchestrator, exporter
    except Exception as e:
        st.error(f"Erro crítico na inicialização: {e}")
        st.stop()

orchestrator, exporter = get_services()

# --- SIDEBAR: CONTROLES ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png", width=50) # Placeholder Logo
    st.title("RADAR FOX-3")
    st.caption("Protocolo Bruno Lima | v3.3 Final")
    
    st.divider()
    
    target_company = st.text_input("Nome da Empresa Alvo", placeholder="Ex: Grupo Scheffer")
    target_cnpj = st.text_input("CNPJ (Opcional)", placeholder="00.000.000/0001-00")
    
    st.divider()
    
    if st.button("🚀 INICIAR VARREDURA"):
        if not target_company:
            st.warning("Informe o nome da empresa!")
        else:
            st.session_state['scanning'] = True
            st.session_state['target'] = target_company
            st.session_state['cnpj_target'] = target_cnpj

# --- ÁREA PRINCIPAL ---
st.title(f"📡 Painel de Inteligência de Mercado")
st.markdown("---")

if 'dossier_result' not in st.session_state:
    st.session_state['dossier_result'] = None

# --- LÓGICA DE EXECUÇÃO ---
if st.session_state.get('scanning'):
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    def update_status(msg):
        status_container.markdown(f"<div class='status-box'>Running: {msg}</div>", unsafe_allow_html=True)

    try:
        # Loop Assíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        start_time = time.time()
        
        dossie_completo = loop.run_until_complete(
            orchestrator.executar_dosier_completo(
                razao_social=st.session_state['target'],
                cnpj=st.session_state['cnpj_target'],
                callback=update_status
            )
        )
        
        elapsed = time.time() - start_time
        progress_bar.progress(100)
        status_container.success(f"Varredura concluída em {elapsed:.1f}s")
        st.session_state['dossier_result'] = dossie_completo
        st.session_state['scanning'] = False
        st.rerun() 
        
    except Exception as e:
        st.error(f"Erro fatal durante varredura: {e}")
        st.session_state['scanning'] = False
        logger.error(f"Erro App: {e}", exc_info=True)

# --- EXIBIÇÃO DE RESULTADOS ---
if st.session_state['dossier_result']:
    dossie = st.session_state['dossier_result']
    
    # Cabeçalho
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Alvo", dossie.get('empresa_alvo', 'N/D'))
    with col2:
        st.metric("Score SAS", f"{dossie.get('sas_score', 0)}/1000")
    with col3:
        st.metric("Tier", dossie.get('sas_tier', 'N/A'))
    with col4:
        area_fmt = f"{dossie.get('dados_operacionais', {}).get('area_total', 0):,.0f}"
        st.metric("Área Mapeada", f"{area_fmt} ha")

    st.markdown("---")

    # Abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Operacional & Industrial", 
        "💰 Financeiro & Auditoria", 
        "🖥️ Tecnologia (Tech Stack)", 
        "🧠 Protocolo Bruno Lima (Estratégia)",
        "📂 Exportação"
    ])

    # TAB 1: OPERACIONAL
    with tab1:
        st.subheader("Infraestrutura Física")
        ops = dossie.get('dados_operacionais', {}) or {}
        ind = ops.get('detalhes_industriais', {}) or {}
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🌾 Terras e Culturas")
            st.write(f"**Área Total:** {ops.get('area_total', 0):,.0f} hectares")
            st.write(f"**Fazendas/Matrículas:** {ops.get('numero_fazendas', 0)}")
            
            # BLINDAGEM VISUAL: Lista de Regiões
            regioes = ops.get('regioes_atuacao', [])
            if isinstance(regioes, list) and regioes:
                st.write(f"**Regiões:** {', '.join(regioes)}")
            else:
                st.write("**Regiões:** N/D")
            
        with c2:
            st.markdown("#### 🏭 Parque Industrial")
            st.write(f"**Armazenagem:** {ind.get('capacidade_armazenagem', 'N/D')}")
            st.write("**Plantas Industriais:**")
            
            # BLINDAGEM VISUAL: Lista de Plantas
            plantas = ind.get('plantas_industriais')
            if isinstance(plantas, list) and plantas:
                for planta in plantas:
                    st.write(f"- {planta}")
            else:
                st.info("Nenhuma planta industrial identificada publicamente.")

    # TAB 2: FINANCEIRO
    with tab2:
        st.subheader("Saúde Financeira e Compliance")
        fin = dossie.get('dados_financeiros', {}) or {}
        
        st.metric("Faturamento Estimado/Real", fin.get('faturamento_estimado', 'N/D'))
        st.info(f"**Fonte/Origem:** {fin.get('fontes_auditoria', 'Análise de Mercado')}")
        
        st.markdown("#### 📰 Auditoria de Notícias (Riscos & Investimentos)")
        
        # BLINDAGEM VISUAL: Notícias
        noticias = dossie.get('auditoria_noticias', [])
        if isinstance(noticias, list) and noticias:
            for n in noticias:
                st.markdown(f"**{n.get('data_aprox', '')}** - [{n.get('titulo')}]({n.get('link', '#')}) - *Fonte: {n.get('fonte')}*")
        else:
            st.caption("Nenhuma notícia crítica recente encontrada.")

    # TAB 3: TECNOLOGIA
    with tab3:
        st.subheader("Ecossistema Tecnológico")
        tech = dossie.get('tech_stack', {}) or {}
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🖥️ ERP & Backoffice")
            erp = str(tech.get('erp_principal', 'N/D'))
            if "senior" in erp.lower():
                st.success(f"**ERP Atual:** {erp} (Base Instalada)")
            else:
                st.error(f"**ERP Atual:** {erp} (Oportunidade de Troca)")
                
        with c2:
            st.markdown("#### 🚜 Agritech & Campo")
            st.write(f"**Maturidade Digital:** {tech.get('maturidade_ti', 'N/D')}")

    # TAB 4: ESTRATÉGIA (PROTOCOLO BRUNO LIMA)
    with tab4:
        st.markdown("### 🧠 Protocolo Bruno Lima (Auditoria Forense)")
        
        analise_ciro = dossie.get("analise_estrategica", {}).get("relatorio_completo_ciro")
        
        if analise_ciro:
            with st.container():
                st.markdown(analise_ciro)
        else:
            st.warning("Relatório forense em processamento ou dados insuficientes.")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Quem é:** {dossie.get('analise_estrategica', {}).get('quem_e_empresa', 'N/D')}")
            with col2:
                st.error(f"**Plano:** {dossie.get('analise_estrategica', {}).get('plano_ataque', 'N/D')}")

    # TAB 5: EXPORTAÇÃO
    with tab5:
        st.subheader("Gerar Entregáveis")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Baixar Relatório PDF (Executivo)"):
                try:
                    pdf_bytes = exporter.gerar_pdf(dossie)
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"RADAR_FOX3_{str(dossie.get('empresa_alvo', 'Alvo')).replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")
        
        with c2:
            if st.button("💾 Baixar Dados Brutos (JSON)"):
                json_bytes = exporter.gerar_json(dossie)
                st.download_button(
                    label="Download JSON",
                    data=json_bytes,
                    file_name=f"RADAR_FOX3_{str(dossie.get('empresa_alvo', 'Alvo')).replace(' ', '_')}.json",
                    mime="application/json"
                )

# --- RODAPÉ ---
st.markdown("---")
st.caption("🔒 SENIOR SISTEMAS | SC SQUAD AGRO | USO INTERNO E CONFIDENCIAL")
