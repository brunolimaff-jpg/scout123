"""
app_v2.py — RADAR FOX-3 v2.0 | Intelligence System
Melhorias: Status em tempo real, validação robusta, Gemini 2.5 Pro, UX aprimorado
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time, random, json, csv, io
from datetime import datetime
from typing import Optional, Dict, Any

# Importações dos serviços
try:
    from services.dossier_orchestrator import gerar_dossie_completo
    from services.cnpj_service import formatar_cnpj, validar_cnpj, limpar_cnpj
    from services.market_estimator_v2 import calcular_sas
    from services.data_validator import safe_float, safe_int, safe_str
    from services.data_sources import data_sources
    from scout_types import DossieCompleto, Tier, QualityLevel, PipelineStepResult
except ImportError as e:
    st.error(f"⚠️ Erro ao importar módulos: {e}")
    st.stop()

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="RADAR FOX-3 v2.0",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS APRIMORADO - HUD AVIATION THEME COM MELHORIAS UX
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Rajdhani:wght@500;600;700;900&display=swap');

/* BASE */
.stApp {
    background: linear-gradient(180deg, #0F172A 0%, #020617 100%) !important;
    color: #E2E8F0 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
    border-right: 2px solid #334155 !important;
}

/* HUD ELEMENTS */
div[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid #475569 !important;
    border-radius: 4px !important;
    padding: 15px !important;
    backdrop-filter: blur(10px);
    position: relative;
}

div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 12px;
    height: 12px;
    border-top: 2px solid #38BDF8;
    border-left: 2px solid #38BDF8;
}

div[data-testid="stMetric"]::after {
    content: '';
    position: absolute;
    bottom: 0;
    right: 0;
    width: 12px;
    height: 12px;
    border-bottom: 2px solid #38BDF8;
    border-right: 2px solid #38BDF8;
}

div[data-testid="stMetric"] label {
    color: #94A3B8 !important;
    font-family: 'JetBrains Mono' !important;
    font-size: 0.75rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #38BDF8 !important;
    font-family: 'Rajdhani' !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

/* BUTTONS */
.stButton>button {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    color: #0F172A !important;
    border: 2px solid #FBBF24 !important;
    font-family: 'Rajdhani' !important;
    font-weight: 800 !important;
    font-size: 1.1rem !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
}

.stButton>button:hover {
    background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%) !important;
    box-shadow: 0 0 25px rgba(245, 158, 11, 0.6) !important;
    transform: translateY(-2px) scale(1.02);
    border-color: #FDE047 !important;
}

.stButton>button:active {
    transform: translateY(0) scale(0.98);
}

/* INPUTS */
.stTextInput>div>div>input {
    background: rgba(15, 23, 42, 0.8) !important;
    color: #38BDF8 !important;
    border: 1px solid #334155 !important;
    font-family: 'JetBrains Mono' !important;
    letter-spacing: 1px !important;
    padding: 12px !important;
    border-radius: 4px !important;
    transition: all 0.3s ease;
}

.stTextInput>div>div>input:focus {
    border-color: #38BDF8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    background: rgba(15, 23, 42, 1) !important;
}

/* PROGRESS BAR CUSTOMIZADO */
.progress-container {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
}

.progress-bar {
    height: 8px;
    background: #1E293B;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #334155;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #38BDF8, #10B981);
    border-radius: 4px;
    transition: width 0.5s ease;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

/* STATUS CARDS */
.status-card {
    background: rgba(30, 41, 59, 0.6);
    border-left: 4px solid #38BDF8;
    padding: 15px;
    margin: 10px 0;
    border-radius: 4px;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.status-card:hover {
    background: rgba(30, 41, 59, 0.8);
    transform: translateX(5px);
}

.status-card.success { border-left-color: #10B981; }
.status-card.warning { border-left-color: #F59E0B; }
.status-card.error { border-left-color: #EF4444; }
.status-card.running { border-left-color: #38BDF8; animation: pulse 2s infinite; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* STEP INDICATOR */
.step-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 15px 0;
}

.step-number {
    min-width: 35px;
    height: 35px;
    border-radius: 50%;
    background: #1E293B;
    border: 2px solid #334155;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Rajdhani';
    font-weight: 700;
    color: #64748B;
}

.step-number.active {
    background: #38BDF8;
    border-color: #38BDF8;
    color: #0F172A;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.5);
}

.step-number.complete {
    background: #10B981;
    border-color: #10B981;
    color: #FFF;
}

.step-number.error {
    background: #EF4444;
    border-color: #EF4444;
    color: #FFF;
}

/* HEADERS */
.radar-header {
    font-family: 'Rajdhani';
    font-weight: 900;
    font-size: 3.5rem;
    color: #38BDF8;
    letter-spacing: 8px;
    text-shadow: 0 0 20px rgba(56, 189, 248, 0.6);
    margin: 0;
    line-height: 1;
}

.section-header {
    font-family: 'Rajdhani';
    color: #E2E8F0;
    font-size: 1.6rem;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 2px solid #334155;
    padding-bottom: 10px;
    margin: 30px 0 20px 0;
    letter-spacing: 2px;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 2px solid #334155;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.4);
    color: #64748B;
    border: none;
    padding: 12px 24px;
    font-family: 'Rajdhani';
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(30, 41, 59, 0.6);
    color: #94A3B8;
}

.stTabs [aria-selected="true"] {
    background: #38BDF8 !important;
    color: #0F172A !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
}

/* EXPANDERS */
.streamlit-expanderHeader {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid #334155 !important;
    border-radius: 4px !important;
    font-family: 'Rajdhani' !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
}

/* DIVIDERS */
.neon-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #38BDF8, transparent);
    margin: 25px 0;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
}

/* CONFIDENCE BADGE */
.confidence-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-family: 'JetBrains Mono';
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
}

.confidence-high { background: #10B981; color: #FFF; }
.confidence-medium { background: #F59E0B; color: #0F172A; }
.confidence-low { background: #EF4444; color: #FFF; }

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1E293B;
}

::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #64748B;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def format_confidence(conf: float) -> str:
    """Formata confiança como badge colorido."""
    conf_pct = int(conf * 100)
    if conf >= 0.7:
        cls = "confidence-high"
        label = "ALTA"
    elif conf >= 0.4:
        cls = "confidence-medium"
        label = "MÉDIA"
    else:
        cls = "confidence-low"
        label = "BAIXA"
    return f'<span class="confidence-badge {cls}">{label} ({conf_pct}%)</span>'

def render_step_indicator(steps: list, current_step: int = 0):
    """Renderiza indicador visual de progresso dos passos."""
    html = '<div style="display:flex;gap:10px;margin:20px 0;flex-wrap:wrap;">'
    
    for i, step in enumerate(steps, 1):
        if isinstance(step, PipelineStepResult):
            status = step.status
            icone = step.icone
            titulo = step.titulo
        else:
            status = 'pending'
            icone = step.get('icone', '❓')
            titulo = step.get('titulo', f'Step {i}')
        
        # Define classe baseada no status
        if status == 'success':
            cls = 'complete'
        elif status == 'running':
            cls = 'active'
        elif status == 'error':
            cls = 'error'
        else:
            cls = ''
        
        html += f'''
        <div class="step-indicator">
            <div class="step-number {cls}">{icone}</div>
            <div style="font-family:'JetBrains Mono';font-size:0.75rem;color:#94A3B8;">
                {titulo}
            </div>
        </div>
        '''
    
    html += '</div>'
    return html

def render_progress_bar(progress: float, label: str = ""):
    """Renderiza barra de progresso customizada."""
    progress_pct = int(progress * 100)
    html = f'''
    <div class="progress-container">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-family:'Rajdhani';font-weight:600;color:#E2E8F0;">{label}</span>
            <span style="font-family:'JetBrains Mono';color:#38BDF8;font-weight:700;">{progress_pct}%</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width:{progress_pct}%;"></div>
        </div>
    </div>
    '''
    return html

def render_status_card(titulo: str, conteudo: str, status: str = "info", detalhes: list = None, conf: float = 0):
    """Renderiza card de status com informações."""
    html = f'<div class="status-card {status}">'
    html += f'<div style="font-family:Rajdhani;font-weight:700;font-size:1.1rem;color:#E2E8F0;margin-bottom:8px;">{titulo}</div>'
    html += f'<div style="font-family:JetBrains Mono;font-size:0.85rem;color:#94A3B8;">{conteudo}</div>'
    
    if detalhes:
        html += '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #334155;">'
        for det in detalhes:
            html += f'<div style="font-family:JetBrains Mono;font-size:0.75rem;color:#64748B;margin:4px 0;">• {det}</div>'
        html += '</div>'
    
    if conf > 0:
        html += f'<div style="margin-top:10px;">{format_confidence(conf)}</div>'
    
    html += '</div>'
    return html

def gerar_csv_report(d: DossieCompleto) -> str:
    """Gera relatório CSV do dossiê."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["RADAR FOX-3 v2.0", "Relatório de Inteligência"])
    writer.writerow(["Timestamp", d.timestamp_geracao])
    writer.writerow([])
    
    writer.writerow(["ALVO"])
    writer.writerow(["Empresa", d.empresa_alvo])
    writer.writerow(["CNPJ", d.cnpj or "N/A"])
    writer.writerow(["Nome Grupo", d.dados_operacionais.nome_grupo or "N/A"])
    writer.writerow([])
    
    writer.writerow(["SCORE SAS"])
    writer.writerow(["Pontuação", d.sas_result.score])
    writer.writerow(["Tier", d.sas_result.tier.value])
    writer.writerow([])
    
    writer.writerow(["DADOS OPERACIONAIS"])
    writer.writerow(["Hectares Total", safe_float(d.dados_operacionais.hectares_total, 0)])
    writer.writerow(["Número de Fazendas", safe_int(d.dados_operacionais.numero_fazendas, 0)])
    writer.writerow(["Culturas", ", ".join(d.dados_operacionais.culturas or [])])
    writer.writerow([])
    
    writer.writerow(["DADOS FINANCEIROS"])
    writer.writerow(["Capital Social", safe_float(d.dados_financeiros.capital_social_estimado, 0)])
    writer.writerow(["Funcionários", safe_int(d.dados_financeiros.funcionarios_estimados, 0)])
    writer.writerow([])
    
    writer.writerow(["QUALIDADE"])
    writer.writerow(["Nível", d.quality_report.nivel.value if d.quality_report else "N/A"])
    writer.writerow(["Score", f"{d.quality_report.score_qualidade:.1f}%" if d.quality_report else "N/A"])
    
    return output.getvalue()

# ==============================================================================
# INICIALIZA SESSION STATE
# ==============================================================================
if 'dossie' not in st.session_state:
    st.session_state.dossie = None
if 'pipeline_steps' not in st.session_state:
    st.session_state.pipeline_steps = []
if 'current_progress' not in st.session_state:
    st.session_state.current_progress = 0.0
if 'processing' not in st.session_state:
    st.session_state.processing = False

# ==============================================================================
# SIDEBAR - CONTROLE DE MISSÃO
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:15px 0 25px 0;">
        <div style="font-size:4rem;margin-bottom:10px;">📡</div>
        <div class="radar-header" style="font-size:2.8rem;">RADAR</div>
        <div style="font-family:'JetBrains Mono';font-size:0.65rem;color:#64748B;letter-spacing:2px;margin-top:10px;">
            v2.0 | PRECISION MODE<br>
            SYSTEM: ONLINE<br>
            MODEL: GEMINI 2.5 PRO
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    
    # API Key
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Key configurada")
    except:
        api_key = st.text_input("🔑 Gemini API Key", type="password", help="Insira sua chave da API Gemini")
        if not api_key:
            st.warning("⚠️ API Key necessária")
    
    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    
    # Inputs de alvo
    st.markdown('<div style="font-family:Rajdhani;font-weight:700;color:#38BDF8;font-size:1.1rem;margin-bottom:10px;">COORDENADAS DO ALVO</div>', unsafe_allow_html=True)
    
    target = st.text_input(
        "Nome da Empresa",
        placeholder="Ex: GRUPO SCHEFFER",
        help="Digite o nome da empresa-alvo",
        disabled=st.session_state.processing
    )
    
    target_cnpj = st.text_input(
        "CNPJ (Opcional)",
        placeholder="00.000.000/0000-00",
        help="CNPJ para busca mais precisa",
        disabled=st.session_state.processing
    )
    
    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    
    # Botão de disparo
    can_fire = target and api_key and not st.session_state.processing
    btn_label = "🦊 FOX-3 DISPARAR" if can_fire else "⛔ AGUARDANDO COORDENADAS"
    
    btn_fire = st.button(
        btn_label,
        type="primary",
        disabled=not can_fire,
        use_container_width=True
    )
    
    # Status do sistema
    if st.session_state.processing:
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        st.markdown(render_progress_bar(st.session_state.current_progress, "PROGRESSÃO DA MISSÃO"), unsafe_allow_html=True)
    
    st.markdown('<div style="position:fixed;bottom:15px;font-size:0.65rem;color:#475569;font-family:JetBrains Mono;text-align:center;width:250px;">© 2026 RADAR SYSTEM<br>CLASSIFIED OPERATION</div>', unsafe_allow_html=True)

# ==============================================================================
# MAIN AREA
# ==============================================================================

tab_radar, tab_steps, tab_intel, tab_sources = st.tabs([
    "📡 RADAR DISPLAY",
    "🔍 PIPELINE STATUS",
    "📂 RAW INTEL",
    "🌐 DATA SOURCES"
])

# TAB 1: RADAR DISPLAY (Principal)
with tab_radar:
    if not target and not st.session_state.dossie:
        # Tela inicial
        st.markdown("""
        <div style="text-align:center;padding:100px 20px;">
            <div style="font-size:5rem;opacity:0.3;margin-bottom:20px;">⌖</div>
            <div class="radar-header" style="font-size:2.5rem;opacity:0.6;">NO TARGET ACQUIRED</div>
            <div style="font-family:JetBrains Mono;font-size:0.9rem;color:#64748B;margin-top:15px;letter-spacing:2px;">
                INSIRA AS COORDENADAS NO PAINEL LATERAL PARA INICIAR
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        
        # Cards informativos
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(render_status_card(
                "🗯️ RECON OPERACIONAL",
                "Busca em múltiplas fontes governamentais",
                "info",
                ["CAR/SICAR", "INCRA SNCR", "IBGE Agro"]
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(render_status_card(
                "💰 INTELIGÊNCIA FINANCEIRA",
                "Dados oficiais sem estimações",
                "info",
                ["CVM", "B3/CETIP", "ComexStat"]
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(render_status_card(
                "🧠 ANÁLISE ESTRATÉGICA",
                "Gemini 2.5 Pro com thinking mode",
                "info",
                ["1M tokens", "Deep reasoning", "Validação cruzada"]
            ), unsafe_allow_html=True)
    
    elif st.session_state.processing:
        # Tela de processamento
        st.markdown(f"""
        <div style="text-align:center;padding:50px 20px;">
            <div class="radar-header" style="font-size:2rem;">MISSÃO EM ANDAMENTO</div>
            <div style="font-family:JetBrains Mono;color:#38BDF8;margin-top:10px;">
                ALVO: {target.upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(render_progress_bar(st.session_state.current_progress, "PROGRESSÃO GERAL"), unsafe_allow_html=True)
        
        # Exibe steps em tempo real
        if st.session_state.pipeline_steps:
            st.markdown(render_step_indicator(st.session_state.pipeline_steps), unsafe_allow_html=True)
            
            # Último step ativo
            for step in reversed(st.session_state.pipeline_steps):
                if step.status == 'running':
                    st.markdown(render_status_card(
                        f"{step.icone} {step.titulo}",
                        "Processando...",
                        "running"
                    ), unsafe_allow_html=True)
                    break
    
    elif st.session_state.dossie:
        # Exibe resultados
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        
        # Header com score
        col_nome, col_score = st.columns([3, 1])
        
        with col_nome:
            st.markdown(f'<div class="radar-header" style="font-size:2.2rem;">{nome.upper()}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-family:JetBrains Mono;color:#10B981;font-size:0.85rem;margin-top:8px;">✅ TARGET LOCKED | {d.timestamp_geracao}</div>', unsafe_allow_html=True)
        
        with col_score:
            tier_colors = {
                "HUNTER-KILLER": "#10B981",
                "HIGH-VALUE": "#38BDF8",
                "MEDIUM": "#F59E0B",
                "LOW-PRIORITY": "#64748B"
            }
            tier_color = tier_colors.get(d.sas_result.tier.value, "#64748B")
            
            st.markdown(f"""
            <div style="text-align:right;padding:15px;background:rgba(30,41,59,0.4);border-radius:8px;border-left:4px solid {tier_color};">
                <div style="color:#94A3B8;font-size:0.7rem;font-family:JetBrains Mono;letter-spacing:1px;">SAS SCORE</div>
                <div style="color:{tier_color};font-size:2.5rem;font-weight:700;font-family:Rajdhani;line-height:1;margin:5px 0;">{d.sas_result.score}</div>
                <div style="color:{tier_color};font-size:0.9rem;font-weight:700;font-family:Rajdhani;letter-spacing:1px;">{d.sas_result.tier.value}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        
        # Métricas principais
        m1, m2, m3, m4 = st.columns(4)
        
        op = d.dados_operacionais
        fi = d.dados_financeiros
        
        with m1:
            ha = safe_float(op.hectares_total, 0)
            ha_color = "#10B981" if ha >= 5000 else "#F59E0B" if ha >= 2000 else "#64748B"
            st.markdown(f"""
            <div style="background:rgba(30,41,59,0.4);padding:15px;border-radius:6px;border-top:3px solid {ha_color};">
                <div style="color:#94A3B8;font-size:0.7rem;font-family:JetBrains Mono;letter-spacing:1px;margin-bottom:8px;">ÁREA TOTAL</div>
                <div style="color:{ha_color};font-size:1.8rem;font-weight:700;font-family:Rajdhani;">{ha:,.0f} <span style="font-size:1rem;">ha</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        with m2:
            cap = safe_float(fi.capital_social_estimado, 0)
            st.metric("CAPITAL SOCIAL", f"R$ {cap/1e6:.1f}M" if cap > 0 else "N/D")
        
        with m3:
            faz = safe_int(op.numero_fazendas, 0)
            st.metric("FAZENDAS", faz if faz > 0 else "N/D")
        
        with m4:
            func = safe_int(fi.funcionarios_estimados, 0)
            st.metric("FUNCIONÁRIOS", f"~{func}" if func > 0 else "N/D")
        
        st.markdown('<div class="section-header">⚙️ DADOS OPERACIONAIS</div>', unsafe_allow_html=True)
        
        op_col1, op_col2 = st.columns(2)
        
        with op_col1:
            st.markdown(render_status_card(
                "🌾 CULTURAS",
                ", ".join(op.culturas[:5]) if op.culturas else "Não identificado",
                "success" if op.culturas else "warning",
                conf=op.confianca
            ), unsafe_allow_html=True)
        
        with op_col2:
            st.markdown(render_status_card(
                "🗺️ REGIÕES",
                ", ".join(op.regioes_atuacao[:3]) if op.regioes_atuacao else "Não identificado",
                "success" if op.regioes_atuacao else "warning",
                conf=op.confianca
            ), unsafe_allow_html=True)
        
        # Seções de análise
        if d.secoes_analise:
            st.markdown('<div class="section-header">📊 ANÁLISE ESTRATÉGICA</div>', unsafe_allow_html=True)
            
            for secao in d.secoes_analise:
                with st.expander(f"{secao.icone} {secao.titulo}", expanded=False):
                    st.markdown(secao.conteudo)
        
        # Download
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        csv_data = gerar_csv_report(d)
        st.download_button(
            "📥 BAIXAR RELATÓRIO (CSV)",
            csv_data,
            f"radar_fox3_{nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )

# TAB 2: PIPELINE STATUS
with tab_steps:
    st.markdown('<div class="section-header">🔍 STATUS DO PIPELINE</div>', unsafe_allow_html=True)
    
    if st.session_state.pipeline_steps:
        st.markdown(render_step_indicator(st.session_state.pipeline_steps), unsafe_allow_html=True)
        
        for step in st.session_state.pipeline_steps:
            status_map = {
                'success': 'success',
                'running': 'running',
                'error': 'error',
                'warning': 'warning'
            }
            
            st.markdown(render_status_card(
                f"{step.icone} Step {step.numero}: {step.titulo}",
                step.resumo or "Processado",
                status_map.get(step.status, 'info'),
                step.detalhes,
                step.confianca
            ), unsafe_allow_html=True)
    else:
        st.info("ℹ️ Nenhuma missão executada ainda")

# TAB 3: RAW INTEL
with tab_intel:
    st.markdown('<div class="section-header">📂 DADOS BRUTOS</div>', unsafe_allow_html=True)
    
    if st.session_state.dossie:
        st.json(json.loads(json.dumps(st.session_state.dossie, default=lambda o: o.__dict__)))
    else:
        st.info("ℹ️ Execute uma missão para visualizar dados brutos")

# TAB 4: DATA SOURCES
with tab_sources:
    st.markdown('<div class="section-header">🌐 FONTES DE DADOS</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Fontes Governamentais Oficiais
    
    **🌾 Propriedades Rurais**
    - CAR/SICAR - Sistema Nacional de Cadastro Ambiental Rural
    - INCRA SNCR - Sistema Nacional de Cadastro Rural
    - IBGE - Produtividade e Dados Agrícolas Regionais
    
    **💰 Dados Financeiros**
    - CVM - Comissão de Valores Mobiliários
    - B3/CETIP - Certificados de Recebíveis do Agronegócio (CRA)
    - Receita Federal - Dados Cadastrais (CNPJ)
    
    **🌍 Comércio Exterior**
    - ComexStat (MDIC) - Estatísticas de Exportação
    - MAPA - Certificações e Registros Sanitários
    
    **📰 Inteligência de Mercado**
    - Google News - Notícias recentes
    - LinkedIn - Estrutura organizacional (via API oficial)
    - CVM - Fatos Relevantes de empresas de capital aberto
    """)
    
    if st.session_state.dossie and hasattr(st.session_state.dossie, 'fontes_consultadas'):
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        st.markdown("### Fontes Consultadas na Última Missão")
        
        for fonte in st.session_state.dossie.fontes_consultadas:
            status = fonte.get('status', 'unknown')
            st.markdown(render_status_card(
                fonte.get('fonte', 'Unknown'),
                fonte.get('nota', 'Consultado'),
                'success' if status == 'success' else 'warning'
            ), unsafe_allow_html=True)

# ==============================================================================
# PROCESSAMENTO
# ==============================================================================

if btn_fire and target and api_key:
    st.session_state.processing = True
    st.session_state.dossie = None
    st.session_state.pipeline_steps = []
    st.session_state.current_progress = 0.0
    st.rerun()

if st.session_state.processing:
    try:
        # Callbacks para atualizar UI
        def progress_callback(progress: float, msg: str):
            st.session_state.current_progress = progress
        
        def step_callback(step: PipelineStepResult):
            # Atualiza ou adiciona step
            found = False
            for i, s in enumerate(st.session_state.pipeline_steps):
                if s.numero == step.numero:
                    st.session_state.pipeline_steps[i] = step
                    found = True
                    break
            if not found:
                st.session_state.pipeline_steps.append(step)
        
        # Executa processamento
        dossie = gerar_dossie_completo(
            target,
            api_key,
            target_cnpj,
            progress_cb=progress_callback,
            step_cb=step_callback
        )
        
        st.session_state.dossie = dossie
        st.session_state.processing = False
        st.session_state.current_progress = 1.0
        st.success("✅ Missão concluída com sucesso!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro durante processamento: {str(e)}")
        st.session_state.processing = False
        st.session_state.current_progress = 0.0
