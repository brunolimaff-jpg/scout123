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


st.set_page_config(page_title="RAPTOR | Intelligence System", page_icon="🦅", layout="wide", initial_sidebar_state="expanded")

FRASES = [
    "Satelites reposicionados...", "Agentes infiltrados...", "Rastreando alvos financeiros...",
    "Deep Scan ativado...", "Mapeando cadeia de comando...", "Perfilando decisores...",
    "Interceptando tech stack...", "Varrendo grupo economico...", "Triangulando dados...",
    "Decodificando sinais de mercado...", "Compilando dossie tatico..."
]

# ═══════════════════════════════════════════════════════════════
# CSS — DARK OPS TACTICAL THEME
# ═══════════════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Orbitron:wght@400;700;900&display=swap');
.stApp{background-color:#0A0E14!important;color:#C5C8C6!important}
#MainMenu{visibility:hidden}footer{visibility:hidden}header{visibility:hidden}
div[data-testid="stToolbar"]{visibility:hidden}div[data-testid="stDecoration"]{display:none}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0D1117,#0A0E14,#111820)!important;border-right:1px solid #00FF4133!important}
section[data-testid="stSidebar"] .stMarkdown p,section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,section[data-testid="stSidebar"] .stMarkdown h3{color:#C5C8C6!important}
div[data-testid="stMetric"]{background:linear-gradient(135deg,#0D1117,#141B24)!important;border:1px solid #00FF4133!important;border-radius:8px!important;padding:16px!important}
div[data-testid="stMetric"] label{color:#00FF41!important;font-family:'JetBrains Mono',monospace!important;font-size:.75rem!important;text-transform:uppercase!important;letter-spacing:1px!important}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#FFF!important;font-family:'Orbitron',sans-serif!important;font-size:1.6rem!important;font-weight:700!important}
div[data-testid="stMetric"] [data-testid="stMetricDelta"]{color:#00FF41!important;font-family:'JetBrains Mono',monospace!important}
.stButton>button{background:linear-gradient(135deg,#00FF41,#00CC33)!important;color:#0A0E14!important;font-family:'JetBrains Mono',monospace!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:2px!important;border:none!important;border-radius:4px!important;transition:all .3s ease!important}
.stButton>button:hover{background:linear-gradient(135deg,#33FF66,#00FF41)!important;box-shadow:0 0 20px rgba(0,255,65,.4)!important}
.stDownloadButton>button{background:linear-gradient(135deg,#1a1f2e,#252b3b)!important;color:#00FF41!important;border:1px solid #00FF4155!important;font-family:'JetBrains Mono',monospace!important;font-weight:500!important;text-transform:uppercase!important;letter-spacing:1px!important;border-radius:4px!important}
.stDownloadButton>button:hover{border-color:#00FF41!important;box-shadow:0 0 15px rgba(0,255,65,.3)!important}
.stTextInput>div>div>input{background-color:#111820!important;color:#00FF41!important;border:1px solid #1E2A3A!important;border-radius:4px!important;font-family:'JetBrains Mono',monospace!important;caret-color:#00FF41!important}
.stTextInput>div>div>input:focus{border-color:#00FF41!important;box-shadow:0 0 10px rgba(0,255,65,.2)!important}
.stTextInput>label{color:#8B949E!important;font-family:'JetBrains Mono',monospace!important;text-transform:uppercase!important;font-size:.75rem!important;letter-spacing:1px!important}
.stSelectbox>div>div{background-color:#111820!important;border:1px solid #1E2A3A!important}
.stSelectbox>label{color:#8B949E!important;font-family:'JetBrains Mono',monospace!important}
.stTabs [data-baseweb="tab-list"]{background-color:#0D1117!important;border-bottom:2px solid #1E2A3A!important;gap:0!important}
.stTabs [data-baseweb="tab"]{color:#8B949E!important;font-family:'JetBrains Mono',monospace!important;text-transform:uppercase!important;font-size:.8rem!important;letter-spacing:1px!important;border-bottom:2px solid transparent!important;padding:10px 20px!important}
.stTabs [aria-selected="true"]{color:#00FF41!important;border-bottom:2px solid #00FF41!important}
.streamlit-expanderHeader{background-color:#111820!important;color:#00FF41!important;border:1px solid #1E2A3A!important;border-radius:4px!important;font-family:'JetBrains Mono',monospace!important}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#00FF41,#00CC33)!important}
.raptor-header{font-family:'Orbitron',sans-serif;font-weight:900;font-size:2.8rem;color:#00FF41;text-shadow:0 0 30px rgba(0,255,65,.5),0 0 60px rgba(0,255,65,.2);letter-spacing:6px;margin:0;line-height:1.2}
.raptor-subtitle{font-family:'JetBrains Mono',monospace;font-size:.85rem;color:#8B949E;letter-spacing:3px;text-transform:uppercase;margin-top:4px}
.raptor-version{font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#00FF4188;letter-spacing:2px}
.status-online{background:#0D1117;border:1px solid #00FF4144;border-radius:6px;padding:12px 16px;margin:8px 0}
.status-dot{display:inline-block;width:8px;height:8px;background:#00FF41;border-radius:50%;margin-right:8px;box-shadow:0 0 8px #00FF41;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 8px #00FF41}50%{opacity:.5;box-shadow:0 0 4px #00FF41}}
.step-card{background:#111820;border-left:3px solid #1E2A3A;padding:12px 16px;border-radius:0 6px 6px 0;margin-bottom:6px;font-family:'JetBrains Mono',monospace;font-size:.85rem;color:#C5C8C6}
.step-success{border-left-color:#00FF41}.step-warning{border-left-color:#FF8C00}.step-error{border-left-color:#FF4B4B}
.target-card{background:linear-gradient(135deg,#0D1117,#141B24);border:1px solid #00FF4122;border-radius:8px;padding:20px;margin:10px 0}
.intel-card{background:#111820;border:1px solid #1E2A3A;border-radius:6px;padding:16px;margin-bottom:10px}
.section-header{font-family:'Orbitron',sans-serif;color:#00FF41;font-size:1.1rem;letter-spacing:2px;text-transform:uppercase;border-bottom:1px solid #00FF4133;padding-bottom:8px;margin-bottom:16px}
.tier-badge{display:inline-block;padding:4px 14px;border-radius:3px;font-family:'Orbitron',sans-serif;font-weight:700;font-size:.85em;letter-spacing:2px}
.tier-diamante{background:#00FF4122;color:#00FF41;border:1px solid #00FF41}
.tier-ouro{background:#FFD70022;color:#FFD700;border:1px solid #FFD700}
.tier-prata{background:#C0C0C022;color:#C0C0C0;border:1px solid #C0C0C0}
.tier-bronze{background:#CD7F3222;color:#CD7F32;border:1px solid #CD7F32}
.neon-divider{height:1px;background:linear-gradient(90deg,transparent,#00FF4144,transparent);margin:20px 0;border:none}
.kill-metric{font-family:'Orbitron',sans-serif;font-size:1.8rem;color:#FFF;font-weight:700}
.mono-text{font-family:'JetBrains Mono',monospace;color:#8B949E;font-size:.85rem}
::-webkit-scrollbar{width:6px;height:6px}::-webkit-scrollbar-track{background:#0A0E14}::-webkit-scrollbar-thumb{background:#1E2A3A;border-radius:3px}::-webkit-scrollbar-thumb:hover{background:#00FF4144}
.js-plotly-plot .plotly .main-svg{background:transparent!important}
</style>""", unsafe_allow_html=True)

for k in ['dossie','logs','historico','step_results']:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ['logs','historico','step_results'] else None

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — COMMAND CENTER
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px 0;">
        <div style="font-size:2.5rem;margin-bottom:4px;">🦅</div>
        <div class="raptor-header" style="font-size:1.8rem;">RAPTOR</div>
        <div class="raptor-version">v1.0 | INTELLIGENCE SYSTEM</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="status-online">
        <span class="status-dot"></span>
        <span style="font-family:'JetBrains Mono',monospace;font-size:.75rem;color:#00FF41;letter-spacing:1px;">SISTEMA ONLINE</span>
        <span style="float:right;font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#8B949E;">OPERACIONAL</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#00FF41;">✅ API KEY: AUTENTICADO</div>', unsafe_allow_html=True)
    except (FileNotFoundError, KeyError):
        api_key = st.text_input("🔑 API KEY", type="password", placeholder="Insira a chave Gemini...")
        if not api_key:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#FF4B4B;">⛔ ACESSO NEGADO</div>', unsafe_allow_html=True)
            st.stop()

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.7rem;color:#8B949E;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">🎯 DESIGNAÇÃO DO ALVO</div>', unsafe_allow_html=True)
    target = st.text_input("Empresa / Grupo", placeholder="Ex: SLC Agricola, Amaggi...", label_visibility="visible")
    target_cnpj = st.text_input("CNPJ (opcional)", placeholder="XX.XXX.XXX/XXXX-XX")
    if target_cnpj:
        cl = limpar_cnpj(target_cnpj)
        if cl and validar_cnpj(cl):
            st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#00FF41;">✅ VALIDADO: {formatar_cnpj(cl)}</div>', unsafe_allow_html=True)
        elif cl:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#FF4B4B;">⛔ CNPJ INVALIDO</div>', unsafe_allow_html=True)

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    btn = st.button("⚡ INICIAR CAÇA", type="primary", disabled=not target, use_container_width=True)

    if st.session_state.historico:
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:.7rem;color:#8B949E;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">📋 ALVOS RECENTES</div>', unsafe_allow_html=True)
        for h in reversed(st.session_state.historico[-8:]):
            tc = "#00FF41" if h['score']>=751 else "#FFD700" if h['score']>=501 else "#C0C0C0" if h['score']>=251 else "#CD7F32"
            st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;padding:4px 0;border-bottom:1px solid #1E2A3A22;"><span style="color:{tc};">●</span> <span style="color:#C5C8C6;">{h["empresa"][:20]}</span><span style="color:{tc};float:right;">{h["score"]}</span></div>', unsafe_allow_html=True)

    st.markdown('<div style="position:fixed;bottom:10px;font-family:\'JetBrains Mono\',monospace;font-size:.6rem;color:#8B949E44;letter-spacing:1px;">RAPTOR © 2025 | CLASSIFIED</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════
tab_scout, tab_compare, tab_arsenal = st.tabs(["🎯 CAÇA", "⚖️ COMPARADOR", "⚔️ ARSENAL"])

TIER_MAP = {"DIAMANTE 💎":"diamante","OURO 🥇":"ouro","PRATA 🥈":"prata","BRONZE 🥉":"bronze"}

with tab_scout:
    if not target and not st.session_state.dossie:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 20px 0;">
            <div style="font-size:4rem;margin-bottom:10px;">🦅</div>
            <div class="raptor-header">RAPTOR</div>
            <div class="raptor-subtitle">SISTEMA AUTÔNOMO DE CAÇA A LEADS HIGH-TICKET (&gt;5.000 ha)</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # === INPUT PRINCIPAL NA TELA (nao depende da sidebar) ===
        st.markdown('<div class="section-header">🎯 DESIGNAÇÃO DO ALVO</div>', unsafe_allow_html=True)
        inp1, inp2, inp3 = st.columns([3, 2, 1])
        with inp1:
            target_main = st.text_input("Empresa / Grupo Econômico", placeholder="Ex: SLC Agrícola, Amaggi, Bom Futuro...", key="target_main")
        with inp2:
            cnpj_main = st.text_input("CNPJ (opcional)", placeholder="XX.XXX.XXX/XXXX-XX", key="cnpj_main")
            if cnpj_main:
                cl_main = limpar_cnpj(cnpj_main)
                if cl_main and validar_cnpj(cl_main):
                    st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#00FF41;">✅ {formatar_cnpj(cl_main)}</span>', unsafe_allow_html=True)
                elif cl_main:
                    st.markdown('<span style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#FF4B4B;">⛔ CNPJ INVÁLIDO</span>', unsafe_allow_html=True)
        with inp3:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_main = st.button("⚡ INICIAR CAÇA", type="primary", key="btn_main", use_container_width=True)

        # Sync: se usou input principal, sobrescreve sidebar
        if target_main:
            target = target_main
        if cnpj_main:
            target_cnpj = cnpj_main
        if btn_main and target_main:
            btn = True
            target = target_main
            if cnpj_main:
                target_cnpj = cnpj_main

        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        for col,icon,title,desc in [(c1,"🛰️","RECON","Hectares, culturas, verticalização"),(c2,"💰","FINANCEIRO","CRAs, Fiagros, M&A, governança"),(c3,"👔","DECISORES","C-Level, LinkedIn, perfil"),(c4,"💻","TECH STACK","ERP atual, vagas TI, maturidade")]:
            with col:
                st.markdown(f'<div class="target-card" style="text-align:center;min-height:160px;"><div style="font-size:2rem;margin-bottom:8px;">{icon}</div><div style="font-family:\'Orbitron\',sans-serif;color:#00FF41;font-size:.85rem;letter-spacing:2px;margin-bottom:8px;">{title}</div><div style="font-family:\'JetBrains Mono\',monospace;color:#8B949E;font-size:.75rem;">{desc}</div></div>', unsafe_allow_html=True)

    if btn and target:
        st.session_state.dossie = None; st.session_state.logs = []; st.session_state.step_results = []
        st.markdown(f'<div style="padding:10px 0;"><div style="font-family:\'Orbitron\',sans-serif;color:#00FF41;font-size:1.2rem;letter-spacing:3px;text-transform:uppercase;">🎯 ALVO ADQUIRIDO: {target.upper()}</div><div class="mono-text" style="margin-top:4px;">Iniciando varredura completa...</div></div>', unsafe_allow_html=True)
        progress_bar = st.progress(0.0); status = st.empty(); step_ctn = st.container()
        def on_progress(p, m):
            progress_bar.progress(min(p, 1.0))
            status.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.85rem;"><span style="color:#00FF41;">▶</span> <span style="color:#C5C8C6;">{m}</span> <span style="color:#8B949E;">— {random.choice(FRASES)}</span></div>', unsafe_allow_html=True)
        def on_step(s):
            st.session_state.step_results.append(s)
            ic = {"success":"✅","warning":"⚠️","error":"❌"}.get(s.status,"⏳")
            with step_ctn:
                cls = f"step-{s.status}"
                h = f'<div class="step-card {cls}"><b>{ic} {s.step_number}. {s.step_name}</b>'
                h += f' <span style="float:right;color:#8B949E;">{s.tempo_segundos:.1f}s</span><br>'
                h += f'<span style="color:#8B949E;">{s.resumo}</span>'
                if s.confianca > 0:
                    cc = "#00FF41" if s.confianca >= 0.7 else "#FF8C00" if s.confianca >= 0.4 else "#FF4B4B"
                    h += f' | <span style="color:{cc};">Conf: {s.confianca:.0%}</span>'
                if s.detalhes: h += '<br><small style="color:#555;">' + ' | '.join(s.detalhes[:4]) + '</small>'
                h += '</div>'; st.markdown(h, unsafe_allow_html=True)
        try:
            dossie = gerar_dossie_completo(target, api_key, target_cnpj, log_cb=lambda m: st.session_state.logs.append(m), progress_cb=on_progress, step_cb=on_step)
            st.session_state.dossie = dossie
            st.session_state.historico.append({'empresa': dossie.dados_operacionais.nome_grupo or target, 'score': dossie.sas_result.score, 'tier': dossie.sas_result.tier.value})
            st.rerun()
        except Exception as e:
            st.markdown(f'<div style="background:#FF4B4B11;border:1px solid #FF4B4B44;border-radius:6px;padding:16px;font-family:\'JetBrains Mono\',monospace;"><span style="color:#FF4B4B;font-weight:700;">⛔ FALHA NA OPERAÇÃO</span><br><span style="color:#C5C8C6;font-size:.85rem;">{e}</span></div>', unsafe_allow_html=True)
            import traceback; st.code(traceback.format_exc())

    # ═══════════════════════════════════════════════════════════
    # RESULTADO
    # ═══════════════════════════════════════════════════════════
    if st.session_state.dossie:
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        op = d.dados_operacionais; fi = d.dados_financeiros; cv = d.cadeia_valor; gr = d.grupo_economico

        # === RAPTOR CLASSIFICATION: HIGH TICKET vs DESCARTADO ===
        ha_total = op.hectares_total or 0
        if ha_total > 0 and ha_total < 5000:
            st.error(f"⛔ ALVO DESCARTADO (BAIXO POTENCIAL) — {ha_total:,} ha < 5.000 ha. Foco RAPTOR: operações High-Ticket.")
        elif ha_total >= 5000:
            st.success(f"✅ ALVO CONFIRMADO — HIGH TICKET | {ha_total:,} ha | Potencial: ALTO")

        # HEADER
        cs,ci,cq = st.columns([1,2,1])
        with cs:
            tier_cls = TIER_MAP.get(d.sas_result.tier.value, "bronze")
            st.markdown(f'<div class="target-card" style="text-align:center;"><div style="font-family:\'JetBrains Mono\',monospace;color:#8B949E;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;">SCORE SAS</div><div class="kill-metric">{d.sas_result.score}</div><div style="font-family:\'JetBrains Mono\',monospace;color:#8B949E;font-size:.75rem;">/1000</div><div class="tier-badge tier-{tier_cls}" style="margin-top:8px;">{d.sas_result.tier.value}</div></div>', unsafe_allow_html=True)
            if d.sas_result.recomendacao_comercial:
                st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.75rem;color:#00FF41;text-align:center;margin-top:8px;">🎯 {d.sas_result.recomendacao_comercial}</div>', unsafe_allow_html=True)
        with ci:
            st.markdown(f'<div style="padding:10px 0;"><div style="font-family:\'Orbitron\',sans-serif;color:#FFF;font-size:1.4rem;letter-spacing:2px;">{nome.upper()}</div></div>', unsafe_allow_html=True)
            badges = op.verticalizacao.listar_ativos()
            if badges:
                bh = " ".join([f'<span style="background:#00FF4111;color:#00FF41;padding:2px 8px;border-radius:3px;font-family:\'JetBrains Mono\',monospace;font-size:.7rem;margin-right:4px;border:1px solid #00FF4133;">{b}</span>' for b in badges[:10]])
                st.markdown(bh, unsafe_allow_html=True)
            st.markdown(f'<div class="mono-text" style="margin-top:8px;">⏱️ {d.tempo_total_segundos:.0f}s | 📅 {d.timestamp_geracao}</div>', unsafe_allow_html=True)
        with cq:
            if d.quality_report:
                lc = {"EXCELENTE":"🟢","BOM":"🔵","ACEITÁVEL":"🟡","INSUFICIENTE":"🔴"}
                qc = lc.get(d.quality_report.nivel.value, '')
                st.markdown(f'<div class="target-card" style="text-align:center;"><div style="font-family:\'JetBrains Mono\',monospace;color:#8B949E;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;">QUALITY GATE</div><div class="kill-metric" style="font-size:1.4rem;">{d.quality_report.score_qualidade:.0f}%</div><div style="font-family:\'JetBrains Mono\',monospace;color:#C5C8C6;font-size:.8rem;margin-top:4px;">{qc} {d.quality_report.nivel.value}</div></div>', unsafe_allow_html=True)
                if d.sas_result.confidence_score:
                    st.markdown(f'<div class="mono-text" style="text-align:center;">Confidence: {d.sas_result.confidence_score:.0f}%</div>', unsafe_allow_html=True)

        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # PERFIL
        st.markdown('<div class="section-header">🏢 PERFIL DO ALVO</div>', unsafe_allow_html=True)
        cp1, cp2 = st.columns([2, 1])
        with cp1:
            parts = [f"**{nome}**"]
            if fi.faturamento_estimado: parts.append(f"com faturamento estimado de **R${fi.faturamento_estimado/1e6:.0f}M**")
            elif fi.capital_social_estimado: parts.append(f"com capital de **R${fi.capital_social_estimado/1e6:.0f}M**")
            if op.hectares_total: parts.append(f"e **{op.hectares_total:,} hectares**")
            if op.culturas: parts.append(f"atuando em **{_sj(op.culturas)}**")
            if op.regioes_atuacao: parts.append(f"nas regioes **{_sj(op.regioes_atuacao)}**")
            st.markdown(" ".join(parts) + ".")
            if badges: st.markdown(f"**Infraestrutura:** {', '.join(badges)}")
            if fi.funcionarios_estimados: st.markdown(f"**Funcionarios:** ~{fi.funcionarios_estimados:,}")
            if op.numero_fazendas: st.markdown(f"**Fazendas/Unidades:** {op.numero_fazendas}")
            if cv.posicao_cadeia: st.markdown(f"**Posicao na cadeia:** {cv.posicao_cadeia} | **Integracao:** {cv.integracao_vertical_nivel}")
            if cv.exporta and cv.mercados_exportacao: st.markdown(f"**Exportacao:** {_sj(cv.mercados_exportacao, 5)}")
            if cv.certificacoes: st.markdown(f"**Certificacoes:** {_sj(cv.certificacoes)}")
            if fi.resumo_financeiro: st.info(fi.resumo_financeiro)
        with cp2:
            if d.dados_cnpj:
                dc = d.dados_cnpj
                for label, val in [("CNPJ",formatar_cnpj(dc.cnpj)),("CNAE",dc.cnae_principal),("CAPITAL",f"R${dc.capital_social:,.0f}"),("NAT.JUR.",dc.natureza_juridica or "N/I"),("LOCAL",f"{dc.municipio}/{dc.uf}"),("QSA",f"{len(dc.qsa)} socios")]:
                    st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.8rem;padding:3px 0;border-bottom:1px solid #1E2A3A22;"><span style="color:#8B949E;">{label}:</span> <span style="color:#C5C8C6;">{val}</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # FINANCEIRO
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
                if fi.auditorias:
                    st.markdown("**Auditorias:**")
                    for a in fi.auditorias: st.markdown(f"✅ {_fmt_movimento(a)}")
                if fi.parceiros_financeiros:
                    st.markdown("**Parceiros:**")
                    for p in fi.parceiros_financeiros: st.markdown(f"🤝 {_fmt_movimento(p)}")
            st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # RAIO-X
        st.markdown('<div class="section-header">📊 RAIO-X DA OPERAÇÃO</div>', unsafe_allow_html=True)
        mc = st.columns(6)
        mc[0].metric("ÁREA", f"{op.hectares_total:,} ha" if op.hectares_total else "N/D")
        mc[1].metric("EFETIVO", f"{fi.funcionarios_estimados:,}" if fi.funcionarios_estimados else "N/D")
        mc[2].metric("CAPITAL", f"R${fi.capital_social_estimado/1e6:.1f}M" if fi.capital_social_estimado else "N/D")
        mc[3].metric("CULTURAS", _sj(op.culturas, 3) if op.culturas else "N/D")
        mc[4].metric("FAZENDAS", str(op.numero_fazendas) if op.numero_fazendas else "N/D")
        mc[5].metric("GRUPO", f"{gr.total_empresas} emp" if gr.total_empresas else "N/D")
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # DECISORES
        decs = d.decisores.get('decisores', []) if d.decisores else []
        if decs:
            st.markdown('<div class="section-header">👔 DECISORES-CHAVE</div>', unsafe_allow_html=True)
            for dec in decs:
                rel = dec.get('relevancia_erp','')
                ic = "🔴" if rel == 'alta' else "🟡" if rel == 'media' else "⚪"
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**{ic} {dec.get('nome','')}** — {dec.get('cargo','')}")
                    det = []
                    if dec.get('formacao') and dec['formacao'] not in ['Nao encontrado','N/I','']: det.append(f"🎓 {dec['formacao']}")
                    if dec.get('experiencia_anterior') and dec['experiencia_anterior'] not in ['Nao encontrado','N/I','']: det.append(f"📋 {dec['experiencia_anterior']}")
                    if dec.get('tempo_cargo') and dec['tempo_cargo'] not in ['Nao encontrado','N/I','']: det.append(f"⏱️ {dec['tempo_cargo']}")
                    if det: st.caption(" | ".join(det))
                with col2:
                    lnk = dec.get('linkedin','')
                    if lnk and lnk not in ['Nao encontrado','N/I','']: st.markdown(f"[🔗 LinkedIn]({lnk})")
                    st.caption(f"Relevancia: **{rel}**")
            est = d.decisores.get('estrutura_decisao',''); mat = d.decisores.get('nivel_maturidade_gestao','')
            if est or mat: st.caption(f"Estrutura: {est} | Maturidade: {mat}")
            st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # TECH STACK
        ts = d.tech_stack if d.tech_stack else {}
        if ts:
            st.markdown('<div class="section-header">💻 TECH STACK DETECTADO</div>', unsafe_allow_html=True)
            erp = ts.get('erp_principal', {})
            ct1, ct2 = st.columns(2)
            with ct1:
                if erp.get('sistema') and erp['sistema'] not in ['N/I','']:
                    st.markdown(f"**ERP Principal:** 🖥️ **{erp['sistema']}** {erp.get('versao','')}")
                    st.caption(f"Fonte: {erp.get('fonte_evidencia','')} | Conf: {erp.get('confianca',0):.0%}")
                else: st.markdown("**ERP Principal:** Nao identificado")
                if ts.get('nivel_maturidade_ti'): st.markdown(f"**Maturidade TI:** {ts['nivel_maturidade_ti']}")
                if ts.get('investimento_ti_percebido'): st.markdown(f"**Investimento TI:** {ts['investimento_ti_percebido']}")
            with ct2:
                outros = ts.get('outros_sistemas', [])
                if outros:
                    st.markdown("**Outros sistemas:**")
                    for o in outros:
                        if isinstance(o, dict): st.markdown(f"- {o.get('tipo','')}: **{o.get('sistema','')}**")
                        else: st.markdown(f"- {o}")
                vagas = ts.get('vagas_ti_abertas', [])
                if vagas:
                    st.markdown("**Vagas TI:**")
                    for v in vagas:
                        if isinstance(v, dict): st.markdown(f"- 📋 {v.get('titulo','')} ({_sj(v.get('sistemas_mencionados',[]))})")
                        else: st.markdown(f"- {v}")
            dores_t = ts.get('dores_tech_identificadas', [])
            if dores_t:
                st.markdown("**Dores tech:**")
                for x in dores_t: st.markdown(f"- ⚠️ {x}")
            st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # GRUPO ECONOMICO
        if gr.total_empresas > 0:
            with st.expander(f"🏛️ GRUPO ECONÔMICO ({gr.total_empresas} empresas)", expanded=False):
                if gr.cnpj_matriz: st.markdown(f"**CNPJ Matriz:** {gr.cnpj_matriz}")
                if hasattr(gr, 'holding_controladora') and gr.holding_controladora: st.markdown(f"**Holding:** {gr.holding_controladora}")
                if gr.controladores: st.markdown(f"**Controladores:** {_sj(gr.controladores)}")
                filiais = gr.cnpjs_filiais
                if filiais:
                    st.markdown(f"#### Filiais ({len(filiais)})")
                    if isinstance(filiais[0], dict): st.dataframe(pd.DataFrame(filiais), hide_index=True, use_container_width=True)
                    else:
                        for f_item in filiais: st.markdown(f"- {f_item}")
                colig = gr.cnpjs_coligadas
                if colig:
                    st.markdown(f"#### Coligadas ({len(colig)})")
                    if isinstance(colig[0], dict): st.dataframe(pd.DataFrame(colig), hide_index=True, use_container_width=True)
                    else:
                        for c_item in colig: st.markdown(f"- {c_item}")

        # SPIDER CHART
        st.markdown('<div class="section-header">📊 SCORE BREAKDOWN</div>', unsafe_allow_html=True)
        cch, ctb = st.columns([2, 1])
        with cch:
            b = d.sas_result.breakdown
            cats = ["MÚSCULO\n(Porte)","COMPLEXIDADE","GENTE\n(Gestão)","MOMENTO\n(Gov/Tech)"]
            vals = [b.musculo, b.complexidade, b.gente, b.momento]; maxs = [400,250,200,150]
            pcts = [v/m*100 for v,m in zip(vals, maxs)]
            fig = go.Figure(go.Scatterpolar(r=pcts+[pcts[0]], theta=cats+[cats[0]], fill='toself',
                line_color='#00FF41', fillcolor='rgba(0,255,65,0.15)', marker=dict(color='#00FF41', size=6)))
            fig.update_layout(polar=dict(bgcolor='#0A0E14',
                radialaxis=dict(visible=True, range=[0,100], ticksuffix="%", gridcolor='#1E2A3A', linecolor='#1E2A3A', tickfont=dict(color='#8B949E', family='JetBrains Mono')),
                angularaxis=dict(gridcolor='#1E2A3A', linecolor='#1E2A3A', tickfont=dict(color='#00FF41', family='JetBrains Mono', size=10))),
                showlegend=False, height=380, margin=dict(l=60,r=60,t=30,b=30),
                paper_bgcolor='#0A0E14', plot_bgcolor='#0A0E14', font=dict(family='JetBrains Mono', color='#C5C8C6'))
            st.plotly_chart(fig, use_container_width=True)
        with ctb:
            df = pd.DataFrame([{"Pilar":"MÚSCULO","Pts":b.musculo,"Max":400,"Pct":f"{b.musculo/4:.0f}%"},{"Pilar":"COMPLEX.","Pts":b.complexidade,"Max":250,"Pct":f"{b.complexidade/2.5:.0f}%"},{"Pilar":"GENTE","Pts":b.gente,"Max":200,"Pct":f"{b.gente/2:.0f}%"},{"Pilar":"MOMENTO","Pts":b.momento,"Max":150,"Pct":f"{b.momento/1.5:.0f}%"}])
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.markdown(f'<div style="text-align:center;margin-top:12px;"><div class="kill-metric" style="font-size:1.4rem;">{d.sas_result.score}/1000</div><div class="tier-badge tier-{TIER_MAP.get(d.sas_result.tier.value,"bronze")}" style="margin-top:8px;">{d.sas_result.tier.value}</div></div>', unsafe_allow_html=True)
            if d.sas_result.vertical_detectada: st.caption(f"Vertical: {d.sas_result.vertical_detectada} | Conf: {d.sas_result.confidence_score:.0f}%")
        if d.sas_result.justificativas:
            with st.expander("🔍 JUSTIFICATIVAS DO SCORE"):
                for j in d.sas_result.justificativas:
                    st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.8rem;color:#8B949E;padding:2px 0;">→ {j}</div>', unsafe_allow_html=True)
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # INTEL
        il = d.intel_mercado
        if il.sinais_compra or il.dores_identificadas:
            st.markdown('<div class="section-header">📡 INTELIGÊNCIA DE MERCADO</div>', unsafe_allow_html=True)
            ti1,ti2,ti3 = st.tabs(["🎯 SINAIS","📰 NOTÍCIAS","⚠️ RISCOS"])
            with ti1:
                for s in il.sinais_compra: st.markdown(f"🟢 {s}")
                if il.dores_identificadas:
                    st.markdown("**Dores:**")
                    for x in il.dores_identificadas: st.markdown(f"🔴 {x}")
            with ti2:
                for n in il.noticias_recentes:
                    st.markdown(_fmt_noticia(n)); st.markdown("---")
            with ti3:
                cr1,co1 = st.columns(2)
                with cr1:
                    st.markdown("**Riscos:**")
                    for r in il.riscos: st.markdown(f"⚠️ {r}")
                with co1:
                    st.markdown("**Oportunidades:**")
                    for o in il.oportunidades: st.markdown(f"💡 {o}")
            st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # NOTICIAS
        noticias = il.noticias_recentes if il.noticias_recentes else []
        if noticias and any(isinstance(n, dict) for n in noticias):
            st.markdown('<div class="section-header">📰 NOTÍCIAS RELEVANTES</div>', unsafe_allow_html=True)
            for n in noticias:
                if isinstance(n, dict):
                    titulo = n.get('titulo',''); resumo = n.get('resumo','')
                    data = n.get('data_aprox', n.get('data','')); fonte = n.get('fonte',''); rel = n.get('relevancia','')
                    date_html = f'<div style="font-family:JetBrains Mono,monospace;color:#8B949E;font-size:.75rem;margin-top:4px;">{data}</div>' if data else ""
                    resumo_html = f'<div style="color:#C5C8C6;font-size:.85rem;margin-top:8px;">{resumo}</div>' if resumo else ""
                    st.markdown(f'<div class="intel-card"><div style="font-family:JetBrains Mono,monospace;color:#FFF;font-size:.9rem;font-weight:500;">{titulo}</div>{date_html}{resumo_html}</div>', unsafe_allow_html=True)

        # ANALISE
        st.markdown('<div class="section-header">🧠 INTELIGÊNCIA ESTRATÉGICA</div>', unsafe_allow_html=True)
        for sec in d.secoes_analise:
            with st.expander(f"{sec.icone} {sec.titulo}", expanded=True):
                st.markdown(sec.conteudo)
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)

        # QUALITY
        if d.quality_report:
            with st.expander("✅ QUALITY GATE"):
                for ch in d.quality_report.checks:
                    ic = "✅" if ch.passou else "❌"
                    st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.85rem;padding:4px 0;border-bottom:1px solid #1E2A3A22;">{ic} <span style="color:#C5C8C6;">{ch.criterio}</span><span style="color:#8B949E;float:right;">{ch.nota}</span></div>', unsafe_allow_html=True)
                if d.quality_report.audit_ia:
                    ai = d.quality_report.audit_ia
                    st.markdown(f'<div style="margin-top:12px;font-family:\'JetBrains Mono\',monospace;"><span style="color:#00FF41;">Nota IA:</span> <span style="color:#FFF;font-weight:700;">{ai.get("nota_final","N/A")}/10</span> — <span style="color:#8B949E;">{ai.get("nivel","")}</span></div>', unsafe_allow_html=True)

        # EXPORT — PDF + CSV + MD + JSON
        st.markdown('<div class="section-header">📤 EXPORTAR DOSSIE</div>', unsafe_allow_html=True)
        md = f"# RAPTOR Intelligence Report: {nome}\n**Score:** {d.sas_result.score}/1000 — {d.sas_result.tier.value}\n\n"
        for sec in d.secoes_analise: md += f"## {sec.icone} {sec.titulo}\n\n{sec.conteudo}\n\n---\n\n"
        csv_data = gerar_csv_report(d)
        jd = json.dumps({"empresa":nome,"score":d.sas_result.score,"tier":d.sas_result.tier.value,"recomendacao":d.sas_result.recomendacao_comercial,"decisores":d.decisores,"tech_stack":d.tech_stack}, indent=2, ensure_ascii=False, default=str)
        ex1,ex2,ex3,ex4 = st.columns(4)
        with ex1:
            try:
                pp = gerar_pdf(d); pf = open(pp, "rb")
                st.download_button("📕 PDF", pf.read(), f"raptor_intelligence_report_{nome.replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
            except Exception as pdf_err:
                st.error(f"PDF: {pdf_err}")
                st.caption("Instale: pip install fpdf2")
        with ex2:
            st.download_button("📊 CSV", csv_data, f"raptor_intelligence_report_{nome.replace(' ','_')}.csv", "text/csv", use_container_width=True)
        with ex3:
            st.download_button("📝 MD", md, f"raptor_{nome.replace(' ','_')}.md", "text/markdown", use_container_width=True)
        with ex4:
            st.download_button("🔧 JSON", jd, f"raptor_{nome.replace(' ','_')}.json", use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# COMPARADOR
# ═══════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown('<div class="section-header">⚖️ COMPARADOR DE ALVOS</div>', unsafe_allow_html=True)
    if len(st.session_state.historico) < 2:
        st.markdown('<div class="target-card" style="text-align:center;padding:40px;"><div style="font-size:2rem;margin-bottom:10px;">⚖️</div><div style="font-family:\'JetBrains Mono\',monospace;color:#8B949E;">Investigue 2+ alvos para habilitar comparacao tatica.</div></div>', unsafe_allow_html=True)
    else:
        hist = st.session_state.historico[-5:]
        st.dataframe(pd.DataFrame(hist), hide_index=True, use_container_width=True)
        fig = go.Figure(go.Bar(x=[h['empresa'] for h in hist], y=[h['score'] for h in hist],
            marker_color=['#00FF41' if h['score']>=751 else '#FFD700' if h['score']>=501 else '#C0C0C0' if h['score']>=251 else '#CD7F32' for h in hist],
            text=[h['tier'] for h in hist], textposition='auto', textfont=dict(family='JetBrains Mono', color='#0A0E14')))
        fig.update_layout(title=dict(text="SCORE SAS POR ALVO", font=dict(family='Orbitron', color='#00FF41', size=14)),
            yaxis_title="Score", height=400, paper_bgcolor='#0A0E14', plot_bgcolor='#0D1117',
            font=dict(family='JetBrains Mono', color='#8B949E'),
            yaxis=dict(gridcolor='#1E2A3A'), xaxis=dict(gridcolor='#1E2A3A'))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# ARSENAL
# ═══════════════════════════════════════════════════════════════
with tab_arsenal:
    st.markdown('<div class="section-header">⚔️ ARSENAL TÁTICO</div>', unsafe_allow_html=True)
    tab_conc, tab_prof = st.tabs(["🗡️ MATADOR CONCORRÊNCIA", "🧠 PROFILER"])
    with tab_conc:
        conc = st.selectbox("CONCORRENTE:", list(ARGUMENTOS_CONCORRENCIA.keys()), format_func=lambda x: ARGUMENTOS_CONCORRENCIA[x]['nome'])
        if conc:
            info = ARGUMENTOS_CONCORRENCIA[conc]
            c1,c2 = st.columns(2)
            with c1:
                st.markdown('<div class="section-header" style="font-size:.9rem;">❌ FRAQUEZAS DO INIMIGO</div>', unsafe_allow_html=True)
                for f_item in info['fraquezas']:
                    st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.85rem;color:#FF4B4B;padding:4px 0;">🔴 {f_item}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="section-header" style="font-size:.9rem;">✅ VANTAGEM SENIOR</div>', unsafe_allow_html=True)
                for v_item in info['senior_vantagem']:
                    st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.85rem;color:#00FF41;padding:4px 0;">🟢 {v_item}</div>', unsafe_allow_html=True)
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
            for label, val in [("🎯 DECISOR",p['d']),("👤 PERFIL",p['p']),("⚡ ABORDAGEM",p['a']),("🛡️ OBJEÇÕES",p['o'])]:
                st.markdown(f'<div class="intel-card"><div style="font-family:\'Orbitron\',sans-serif;color:#00FF41;font-size:.75rem;letter-spacing:2px;margin-bottom:4px;">{label}</div><div style="font-family:\'JetBrains Mono\',monospace;color:#C5C8C6;font-size:.9rem;">{val}</div></div>', unsafe_allow_html=True)
