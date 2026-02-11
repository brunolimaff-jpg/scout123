"""
app.py — Interface Principal do Senior Scout 360
Versão Blindada com Diagnóstico de Erros de Importação
"""
import streamlit as st
import logging
import sys
import os

# 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATÓRIO SER A PRIMEIRA LINHA STREAMLIT)
st.set_page_config(
    page_title="RADAR FOX-3 | Senior Scout",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- DIAGNÓSTICO DE IMPORTS (EVITA TELA BRANCA) ---
try:
    import asyncio
    import json
    import time
    from services.dossier_orchestrator import DossierOrchestrator
    from services.gemini_service import GeminiService
    from services.infrastructure_layer import InfrastructureLayer
    from services.financial_layer import FinancialLayer
    from services.intelligence_layer import IntelligenceLayer
    from services.market_estimator import MarketEstimator
    from utils.export_handler import ExportHandler
except ImportError as e:
    st.error(f"🔴 ERRO CRÍTICO DE IMPORTAÇÃO: {e}")
    st.error("Verifique se todos os arquivos em 'services/' e 'utils/' existem e não têm erros de sintaxe.")
    st.stop()
except Exception as e:
    st.error(f"🔴 ERRO DESCONHECIDO NA INICIALIZAÇÃO: {e}")
    st.stop()

# --- ESTILOS CSS PERSONALIZADOS ---
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
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("⚠️ GEMINI_API_KEY não encontrada nos secrets!")
            st.stop()
            
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
        st.error(f"🔴 Erro ao iniciar serviços: {e}")
        # Retorna None para evitar crash, o app vai tratar depois
        return None, None

orchestrator, exporter = get_services()

if not orchestrator:
    st.stop() # Para a execução se os serviços falharem

# --- SIDEBAR ---
with st.sidebar:
    st.title("RADAR FOX-3")
    st.caption("Protocolo Bruno Lima | v3.4 Stable")
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
        # Loop Assíncrono Seguro para Streamlit
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        start_time = time.time()
        
        # Execução
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
        st.error(f"🔴 Erro fatal durante varredura: {e}")
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
        "📍 Infraestrutura & Ativos", 
        "💰 Financeiro & Compliance", 
        "🖥️ Tecnologia (Tech Stack)", 
        "🧠 Estratégia (Protocolo Ciro)",
        "📂 Exportação"
    ])

    # TAB 1: INFRAESTRUTURA (Deep Infra)
    with tab1:
        st.subheader("📍 Raio-X Geográfico e Industrial")
        
        ops = dossie.get('dados_operacionais', {}) or {}
        geo = dossie.get('sigef_car', {}) or {} 
        ind = ops.get('detalhes_industriais', {}) or {}
        
        # CORPORATIVO E ÁREA
        col_corp, col_area = st.columns([1, 1])
        
        with col_corp:
            st.markdown("### 🏢 QG Corporativo")
            corp = geo.get('corporativo', {})
            matriz = corp.get('matriz_endereco', 'Endereço não identificado')
            st.info(f"📍 **Matriz:** {matriz}")
            
            filiais = corp.get('escritorios_regionais', [])
            if isinstance(filiais, list) and filiais:
                st.caption(f"**Filiais/Bases:** {', '.join(filiais)}")
        
        with col_area:
            st.markdown("### 🗺️ Território")
            resumo = geo.get('resumo_territorial', {})
            area_real = resumo.get('area_total_ha', ops.get('area_total', 0))
            
            c1, c2 = st.columns(2)
            c1.metric("Área Total", f"{area_real:,.0f} ha")
            
            estados = resumo.get('estados', [])
            if isinstance(estados, list):
                c2.metric("Estados", ', '.join(estados))
            else:
                c2.metric("Estados", "N/D")

        st.markdown("---")

        # FAZENDAS
        lista_fazendas = geo.get('lista_fazendas', [])
        st.markdown(f"### 🚜 Unidades Produtivas ({len(lista_fazendas) if isinstance(lista_fazendas, list) else 0})")
        
        if isinstance(lista_fazendas, list) and lista_fazendas:
            with st.expander("📋 Ver Lista Completa de Fazendas", expanded=True):
                for f in lista_fazendas:
                    c_nome, c_local, c_detalhe = st.columns([2, 1, 2])
                    c_nome.markdown(f"**{f.get('nome', 'Fazenda')}**")
                    c_local.caption(f"📍 {f.get('municipio', 'N/D')}")
                    c_detalhe.write(f"📝 {f.get('detalhe', '-')}")
                    st.divider()
        else:
            st.warning("Lista nominal de fazendas não disponível.")

        st.markdown("---")

        # INDÚSTRIA E LOGÍSTICA
        col_ind, col_log = st.columns(2)
        
        with col_ind:
            st.markdown("### 🏭 Complexo Industrial & Bio")
            complexo = geo.get('complexo_industrial', [])
            
            if isinstance(complexo, list) and complexo:
                for item in complexo:
                    icone = "⚡" if "Energia" in str(item.get('tipo', '')) else "🧪"
                    st.success(f"**{icone} {item.get('tipo', 'Unidade')}:** {item.get('detalhe', '')}")
            elif isinstance(ind.get('plantas_industriais'), list) and ind.get('plantas_industriais'):
                for p in ind.get('plantas_industriais', []):
                    st.success(f"🏭 {p}")
            else:
                st.info("Nenhuma planta industrial complexa mapeada.")

        with col_log:
            st.markdown("### 🚚 Logística & Maquinário")
            log = geo.get('logistica_bimodal', {})
            
            if log:
                st.markdown(f"🚛 **Rodoviário:** {log.get('frota_rodoviaria', 'N/D')}")
                st.markdown(f"✈️ **Aéreo:** {log.get('frota_aerea', 'N/D')}")
                st.markdown(f"🚜 **Campo:** {log.get('patio_maquinas', 'N/D')}")
            else:
                st.caption("Detalhes logísticos restritos.")

    # TAB 2: FINANCEIRO
    with tab2:
        st.subheader("Saúde Financeira e Compliance")
        fin = dossie.get('dados_financeiros', {}) or {}
        
        st.metric("Faturamento Estimado/Real", fin.get('faturamento_estimado', 'N/D'))
        st.info(f"**Fonte/Origem:** {fin.get('fontes_auditoria', 'Análise de Mercado')}")
        
        st.markdown("#### 📰 Auditoria de Notícias")
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

    # TAB 4: ESTRATÉGIA
    with tab4:
        st.markdown("### 🧠 Protocolo Bruno Lima (Auditoria Forense)")
        
        analise_ciro = dossie.get("analise_estrategica", {}).get("relatorio_completo_ciro")
        
        if analise_ciro:
            with st.container():
                st.markdown(analise_ciro)
        else:
            st.warning("Relatório forense em processamento ou dados insuficientes.")

    # TAB 5: EXPORTAÇÃO
    with tab5:
        st.subheader("Gerar Entregáveis")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Baixar Relatório PDF"):
                try:
                    pdf_bytes = exporter.gerar_pdf(dossie)
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"RADAR_{str(dossie.get('empresa_alvo', 'Alvo')).replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")
        
        with c2:
            if st.button("💾 Baixar JSON"):
                try:
                    json_bytes = exporter.gerar_json(dossie)
                    st.download_button(
                        label="Download JSON",
                        data=json_bytes,
                        file_name=f"RADAR_{str(dossie.get('empresa_alvo', 'Alvo')).replace(' ', '_')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar JSON: {e}")

st.markdown("---")
st.caption("🔒 SENIOR SISTEMAS | SC SQUAD AGRO | USO INTERNO E CONFIDENCIAL")
