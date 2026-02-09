"""
app.py — RAPTOR V1.0 | Intelligence System
Sistema Autonomo de Caca a Leads High-Ticket (>5.000 ha)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time, random, json, csv, io
from services.dossier_orchestrator import gerar_dossie_completo
from services.cnpj_service import formatar_cnpj, validar_cnpj, limpar_cnpj
from services.cache_service import cache
from services.request_queue import request_queue
from utils.market_intelligence import ARGUMENTOS_CONCORRENCIA
from utils.pdf_export import gerar_pdf
from scout_types import DossieCompleto, Tier, QualityLevel

# ==============================================================================
# 1. FUNÇÕES AUXILIARES DE FORMATAÇÃO
# ==============================================================================
def _sj(lst, n=None):
    if not lst: return ''
    items = lst[:n] if n else lst
    return ', '.join(
        str(x) if not isinstance(x, dict) else x.get('nome', x.get('titulo', x.get('sistema', str(x))))
        for x in items)

def _fmt_movimento(m):
    if isinstance(m, str):
        if m.startswith('{'):
            try: m = json.loads(m)
            except Exception: return m
        else:
            return m
    if isinstance(m, dict):
        tipo = m.get('tipo', m.get('titulo', ''))
        data = m.get('data', m.get('data_aprox', ''))
        valor = m.get('valor', '')
        det = m.get('detalhes', m.get('descricao', m.get('resumo', '')))
        parts = []
        if tipo: parts.append(f"**{tipo}**")
        if data: parts.append(f"({data})")
        if valor and str(valor) != 'Nao divulgado' and str(valor) != '0':
            if isinstance(valor, (int, float)): parts.append(f"R${valor/1e6:.1f}M")
            else: parts.append(str(valor))
        if det: parts.append(f"— {det}")
        return " ".join(parts) if parts else str(m)
    return str(m)

def _fmt_noticia(n):
    if isinstance(n, str): return n
    if isinstance(n, dict):
        t = n.get('titulo', '')
        r = n.get('resumo', '')
        d = n.get('data_aprox', n.get('data', ''))
        f = n.get('fonte', '')
        rel = n.get('relevancia', '')
        md = f"**{t}**" if t else ''
        if d: md += f" ({d})"
        if r: md += f"\n\n{r}"
        if f or rel:
            tags = []
            if f: tags.append(f"`{f.upper()}`")
            if rel: tags.append(f"{'🔴' if rel=='alta' else '🟡'} {rel.upper()}")
            md += f"\n\n{' '.join(tags)}"
        return md
    return str(n)

def gerar_csv_report(d):
    """Gera CSV do raptor_intelligence_report."""
    output = io.StringIO()
    writer = csv.writer(output)
    nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
    op = d.dados_operacionais; fi = d.dados_financeiros; cv = d.cadeia_valor; gr = d.grupo_economico
    ha = op.hectares_total or 0
    status = "ALVO DESCARTADO (BAIXO POTENCIAL)" if ha < 5000 else "ALVO CONFIRMADO - HIGH TICKET"
    writer.writerow(["Campo", "Valor"])
    writer.writerow(["Empresa", nome])
    writer.writerow(["Status RAPTOR", status])
    writer.writerow(["Score SAS", f"{d.sas_result.score}/1000"])
    writer.writerow(["Tier", d.sas_result.tier.value])
    writer.writerow(["Recomendacao", d.sas_result.recomendacao_comercial])
    writer.writerow(["Hectares", f"{ha:,}"])
    writer.writerow(["Culturas", _sj(op.culturas)])
    writer.writerow(["Regioes", _sj(op.regioes_atuacao)])
    writer.writerow(["Fazendas", op.numero_fazendas])
    writer.writerow(["Funcionarios", fi.funcionarios_estimados])
    writer.writerow(["Capital Estimado", f"R${fi.capital_social_estimado/1e6:.1f}M"])
    writer.writerow(["Faturamento", f"R${fi.faturamento_estimado/1e6:.1f}M" if fi.faturamento_estimado else "N/D"])
    writer.writerow(["Posicao Cadeia", cv.posicao_cadeia])
    writer.writerow(["Integracao Vertical", cv.integracao_vertical_nivel])
    writer.writerow(["Exporta", "Sim" if cv.exporta else "Nao"])
    writer.writerow(["Grupo Total Empresas", gr.total_empresas])
    writer.writerow(["CNPJ", d.cnpj or "N/D"])
    if d.dados_cnpj:
        writer.writerow(["Razao Social", d.dados_cnpj.razao_social])
        writer.writerow(["CNAE", d.dados_cnpj.cnae_principal])
        writer.writerow(["Municipio/UF", f"{d.dados_cnpj.municipio}/{d.dados_cnpj.uf}"])
    ts = d.tech_stack or {}
    erp = ts.get('erp_principal', {})
    writer.writerow(["ERP Detectado", erp.get('sistema', 'N/I')])
    writer.writerow(["Maturidade TI", ts.get('nivel_maturidade_ti', 'N/I')])
    writer.writerow(["Vertical", d.sas_result.vertical_detectada])
    writer.writerow(["Confidence", f"{d.sas_result.confidence_score:.0f}%"])
    writer.writerow(["Musculo", f"{d.sas_result.breakdown.musculo}/400"])
    writer.writerow(["Complexidade", f"{d.sas_result.breakdown.complexidade}/250"])
    writer.writerow(["Gente", f"{d.sas_result.breakdown.gente}/200"])
    writer.writerow(["Momento", f"{d.sas_result.breakdown.momento}/150"])
    decs = d.decisores.get('decisores', []) if d.decisores else []
    for i, dec in enumerate(decs[:5]):
        writer.writerow([f"Decisor {i+1}", f"{dec.get('nome','')} - {dec.get('cargo','')} [{dec.get('relevancia_erp','')}]"])
    return output.getvalue()

# ==============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="RAPTOR | Intelligence System", page_icon="🦖", layout="wide", initial_sidebar_state="expanded")

FRASES = [
    "Satelites reposicionados...", "Agentes infiltrados...", "Rastreando alvos financeiros...",
    "Deep Scan ativado...", "Mapeando cadeia de comando...", "Perfilando decisores...",
    "Interceptando tech stack...", "Varrendo grupo economico...", "Triangulando dados...",
    "Decodificando sinais de mercado...", "Compilando dossie tatico..."
]

# ==============================================================================
# 3. CSS — TITANIUM GREY THEME (VISIBILITY FIX)
# ==============================================================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;600;800&family=Orbitron:wght@500;700;900&display=swap');

/* --- BASE COLORS & FONTS --- */
/* Fundo Principal - Cinza Chumbo/Titânio (NÃO PRETO) */
.stApp {
    background-color: #1B2028 !important; 
    color: #E6EDF3 !important;
    font-family: 'Inter', sans-serif !important;
}

/* --- SIDEBAR --- */
/* Sidebar um pouco mais clara para contraste */
section[data-testid="stSidebar"] {
    background-color: #212630 !important; 
    border-right: 1px solid #363E4B !important;
}
section[data-testid="stSidebar"] .stMarkdown p, 
section[data-testid="stSidebar"] .stMarkdown span {
    color: #D1D5DB !important;
}

/* --- METRICS & CARDS --- */
div[data-testid="stMetric"] {
    background-color: #2A323E !important; /* Card background Lighter */
    border: 1px solid #3E4C5E !important;
    border-radius: 8px !important;
    padding: 15px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}
div[data-testid="stMetric"] label {
    color: #9CA3AF !important; /* Lighter grey for labels */
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
}

/* --- BUTTONS --- */
.stButton>button {
    background: linear-gradient(180deg, #10B981, #059669) !important; /* Emerald Tactical Green */
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    border-radius: 6px !important;
}
.stButton>button:hover {
    background: #10B981 !important;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.4) !important;
    transform: translateY(-2px);
}

/* --- INPUTS --- */
.stTextInput>div>div>input {
    background-color: #111419 !important; /* Darker input for contrast against grey bg */
    color: #FFFFFF !important;
    border: 1px solid #4B5563 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput>div>div>input:focus {
    border-color: #10B981 !important;
    box-shadow: 0 0 0 1px #10B981 !important;
}

/* --- TABS --- */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 2px solid #363E4B !important;
    gap: 20px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #9CA3AF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #10B981 !important;
    border-bottom: 2px solid #10B981 !important;
}

/* --- CUSTOM CLASSES --- */
.raptor-header {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 3.5rem;
    background: -webkit-linear-gradient(#22C55E, #15803D); /* Green Gradient */
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 6px;
    margin: 0;
    line-height: 1.1;
    text-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
}
.raptor-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    color: #9CA3AF;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 8px;
}
.raptor-version {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #10B981;
    letter-spacing: 2px;
    opacity: 0.9;
}

/* Status Indicators */
.status-online {
    background: #1B2028;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 8px 0;
}
.status-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: #10B981;
    border-radius: 50%;
    margin-right: 10px;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    animation: pulse 2s infinite;
}
@keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.6;} 100% {opacity: 1;} }

/* Card Styles */
.target-card {
    background-color: #2A323E; /* Lighter card background */
    border: 1px solid #3E4C5E;
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
    transition: transform 0.2s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.target-card:hover {
    border-color: #10B981;
    transform: translateY(-2px);
}
.intel-card {
    background-color: #2A323E;
    border-left: 4px solid #3E4C5E;
    padding: 16px;
    margin-bottom: 12px;
    border-radius: 0 6px 6px 0;
}

/* Typography & Layout */
.section-header {
    font-family: 'Orbitron', sans-serif;
    color: #F3F4F6;
    font-size: 1.2rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-bottom: 2px solid #374151;
    padding-bottom: 8px;
    margin-bottom: 20px;
    margin-top: 30px;
    display: flex;
    align-items: center;
}
.section-header::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #10B981;
    margin-right: 12px;
    transform: rotate(45deg);
}

.mono-text { font-family: 'JetBrains Mono', monospace; color: #9CA3AF; font-size: 0.85rem; }
.kill-metric { font-family: 'Orbitron', sans-serif; font-size: 2.0rem; color: #FFF; font-weight: 700; }

/* Dividers */
.neon-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #4B5563, transparent);
    margin: 30px 0;
}

/* Tier Badges */
.tier-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-family: 'Inter', sans-serif; font-weight: 700; font-size: 0.8em; letter-spacing: 1px; text-transform: uppercase; }
.tier-diamante { background: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid #3B82F6; }
.tier-ouro { background: rgba(234, 179, 8, 0.2); color: #FACC15; border: 1px solid #EAB308; }
.tier-prata { background: rgba(156, 163, 175, 0.2); color: #D1D5DB; border: 1px solid #9CA3AF; }
.tier-bronze { background: rgba(217, 119, 6, 0.2); color: #FB923C; border: 1px solid #D97706; }

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #1B2028; }
::-webkit-scrollbar-thumb { background: #4B5563; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #6B7280; }

</style>""", unsafe_allow_html=True)

# Inicializa Session State
for k in ['dossie','logs','historico','step_results']:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ['logs','historico','step_results'] else None

# ==============================================================================
# 4. SIDEBAR — COMMAND CENTER
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px 0;">
        <div style="font-size:3rem;margin-bottom:10px;">🦖</div>
        <div class="raptor-header" style="font-size:2rem;">RAPTOR</div>
        <div class="raptor-version">v1.0 | INTELLIGENCE SYSTEM</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="status-online">
        <span class="status-dot"></span>
        <span style="font-family:'JetBrains Mono',monospace;font-size:.75rem;color:#E6EDF3;letter-spacing:1px;">SISTEMA ONLINE</span>
        <span style="float:right;font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#9CA3AF;">OPERACIONAL</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#10B981;">✅ API KEY: AUTENTICADO</div>', unsafe_allow_html=True)
    except (FileNotFoundError, KeyError):
        api_key = st.text_input("🔑 API KEY", type="password", placeholder="Insira a chave Gemini...")
        if not api_key:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#EF4444;">⛔ ACESSO NEGADO</div>', unsafe_allow_html=True)
            st.stop()

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.7rem;color:#9CA3AF;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">🎯 DESIGNAÇÃO DO ALVO</div>', unsafe_allow_html=True)
    
    target = st.text_input("Empresa / Grupo", placeholder="Ex: SLC Agricola, Amaggi...", label_visibility="collapsed")
    target_cnpj = st.text_input("CNPJ (opcional)", placeholder="XX.XXX.XXX/XXXX-XX", label_visibility="collapsed")
    
    if target_cnpj:
        cl = limpar_cnpj(target_cnpj)
        if cl and validar_cnpj(cl):
            st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#10B981;margin-top:4px;">✅ VALIDADO: {formatar_cnpj(cl)}</div>', unsafe_allow_html=True)
        elif cl:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#EF4444;margin-top:4px;">⛔ CNPJ INVALIDO</div>', unsafe_allow_html=True)

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    btn = st.button("⚡ INICIAR CAÇA", type="primary", disabled=not target, use_container_width=True)

    if st.session_state.historico:
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.7rem;color:#9CA3AF;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">📋 ALVOS RECENTES</div>', unsafe_allow_html=True)
        for h in reversed(st.session_state.historico[-8:]):
            tc = "#10B981" if h['score']>=751 else "#F59E0B" if h['score']>=501 else "#9CA3AF"
            st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;padding:6px 0;border-bottom:1px solid #374151;"><span style="color:{tc};">●</span> <span style="color:#E5E7EB;">{h["empresa"][:20]}</span><span style="color:{tc};float:right;">{h["score"]}</span></div>', unsafe_allow_html=True)

    st.markdown('<div style="position:fixed;bottom:10px;font-family:\'JetBrains Mono\',monospace;font-size:.6rem;color:#6B7280;letter-spacing:1px;">RAPTOR © 2026 | CLASSIFIED</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. TABS PRINCIPAIS
# ==============================================================================
tab_scout, tab_compare, tab_arsenal = st.tabs(["🎯 CAÇA", "⚖️ COMPARADOR", "⚔️ ARSENAL"])

TIER_MAP = {"DIAMANTE 💎":"diamante","OURO 🥇":"ouro","PRATA 🥈":"prata","BRONZE 🥉":"bronze"}

with tab_scout:
    # -------------------------------------------------------------------------
    # TELA INICIAL (SEM ALVO)
    # -------------------------------------------------------------------------
    if not target and not st.session_state.dossie:
        st.markdown("""
        <div style="text-align:center;padding:50px 0 30px 0;">
            <div class="raptor-header">R.A.P.T.O.R.</div>
            <div class="raptor-subtitle">
                <b>R</b>astreamento <b>A</b>utomatizado de <b>P</b>otencial <b>T</b>op-tier e <b>O</b>portunidades <b>R</b>eais<br>
                SISTEMA AUTÔNOMO DE CAÇA A LEADS HIGH-TICKET (>5.000 ha)
            </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">🎯 DESIGNAÇÃO DO ALVO (ACESSO RÁPIDO)</div>', unsafe_allow_html=True)
        inp1, inp2, inp3 = st.columns([3, 2, 1])
        with inp1:
            target_main = st.text_input("Empresa / Grupo Econômico", placeholder="Ex: SLC Agrícola, Amaggi, Bom Futuro...", key="target_main")
        with inp2:
            cnpj_main = st.text_input("CNPJ (opcional)", placeholder="XX.XXX.XXX/XXXX-XX", key="cnpj_main")
        with inp3:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_main = st.button("⚡ INICIAR", type="primary", key="btn_main", use_container_width=True)

        # Sincronia de Inputs
        if target_main: target = target_main
        if cnpj_main: target_cnpj = cnpj_main
        if btn_main and target_main: btn = True; target = target_main; target_cnpj = cnpj_main

        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        
        # Grid de Funcionalidades (Agora com Cards Mais Claros)
        c1,c2,c3,c4 = st.columns(4)
        for col,icon,title,desc in [
            (c1,"🛰️","RECON","Hectares, culturas, verticalização"),
            (c2,"💰","FINANCEIRO","CRAs, Fiagros, M&A, governança"),
            (c3,"👔","DECISORES","C-Level, LinkedIn, perfil"),
            (c4,"💻","TECH STACK","ERP atual, vagas TI, maturidade")
        ]:
            with col:
                st.markdown(f"""
                <div class="target-card" style="text-align:center;min-height:160px;">
                    <div style="font-size:2rem;margin-bottom:10px;">{icon}</div>
                    <div style="font-family:'Orbitron',sans-serif;color:#E6EDF3;font-size:0.9rem;letter-spacing:1px;margin-bottom:8px;font-weight:700;">{title}</div>
                    <div style="font-family:'JetBrains Mono',monospace;color:#9CA3AF;font-size:0.75rem;">{desc}</div>
                </div>""", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # PROCESSAMENTO (LOADING)
    # -------------------------------------------------------------------------
    if btn and target:
        st.session_state.dossie = None; st.session_state.logs = []; st.session_state.step_results = []
        st.markdown(f'<div style="padding:10px 0;"><div style="font-family:\'Orbitron\',sans-serif;color:#10B981;font-size:1.4rem;letter-spacing:2px;text-transform:uppercase;">🎯 ALVO ADQUIRIDO: {target.upper()}</div><div class="mono-text" style="margin-top:4px;">Iniciando varredura completa...</div></div>', unsafe_allow_html=True)
        progress_bar = st.progress(0.0); status = st.empty(); step_ctn = st.container()
        
        def on_progress(p, m):
            progress_bar.progress(min(p, 1.0))
            status.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.85rem;"><span style="color:#10B981;">▶</span> <span style="color:#E5E7EB;">{m}</span> <span style="color:#9CA3AF;">— {random.choice(FRASES)}</span></div>', unsafe_allow_html=True)
        
        def on_step(s):
            st.session_state.step_results.append(s)
            ic = {"success":"✅","warning":"⚠️","error":"❌"}.get(s.status,"⏳")
            with step_ctn:
                border_color = "#10B981" if s.status == "success" else "#F59E0B" if s.status == "warning" else "#EF4444"
                bg_color = "#212630"
                h = f'<div style="background:{bg_color};border-left:4px solid {border_color};padding:14px;margin-bottom:10px;border-radius:0 4px 4px 0;">'
                h += f'<b style="color:#E6EDF3;">{ic} {s.step_number}. {s.step_name}</b>'
                h += f' <span style="float:right;color:#9CA3AF;font-family:\'JetBrains Mono\',monospace;">{s.tempo_segundos:.1f}s</span><br>'
                h += f'<span style="color:#9CA3AF;font-size:0.9rem;">{s.resumo}</span>'
                if s.confianca > 0:
                    cc = "#10B981" if s.confianca >= 0.7 else "#F59E0B" if s.confianca >= 0.4 else "#EF4444"
                    h += f' | <span style="color:{cc};font-size:0.8rem;">Conf: {s.confianca:.0%}</span>'
                h += '</div>'
                st.markdown(h, unsafe_allow_html=True)
        try:
            dossie = gerar_dossie_completo(target, api_key, target_cnpj, log_cb=lambda m: st.session_state.logs.append(m), progress_cb=on_progress, step_cb=on_step)
            st.session_state.dossie = dossie
            st.session_state.historico.append({'empresa': dossie.dados_operacionais.nome_grupo or target, 'score': dossie.sas_result.score, 'tier': dossie.sas_result.tier.value})
            st.rerun()
        except Exception as e:
            st.markdown(f'<div style="background:rgba(239, 68, 68, 0.1);border:1px solid rgba(239, 68, 68, 0.4);border-radius:6px;padding:16px;font-family:\'JetBrains Mono\',monospace;"><span style="color:#EF4444;font-weight:700;">⛔ FALHA NA OPERAÇÃO</span><br><span style="color:#E5E7EB;font-size:.85rem;">{e}</span></div>', unsafe_allow_html=True)
            import traceback; st.code(traceback.format_exc())

    # -------------------------------------------------------------------------
    # RESULTADO (DOSSÊ)
    # -------------------------------------------------------------------------
    if st.session_state.dossie:
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        op = d.dados_operacionais; fi = d.dados_financeiros; cv = d.cadeia_valor; gr = d.grupo_economico

        # === RAPTOR CLASSIFICATION ===
        ha_total = op.hectares_total or 0
        if ha_total > 0 and ha_total < 5000:
            st.error(f"⛔ ALVO DESCARTADO (BAIXO POTENCIAL) — {ha_total:,} ha < 5.000 ha. Foco RAPTOR: operações High-Ticket.")
        elif ha_total >= 5000:
            st.success(f"✅ ALVO CONFIRMADO — HIGH TICKET | {ha_total:,} ha | Potencial: ALTO")

        # HEADER DO DOSSÊ
        cs,ci,cq = st.columns([1,2,1])
        with cs:
            tier_cls = TIER_MAP.get(d.sas_result.tier.value, "bronze")
            st.markdown(f"""
            <div class="target-card" style="text-align:center;">
                <div style="font-family:'JetBrains Mono',monospace;color:#9CA3AF;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;">SCORE SAS</div>
                <div class="kill-metric">{d.sas_result.score}</div>
                <div style="font-family:'JetBrains Mono',monospace;color:#9CA3AF;font-size:.75rem;">/1000</div>
                <div class="tier-badge tier-{tier_cls}" style="margin-top:8px;">{d.sas_result.tier.value}</div>
            </div>""", unsafe_allow_html=True)
            if d.sas_result.recomendacao_comercial:
                st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#10B981;text-align:center;margin-top:8px;">🎯 {d.sas_result.recomendacao_comercial}</div>', unsafe_allow_html=True)
        
        with ci:
            st.markdown(f'<div style="padding:10px 0;"><div style="font-family:\'Orbitron\',sans-serif;color:#E6EDF3;font-size:1.8rem;letter-spacing:1px;font-weight:700;">{nome.upper()}</div></div>', unsafe_allow_html=True)
            badges = op.verticalizacao.listar_ativos()
            if badges:
                bh = " ".join([f'<span style="background:rgba(16, 185, 129, 0.1);color:#10B981;padding:4px 10px;border-radius:6px;font-family:\'Inter\',sans-serif;font-size:.75rem;margin-right:6px;border:1px solid rgba(16, 185, 129, 0.3);font-weight:600;">{b}</span>' for b in badges[:10]])
                st.markdown(bh, unsafe_allow_html=True)
            st.markdown(f'<div class="mono-text" style="margin-top:12px;">⏱️ {d.tempo_total_segundos:.0f}s | 📅 {d.timestamp_geracao}</div>', unsafe_allow_html=True)
        
        with cq:
            if d.quality_report:
                lc = {"EXCELENTE":"🟢","BOM":"🔵","ACEITÁVEL":"🟡","INSUFICIENTE":"🔴"}
                qc = lc.get(d.quality_report.nivel.value, '')
                st.markdown(f"""
                <div class="target-card" style="text-align:center;">
                    <div style="font-family:'JetBrains Mono',monospace;color:#9CA3AF;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;">QUALITY GATE</div>
                    <div class="kill-metric" style="font-size:1.4rem;">{d.quality_report.score_qualidade:.0f}%</div>
                    <div style="font-family:'JetBrains Mono',monospace;color:#E6EDF3;font-size:.8rem;margin-top:4px;">{qc} {d.quality_report.nivel.value}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # 1. PERFIL DO ALVO
        st.markdown('<div class="section-header">🏢 PERFIL DO ALVO</div>', unsafe_allow_html=True)
        cp1, cp2 = st.columns([2, 1])
        with cp1:
            # Construção de texto narrativo para facilitar leitura
            txt = f"**{nome}**"
            if fi.faturamento_estimado: txt += f" com faturamento estimado de **R${fi.faturamento_estimado/1e6:.0f}M**"
            elif fi.capital_social_estimado: txt += f" com capital de **R${fi.capital_social_estimado/1e6:.0f}M**"
            if op.hectares_total: txt += f" e **{op.hectares_total:,} hectares**"
            if op.culturas: txt += f" atuando em **{_sj(op.culturas)}**"
            if op.regioes_atuacao: txt += f" nas regiões **{_sj(op.regioes_atuacao)}**."
            
            st.markdown(f"<div style='font-size:1.1rem;line-height:1.6;color:#E6EDF3;'>{txt}</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if badges: st.markdown(f"**🏗️ Infraestrutura:** {', '.join(badges)}")
            if fi.funcionarios_estimados: st.markdown(f"**👥 Funcionários:** ~{fi.funcionarios_estimados:,}")
            if op.numero_fazendas: st.markdown(f"**🚜 Fazendas/Unidades:** {op.numero_fazendas}")
            if cv.posicao_cadeia: st.markdown(f"**⛓️ Posição na cadeia:** {cv.posicao_cadeia} | **Integração:** {cv.integracao_vertical_nivel}")
            if cv.exporta: st.markdown(f"**🚢 Exportação:** {_sj(cv.mercados_exportacao, 5)}")
            if fi.resumo_financeiro: st.info(fi.resumo_financeiro)
            
        with cp2:
            if d.dados_cnpj:
                dc = d.dados_cnpj
                st.markdown(f"""
                <div style="background:#212630;border:1px solid #374151;border-radius:6px;padding:15px;">
                    <div style="font-size:0.8rem;color:#9CA3AF;margin-bottom:4px;">CNPJ</div>
                    <div style="font-family:'JetBrains Mono';font-size:0.9rem;color:#E6EDF3;margin-bottom:10px;">{formatar_cnpj(dc.cnpj)}</div>
                    <div style="font-size:0.8rem;color:#9CA3AF;margin-bottom:4px;">CNAE</div>
                    <div style="font-size:0.9rem;color:#E6EDF3;margin-bottom:10px;">{dc.cnae_principal}</div>
                    <div style="font-size:0.8rem;color:#9CA3AF;margin-bottom:4px;">CAPITAL SOCIAL</div>
                    <div style="font-size:0.9rem;color:#E6EDF3;margin-bottom:10px;">R${dc.capital_social:,.0f}</div>
                    <div style="font-size:0.8rem;color:#9CA3AF;margin-bottom:4px;">LOCALIZAÇÃO</div>
                    <div style="font-size:0.9rem;color:#E6EDF3;margin-bottom:10px;">{dc.municipio}/{dc.uf}</div>
                    <div style="font-size:0.8rem;color:#9CA3AF;margin-bottom:4px;">QSA</div>
                    <div style="font-size:0.9rem;color:#E6EDF3;">{len(dc.qsa)} sócios encontrados</div>
                </div>""", unsafe_allow_html=True)

        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # 2. MOVIMENTOS FINANCEIROS
        movs = fi.movimentos_financeiros; cras = fi.cras_emitidos; fiagros = fi.fiagros_relacionados
        if movs or cras or fiagros:
            st.markdown('<div class="section-header">💰 MOVIMENTOS FINANCEIROS</div>', unsafe_allow_html=True)
            cm, cf2 = st.columns(2)
            with cm:
                if movs:
                    for m in movs: st.markdown(f"🏦 {_fmt_movimento(m)}")
            with cf2:
                if cras:
                    st.markdown("**CRAs:**")
                    for c in cras: st.markdown(f"📜 {_fmt_movimento(c)}")
                if fiagros:
                    st.markdown("**Fiagros:**")
                    for f in fiagros: st.markdown(f"📈 {_fmt_movimento(f)}")
                if fi.parceiros_financeiros:
                    st.markdown("**Parceiros:**")
                    for p in fi.parceiros_financeiros: st.markdown(f"🤝 {_fmt_movimento(p)}")
            st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # 3. METRÍCAS PRINCIPAIS
        st.markdown('<div class="section-header">📊 RAIO-X DA OPERAÇÃO</div>', unsafe_allow_html=True)
        mc = st.columns(6)
        mc[0].metric("ÁREA", f"{op.hectares_total:,} ha" if op.hectares_total else "N/D")
        mc[1].metric("EFETIVO", f"{fi.funcionarios_estimados:,}" if fi.funcionarios_estimados else "N/D")
        mc[2].metric("CAPITAL", f"R${fi.capital_social_estimado/1e6:.1f}M" if fi.capital_social_estimado else "N/D")
        mc[3].metric("CULTURAS", _sj(op.culturas, 3) if op.culturas else "N/D")
        mc[4].metric("FAZENDAS", str(op.numero_fazendas) if op.numero_fazendas else "N/D")
        mc[5].metric("GRUPO", f"{gr.total_empresas} emp" if gr.total_empresas else "N/D")
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # 4. DECISORES
        decs = d.decisores.get('decisores', []) if d.decisores else []
        if decs:
            st.markdown('<div class="section-header">👔 DECISORES-CHAVE</div>', unsafe_allow_html=True)
            for dec in decs:
                rel = dec.get('relevancia_erp','')
                ic = "🔴" if rel == 'alta' else "🟡" if rel == 'media' else "⚪"
                
                with st.container():
                    st.markdown(f"""
                    <div style="background:#212630;padding:15px;border-radius:6px;margin-bottom:10px;border-left:4px solid {'#EF4444' if rel=='alta' else '#F59E0B'};">
                        <div style="display:flex;justify-content:space-between;">
                            <div style="font-weight:700;font-size:1.05rem;color:#E6EDF3;">{dec.get('nome','')}</div>
                            <div style="font-family:'JetBrains Mono';font-size:0.75rem;color:#9CA3AF;text-transform:uppercase;">{rel} RELEVANCE</div>
                        </div>
                        <div style="color:#10B981;font-size:0.9rem;margin-bottom:5px;">{dec.get('cargo','')}</div>
                        <div style="font-size:0.85rem;color:#D1D5DB;">
                            {'🎓 ' + dec['formacao'] if dec.get('formacao') else ''} 
                            {' | ⏱️ ' + dec['tempo_cargo'] if dec.get('tempo_cargo') else ''}
                        </div>
                        {f'<div style="margin-top:5px;"><a href="{dec["linkedin"]}" target="_blank" style="text-decoration:none;color:#60A5FA;font-size:0.8rem;">🔗 LinkedIn Profile</a></div>' if dec.get('linkedin') else ''}
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # 5. TECH STACK
        ts = d.tech_stack if d.tech_stack else {}
        if ts:
            st.markdown('<div class="section-header">💻 TECH STACK DETECTADO</div>', unsafe_allow_html=True)
            erp = ts.get('erp_principal', {})
            ct1, ct2 = st.columns(2)
            with ct1:
                st.markdown(f"""
                <div class="target-card">
                    <div style="font-size:0.8rem;color:#9CA3AF;text-transform:uppercase;">ERP PRINCIPAL</div>
                    <div style="font-size:1.4rem;font-weight:700;color:#60A5FA;margin-bottom:4px;">{erp.get('sistema', 'Não Identificado')}</div>
                    <div style="font-size:0.9rem;color:#D1D5DB;">{erp.get('versao','')}</div>
                    <hr style="border-color:#374151;margin:10px 0;">
                    <div style="font-size:0.8rem;color:#9CA3AF;">Fonte: {erp.get('fonte_evidencia','N/A')}</div>
                </div>
                """, unsafe_allow_html=True)
            with ct2:
                outros = ts.get('outros_sistemas', [])
                if outros:
                    st.markdown("**Outros sistemas:**")
                    for o in outros:
                        val = o.get('sistema','') if isinstance(o, dict) else o
                        st.markdown(f"- 🖥️ {val}")
                vagas = ts.get('vagas_ti_abertas', [])
                if vagas:
                    st.markdown("**Vagas TI Recentes:**")
                    for v in vagas:
                        tit = v.get('titulo','') if isinstance(v, dict) else v
                        st.markdown(f"- 📋 {tit}")

        # 6. GRUPO ECONÔMICO (Expander)
        if gr.total_empresas > 0:
            with st.expander(f"🏛️ ESTRUTURA SOCIETÁRIA ({gr.total_empresas} empresas)", expanded=False):
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    if gr.cnpj_matriz: st.markdown(f"**CNPJ Matriz:** `{gr.cnpj_matriz}`")
                    if hasattr(gr, 'holding_controladora'): st.markdown(f"**Holding:** {gr.holding_controladora}")
                with col_g2:
                    if gr.controladores: st.markdown(f"**Controladores:** {_sj(gr.controladores)}")
                
                filiais = gr.cnpjs_filiais
                if filiais:
                    st.markdown("---")
                    st.markdown(f"**Filiais ({len(filiais)}):**")
                    st.dataframe(pd.DataFrame(filiais), hide_index=True, use_container_width=True)

        # 7. GRÁFICO POLAR (Score Breakdown)
        st.markdown('<div class="section-header">📊 SCORE BREAKDOWN</div>', unsafe_allow_html=True)
        cch, ctb = st.columns([2, 1])
        with cch:
            b = d.sas_result.breakdown
            cats = ["MÚSCULO\n(Porte)","COMPLEXIDADE","GENTE\n(Gestão)","MOMENTO\n(Gov/Tech)"]
            vals = [b.musculo, b.complexidade, b.gente, b.momento]; maxs = [400,250,200,150]
            pcts = [v/m*100 for v,m in zip(vals, maxs)]
            
            fig = go.Figure(go.Scatterpolar(r=pcts+[pcts[0]], theta=cats+[cats[0]], fill='toself',
                line_color='#10B981', fillcolor='rgba(16, 185, 129, 0.2)', marker=dict(color='#10B981', size=8)))
            fig.update_layout(polar=dict(bgcolor='#1B2028',
                radialaxis=dict(visible=True, range=[0,100], ticksuffix="%", gridcolor='#374151', linecolor='#374151', tickfont=dict(color='#9CA3AF', family='JetBrains Mono')),
                angularaxis=dict(gridcolor='#374151', linecolor='#374151', tickfont=dict(color='#E6EDF3', family='Inter', size=11, weight=700))),
                showlegend=False, height=350, margin=dict(l=60,r=60,t=20,b=20),
                paper_bgcolor='#1B2028', plot_bgcolor='#1B2028', font=dict(family='Inter', color='#D1D5DB'))
            st.plotly_chart(fig, use_container_width=True)
        
        with ctb:
            st.markdown(f"""
            <div style="background:#212630;padding:15px;border-radius:6px;border:1px solid #374151;">
                <div style="display:flex;justify-content:space-between;border-bottom:1px solid #374151;padding-bottom:5px;margin-bottom:5px;">
                    <span style="color:#9CA3AF;">MÚSCULO</span><span style="color:#FFF;">{b.musculo}/400</span>
                </div>
                <div style="display:flex;justify-content:space-between;border-bottom:1px solid #374151;padding-bottom:5px;margin-bottom:5px;">
                    <span style="color:#9CA3AF;">COMPLEX.</span><span style="color:#FFF;">{b.complexidade}/250</span>
                </div>
                <div style="display:flex;justify-content:space-between;border-bottom:1px solid #374151;padding-bottom:5px;margin-bottom:5px;">
                    <span style="color:#9CA3AF;">GENTE</span><span style="color:#FFF;">{b.gente}/200</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#9CA3AF;">MOMENTO</span><span style="color:#FFF;">{b.momento}/150</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if d.sas_result.justificativas:
                with st.expander("🔍 JUSTIFICATIVAS", expanded=False):
                    for j in d.sas_result.justificativas:
                        st.markdown(f"- {j}")

        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # 8. INTELIGÊNCIA ESTRATÉGICA (TEXTOS GERADOS)
        st.markdown('<div class="section-header">🧠 ANÁLISE ESTRATÉGICA (GEMINI)</div>', unsafe_allow_html=True)
        for sec in d.secoes_analise:
            with st.expander(f"{sec.icone} {sec.titulo}", expanded=True):
                st.markdown(sec.conteudo)

        # 9. EXPORTS
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📤 EXPORTAR RELATÓRIO</div>', unsafe_allow_html=True)
        
        md = f"# RAPTOR Intelligence Report: {nome}\n**Score:** {d.sas_result.score}/1000 — {d.sas_result.tier.value}\n\n"
        for sec in d.secoes_analise: md += f"## {sec.icone} {sec.titulo}\n\n{sec.conteudo}\n\n---\n\n"
        csv_data = gerar_csv_report(d)
        jd = json.dumps({"empresa":nome,"score":d.sas_result.score}, indent=2, ensure_ascii=False, default=str)
        
        ex1,ex2,ex3,ex4 = st.columns(4)
        with ex1:
            try:
                pp = gerar_pdf(d); pf = open(pp, "rb")
                st.download_button("📕 BAIXAR PDF", pf.read(), f"raptor_{nome}.pdf", "application/pdf", use_container_width=True)
            except: st.error("Erro PDF")
        with ex2:
            st.download_button("📊 BAIXAR CSV", csv_data, f"raptor_{nome}.csv", "text/csv", use_container_width=True)
        with ex3:
            st.download_button("📝 BAIXAR MD", md, f"raptor_{nome}.md", "text/markdown", use_container_width=True)
        with ex4:
            st.download_button("🔧 BAIXAR JSON", jd, f"raptor_{nome}.json", use_container_width=True)

# ==============================================================================
# 6. TAB: COMPARADOR
# ==============================================================================
with tab_compare:
    st.markdown('<div class="section-header">⚖️ COMPARADOR TÁTICO</div>', unsafe_allow_html=True)
    if len(st.session_state.historico) < 2:
        st.info("⚠️ Investigue pelo menos 2 alvos para habilitar a comparação.")
    else:
        hist = st.session_state.historico[-5:]
        st.dataframe(pd.DataFrame(hist), hide_index=True, use_container_width=True)
        
        colors = ['#10B981' if h['score']>=751 else '#F59E0B' if h['score']>=501 else '#9CA3AF' for h in hist]
        fig = go.Figure(go.Bar(x=[h['empresa'] for h in hist], y=[h['score'] for h in hist],
            marker_color=colors, text=[h['tier'] for h in hist], textposition='auto'))
        
        fig.update_layout(title="RANKING DE OPORTUNIDADES", paper_bgcolor='#1B2028', plot_bgcolor='#1B2028',
            font=dict(family='Inter', color='#D1D5DB'), yaxis=dict(gridcolor='#374151'), xaxis=dict(gridcolor='#374151'))
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 7. TAB: ARSENAL
# ==============================================================================
with tab_arsenal:
    st.markdown('<div class="section-header">⚔️ ARSENAL DE VENDAS</div>', unsafe_allow_html=True)
    tab_conc, tab_prof = st.tabs(["🗡️ MATADOR CONCORRÊNCIA", "🧠 PROFILER"])
    
    with tab_conc:
        conc = st.selectbox("Selecione o Concorrente:", list(ARGUMENTOS_CONCORRENCIA.keys()), format_func=lambda x: ARGUMENTOS_CONCORRENCIA[x]['nome'])
        if conc:
            info = ARGUMENTOS_CONCORRENCIA[conc]
            c1,c2 = st.columns(2)
            with c1:
                st.markdown('<div class="section-header" style="font-size:.9rem;color:#EF4444;">❌ PONTOS FRACOS</div>', unsafe_allow_html=True)
                for f in info['fraquezas']: st.markdown(f"- {f}")
            with c2:
                st.markdown('<div class="section-header" style="font-size:.9rem;color:#10B981;">✅ VANTAGEM SENIOR</div>', unsafe_allow_html=True)
                for v in info['senior_vantagem']: st.markdown(f"- {v}")

    with tab_prof:
        tipo = st.selectbox("PERFIL DO ALVO:", ["Grande Grupo (10k+ ha)","Usina","Cooperativa","Pecuaria","HF","Florestal"])
        perfis = {
            "Grande Grupo (10k+ ha)":{"d":"CEO/CFO","p":"Corporativo, ROI, TCO","a":"Business case, referencias","o":"Ja tenho ERP"},
            "Usina":{"d":"Dir. Industrial/CFO","p":"Tecnico, CTT, RenovaBio","a":"Demo tecnica, POC manutencao","o":"TOTVS embarcado"},
            "Cooperativa":{"d":"Presidente/Dir. Admin","p":"Politico, consenso conselho","a":"Piloto 1 unidade, ROI","o":"Sistema proprio"},
            "Pecuaria":{"d":"Dono/Dir. Ops","p":"Pragmatico, simplicidade","a":"Demo campo, SISBOV","o":"Planilha resolve"},
            "HF":{"d":"Dono/Gerente","p":"Operacional, rastreabilidade","a":"Demo rastreabilidade","o":"Caro demais"},
            "Florestal":{"d":"Dir. Florestal/CIO","p":"Tecnico, ciclo longo","a":"POC manutencao, GIS","o":"SAP implantado"},
        }
        p = perfis.get(tipo, {})
        if p:
            c1,c2 = st.columns(2)
            with c1:
                st.info(f"**🎯 DECISOR:** {p['d']}")
                st.info(f"**⚡ ABORDAGEM:** {p['a']}")
            with c2:
                st.warning(f"**👤 PERFIL:** {p['p']}")
                st.error(f"**🛡️ OBJEÇÃO:** {p['o']}")
