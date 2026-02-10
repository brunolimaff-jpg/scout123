"""
app.py — RADAR FOX-3 v2.0 | Intelligence System
Versão atualizada com validação robusta e ZERO falhas
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time, random, json, csv, io
from datetime import datetime

# Importações dos serviços COM VALIDAÇÃO DEFENSIVA
try:
    from services.dossier_orchestrator import gerar_dossie_completo
    from services.cnpj_service import formatar_cnpj, validar_cnpj, limpar_cnpj
    from services.market_estimator import calcular_sas  # USA O ATUALIZADO
    from services.data_validator import safe_float, safe_int, safe_str  # NOVO
    from services.cache_service import cache
    from services.request_queue import request_queue
    from utils.market_intelligence import ARGUMENTOS_CONCORRENCIA
    from utils.pdf_export import gerar_pdf
    from scout_types import DossieCompleto, Tier, QualityLevel
except ImportError as e:
    st.error(f"⚠️ Erro ao importar módulos: {e}")
    st.stop()

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def _sj(lst, n=None):
    if not lst: return ''
    items = lst[:n] if n else lst
    return ', '.join(str(x) if not isinstance(x, dict) else x.get('nome', x.get('titulo', x.get('sistema', str(x)))) for x in items)

def _fmt_movimento(m):
    if isinstance(m, str):
        if m.startswith('{'):
            try: m = json.loads(m)
            except: return m
        else: return m
    if isinstance(m, dict):
        tipo = m.get('tipo', '')
        valor = m.get('valor', '')
        det = m.get('detalhes', '')
        parts = []
        if tipo: parts.append(f"**{tipo}**")
        if valor and str(valor) != '0': parts.append(f"R${valor}")
        if det: parts.append(f"— {det}")
        return " ".join(parts) if parts else str(m)
    return str(m)

def gerar_csv_report(d):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Protocolo RADAR", "Relatorio de Combate (BDA)"])
    writer.writerow(["Alvo", d.dados_operacionais.nome_grupo or d.empresa_alvo])
    writer.writerow(["Score Tatico", d.sas_result.score])
    writer.writerow(["Classificacao", d.sas_result.tier.value])
    return output.getvalue()

# LOGS DE COMBATE AÉREO
LOGS_COMBATE = [
    "📡 SYSTEM CHECK: RADAR ON. COMMs ON.",
    "🔄 CALIBRATING SENSORS... (Ajustando Frequência)",
    "⚠️ BOGEY DETECTED ON SECTOR 4. (Alvo Detectado)",
    "📶 ESTABLISHING DATALINK WITH AWACS... (Conectando Base)",
    "⚙️ COMPUTING INTERCEPT GEOMETRY... (Calculando Rota)",
    "🔍 IDENTIFYING IFF (FRIEND OR FOE)... (Validando CNPJ)",
    "🔒 HARD LOCK ACQUIRED - TONE! (Mira Travada)",
    "🦊 FOX 3 AWAY! (Míssil de Inteligência Disparado)",
    "⏱️ TIME TO IMPACT: CALCULATING...",
    "🔥 ANALYZING HEAT SIGNATURE... (Varrendo Financeiro)",
    "👤 SCANNING COCKPIT CREW... (Identificando Decisores)",
    "💥 SPLASH ONE! GOOD EFFECT ON TARGET. (Extração Concluída)",
    "📥 SECURING FLIGHT RECORDER DATA... (Baixando Dossiê)"
]

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="RADAR | FOX-3", page_icon="✈️", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# CSS — HUD AVIATION THEME
# ==============================================================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Rajdhani:wght@500;600;700;900&display=swap');

.stApp {
    background-color: #0F172A !important;
    color: #E2E8F0 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

section[data-testid="stSidebar"] {
    background-color: #1E293B !important;
    border-right: 2px solid #334155 !important;
}

div[data-testid="stMetric"], .intel-card {
    background-color: #1E293B !important;
    border: 1px solid #475569 !important;
    border-radius: 2px !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    position: relative;
}

div[data-testid="stMetric"]::before {
    content: ''; position: absolute; top: 0; left: 0; width: 10px; height: 10px;
    border-top: 2px solid #38BDF8; border-left: 2px solid #38BDF8;
}

div[data-testid="stMetric"]::after {
    content: ''; position: absolute; bottom: 0; right: 0; width: 10px; height: 10px;
    border-bottom: 2px solid #38BDF8; border-right: 2px solid #38BDF8;
}

div[data-testid="stMetric"] label { 
    color: #64748B !important; 
    font-family: 'JetBrains Mono'; 
    font-size: 0.7rem !important; 
    letter-spacing: 1px; 
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #38BDF8 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

.stButton>button {
    background: linear-gradient(180deg, #F59E0B, #D97706) !important;
    color: #0F172A !important;
    border: 1px solid #FBBF24 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.1rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
    animation: pulse-border 2s infinite;
}

.stButton>button:hover {
    background: #FBBF24 !important;
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.6) !important;
    transform: scale(1.02);
}

@keyframes pulse-border {
    0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }
    100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

.stTextInput>div>div>input {
    background-color: #0F172A !important;
    color: #38BDF8 !important;
    border: 1px solid #334155 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 1px;
}

.stTextInput>div>div>input:focus {
    border-color: #38BDF8 !important;
    box-shadow: 0 0 0 1px #38BDF8 !important;
}

.radar-header {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    font-size: 3rem;
    color: #38BDF8;
    letter-spacing: 6px;
    margin: 0;
    line-height: 1;
    text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
}

.radar-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #64748B;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 5px;
    border-top: 1px solid #334155;
    padding-top: 5px;
    width: 100%;
}

.section-header {
    font-family: 'Rajdhani', sans-serif;
    color: #E2E8F0;
    font-size: 1.4rem;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 2px solid #334155;
    padding-bottom: 5px;
    margin-top: 30px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
}

.section-header::before {
    content: '✈'; margin-right: 12px; color: #F59E0B; transform: rotate(90deg);
}

.status-panel {
    background: #020617;
    border: 1px solid #1E293B;
    padding: 10px;
    font-family: 'JetBrains Mono';
    font-size: 0.7rem;
    color: #94A3B8;
    margin-bottom: 20px;
}

.stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 2px solid #334155; }

.stTabs [data-baseweb="tab"] {
    background-color: #1E293B; color: #64748B; border: none; margin-right: 2px;
    font-family: 'Rajdhani'; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
}

.stTabs [aria-selected="true"] {
    background-color: #38BDF8 !important; color: #0F172A !important;
}

.neon-divider { 
    height: 1px; 
    background: linear-gradient(90deg, transparent, #334155, transparent); 
    margin: 20px 0; 
}

.kill-metric { 
    font-family: 'Rajdhani', sans-serif; 
    font-size: 3rem; 
    color: #FFF; 
    font-weight: 700; 
    line-height: 1; 
}

.bda-card { 
    background: #1E293B; 
    border-left: 4px solid #F59E0B; 
    padding: 15px; 
    margin-bottom: 10px; 
}
</style>""", unsafe_allow_html=True)

# Inicializa Session State
for k in ['dossie','logs','historico','step_results']:
    if k not in st.session_state: st.session_state[k] = []

# ==============================================================================
# SIDEBAR — COCKPIT DE CONTROLE
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:10px 0 20px 0;">
        <div style="font-size:3rem;margin-bottom:0px;">📡</div>
        <div class="radar-header">RADAR</div>
        <div class="radar-subtitle">
            SYSTEM: ONLINE<br>
            ALTITUDE: FL-500<br>
            MODE: HUNTER-KILLER<br>
            v2.0 | VALIDATED
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="status-panel">
        <div>PWR: <span style="color:#10B981">NOMINAL</span></div>
        <div>LINK: <span style="color:#10B981">SECURE</span></div>
        <div>WEAPON: <span style="color:#F59E0B">FOX-3 READY</span></div>
        <div>VALIDATION: <span style="color:#10B981">ACTIVE</span></div>
    </div>""", unsafe_allow_html=True)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        api_key = st.text_input("🔑 API KEY", type="password")
    
    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Rajdhani\';font-weight:700;color:#38BDF8;margin-bottom:5px;">COORDINATES (ALVO)</div>', unsafe_allow_html=True)
    target = st.text_input("Empresa", placeholder="Ex: GRUPO SCHEFFER", label_visibility="collapsed")
    
    st.markdown('<div style="font-family:\'Rajdhani\';font-weight:700;color:#38BDF8;margin-bottom:5px;margin-top:10px;">ID (CNPJ - OPCIONAL)</div>', unsafe_allow_html=True)
    target_cnpj = st.text_input("CNPJ", placeholder="XX.XXX.XXX/XXXX-XX", label_visibility="collapsed")
    
    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    
    btn_label = "🦊 FOX 3 - DISPARAR" if target else "⛔ AGUARDANDO ALVO"
    btn = st.button(btn_label, type="primary", disabled=not target, use_container_width=True)

    st.markdown('<div style="position:fixed;bottom:10px;font-size:0.6rem;color:#475569;font-family:\'JetBrains Mono\';">RADAR SYSTEM © 2026 | CLASSIFIED</div>', unsafe_allow_html=True)

# ==============================================================================
# MAIN — FLIGHT DECK (HUD)
# ==============================================================================
tab_radar, tab_intel = st.tabs(["📡 RADAR DISPLAY", "📂 INTEL PACKET"])

with tab_radar:
    # TELA DE ESPERA
    if not target and not st.session_state.dossie:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;opacity:0.5;">
            <div style="font-size:4rem;">⌖</div>
            <div style="font-family:'Rajdhani';font-size:1.5rem;color:#64748B;letter-spacing:2px;">NO TARGET ACQUIRED</div>
            <div style="font-family:'JetBrains Mono';font-size:0.8rem;color:#475569;margin-top:10px;">
                ENTER COORDINATES IN SIDEBAR TO ENGAGE.
            </div>
        </div>""", unsafe_allow_html=True)
        
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown('<div class="bda-card"><b>🗺️ RECON</b><br><small>Hectares, Culturas, Mapas</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="bda-card"><b>💰 FINOPS</b><br><small>CRAs, Dívidas, M&A</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="bda-card"><b>🤝 HUMAN INTEL</b><br><small>Decisores, LinkedIn</small></div>', unsafe_allow_html=True)

    # SEQUÊNCIA DE DISPARO
    if btn and target:
        st.session_state.dossie = None; st.session_state.logs = []
        with st.status("🚀 INITIATING COMBAT SEQUENCE...", expanded=True) as status:
            log_container = st.empty()
            log_history = ""
            for i, log in enumerate(LOGS_COMBATE):
                log_history += f"> {log}\n"
                log_container.code(log_history, language="bash")
                if i == len(LOGS_COMBATE) - 1:
                    st.write("⚙️ DECRYPTING INTEL... (Aguarde o processamento final)")
                else:
                    time.sleep(random.uniform(0.4, 1.2))
            
            try:
                dossie = gerar_dossie_completo(target, api_key, target_cnpj, log_cb=lambda m: None) 
                st.session_state.dossie = dossie
                status.update(label="✅ MISSION ACCOMPLISHED (TARGET NEUTRALIZED)", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                st.error(f"❌ WEAPON MALFUNCTION: {e}")
                status.update(label="⛔ MISSION FAILED", state="error")

    # RESULTADO
    if st.session_state.dossie:
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        
        col_hud1, col_hud2 = st.columns([3, 1])
        with col_hud1:
            st.markdown(f'<div class="radar-header" style="font-size:2.5rem;text-align:left;">{nome.upper()}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-family:\'JetBrains Mono\';color:#10B981;">✅ HARD LOCK CONFIRMED | TSTAMP: {d.timestamp_geracao}</div>', unsafe_allow_html=True)
        
        with col_hud2:
            st.markdown(f"""
            <div style="text-align:right;border-right:4px solid #38BDF8;padding-right:10px;">
                <div style="color:#64748B;font-size:0.7rem;font-family:'JetBrains Mono';">SCORE SAS</div>
                <div class="kill-metric" style="color:#38BDF8;">{d.sas_result.score}</div>
                <div style="color:#F59E0B;font-size:0.8rem;font-weight:700;">{d.sas_result.tier.value}</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        
        # Usa safe_float e safe_int para NUNCA falhar
        op = d.dados_operacionais
        fi = d.dados_financeiros
        
        hectares = safe_float(op.hectares_total, 0)
        ha_color = "#10B981" if hectares >= 5000 else "#EF4444"
        
        capital = safe_float(fi.capital_social_estimado, 0)
        fazendas = safe_int(op.numero_fazendas, 0)
        funcionarios = safe_int(fi.funcionarios_estimados, 0)
        
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div style="border-top:2px solid {ha_color};padding-top:5px;"><div style="color:#64748B;font-size:0.7rem;">ÁREA TOTAL</div><div style="font-size:1.5rem;font-weight:700;color:{ha_color};">{hectares:,.0f} ha</div></div>', unsafe_allow_html=True)
        k2.metric("CAPITAL SOCIAL", f"R${capital/1e6:.0f}M" if capital > 0 else "N/A")
        k3.metric("FAZENDAS", fazendas if fazendas > 0 else "N/A")
        k4.metric("FUNCIONÁRIOS", f"~{funcionarios}" if funcionarios > 0 else "N/A")
        
        st.markdown('<div class="section-header">INFORMES DE INTELIGÊNCIA</div>', unsafe_allow_html=True)
        for sec in d.secoes_analise:
            with st.expander(f"{sec.icone} {sec.titulo}", expanded=True):
                st.markdown(sec.conteudo)
                
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        csv_data = gerar_csv_report(d)
        c_dl1, c_dl2 = st.columns([1,3])
        with c_dl1:
            st.download_button("📥 BAIXAR BDA (CSV)", csv_data, f"radar_{nome}.csv", "text/csv", use_container_width=True)

with tab_intel:
    st.markdown("### 📂 RAW DATA PACKET")
    if st.session_state.dossie:
        st.json(json.loads(json.dumps(st.session_state.dossie, default=lambda o: o.__dict__)))
    else:
        st.info("NO DATA AVAILABLE. EXECUTE FOX-3 FIRST.")
