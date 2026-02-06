import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(**file**)))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time, random, json
from services.dossier_orchestrator import gerar_dossie_completo
from services.market_estimator import calcular_sas
from services.cnpj_service import consultar_cnpj, formatar_cnpj, validar_cnpj, limpar_cnpj
from services.cache_service import cache
from services.request_queue import request_queue
from utils.market_intelligence import ARGUMENTOS_CONCORRENCIA, get_contexto_cnae, get_contexto_regional
from utils.pdf_export import gerar_pdf
from scout_types import DossieCompleto, Tier, QualityLevel

st.set_page_config(page_title=Senior Scout 360 v3.1, page_icon=“🕵️”, layout=“wide”, initial_sidebar_state=“expanded”)

FRASES = [
“🛰️ Ativando satélites de reconhecimento…”, “📡 Conectando 7 agentes Pro…”,
“💰 Rastreando CRAs e Fiagros…”, “🧠 Gemini 2.5 Pro pensando profundamente…”,
“🔗 Mapeando cadeia de valor…”, “🏛️ Investigando grupo econômico…”,
“📊 Cruzando dados financeiros…”, “🚜 Varrendo operações de campo…”,
]

# === CSS ===

st.markdown(”””<style>
div[data-testid=“stMetric”] { background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 16px; border-radius: 12px; }
div[data-testid=“stMetric”] label { color: rgba(255,255,255,0.8) !important; }
div[data-testid=“stMetric”] [data-testid=“stMetricValue”] { color: white !important; font-size: 1.8rem !important; }
div[data-testid=“stMetric”] [data-testid=“stMetricDelta”] { color: rgba(255,255,255,0.9) !important; }
.step-card { background: #f8f9fa; border-left: 4px solid #2d5a87; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 8px; }
.step-success { border-left-color: #28a745; }
.step-warning { border-left-color: #ffc107; }
.step-error { border-left-color: #dc3545; }
.conf-high { color: #28a745; font-weight: bold; }
.conf-med { color: #ffc107; font-weight: bold; }
.conf-low { color: #dc3545; font-weight: bold; }
</style>”””, unsafe_allow_html=True)

# === SESSION STATE ===

for k in [‘dossie’, ‘logs’, ‘historico’, ‘step_results’]:
if k not in st.session_state:
st.session_state[k] = [] if k in [‘logs’, ‘historico’, ‘step_results’] else None

# === SIDEBAR ===

with st.sidebar:
st.title(“🕵️ Senior Scout 360”)
st.caption(“v3.1 | All Pro | 8 Agents | Full Agro”)
st.markdown(”—”)
try:
api_key = st.secrets[“GEMINI_API_KEY”]
st.success(“✅ API Key OK”)
except (FileNotFoundError, KeyError):
api_key = st.text_input(“Gemini API Key:”, type=“password”)
if not api_key: st.error(“Insira a API Key”); st.stop()
st.markdown(”—”)
target = st.text_input(“🎯 Empresa / Grupo”, placeholder=“Ex: SLC Agrícola, Bom Futuro…”)
target_cnpj = st.text_input(“CNPJ (opcional)”, placeholder=“XX.XXX.XXX/XXXX-XX”)
if target_cnpj:
cl = limpar_cnpj(target_cnpj)
if cl and validar_cnpj(cl): st.caption(f”✅ {formatar_cnpj(cl)}”)
elif cl: st.caption(“❌ Inválido”)
st.markdown(”—”)
btn = st.button(“🚀 Investigação Completa”, type=“primary”, disabled=not target, use_container_width=True)
st.markdown(”—”)
st.info(”**Pipeline v3.1 (8 Passos)**\n\n”
“1. 📋 CNPJ (BrasilAPI)\n2. 🛰️ Recon Operacional\n3. 💰 Sniper Financeiro\n”
“4. 🔗 Cadeia de Valor\n5. 🏛️ Grupo Econômico\n6. 📡 Intel Mercado\n”
“7. 🧠 Análise Estratégica\n8. ✅ Quality Gate\n\n*Todos no Gemini 2.5 Pro*”)
if st.session_state.historico:
st.markdown(”—”)
st.subheader(“📚 Histórico”)
for h in reversed(st.session_state.historico[-8:]):
st.caption(f”• {h[‘empresa’]} — {h[‘tier’]} ({h[‘score’]})”)

# === TABS PRINCIPAIS ===

tab_scout, tab_compare, tab_arsenal = st.tabs([“🕵️ Scout”, “⚖️ Comparador”, “⚔️ Arsenal”])

with tab_scout:
if not target and st.session_state.dossie is None:
st.header(“🕵️ Senior Scout 360”)
st.markdown(”**7 agentes de IA especializados** no Gemini 2.5 Pro investigam empresas do agronegócio.”)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(”#### 🛰️ Recon\nHectares, culturas, verticalizações”)
with c2: st.markdown(”#### 💰 Finanças\nCRAs, Fiagros, governança”)
with c3: st.markdown(”#### 🔗 Cadeia\nFornecedores, clientes, export”)
with c4: st.markdown(”#### 🧠 Análise\nDossiê estratégico Deep Thinking”)

```
elif btn and target:
    st.session_state.dossie = None
    st.session_state.logs = []
    st.session_state.step_results = []
    st.header(f"🔍 Investigando: {target}")
    progress_bar = st.progress(0.0)
    status = st.empty()
    step_container = st.container()

    def on_progress(p, m):
        progress_bar.progress(min(p, 1.0))
        status.markdown(f"**{m}** — _{random.choice(FRASES)}_")

    def on_step(s):
        st.session_state.step_results.append(s)
        ic = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(s.status, "⏳")
        conf_cls = "conf-high" if s.confianca >= 0.7 else "conf-med" if s.confianca >= 0.4 else "conf-low"
        with step_container:
            cls = f"step-{s.status}"
            html = f'<div class="step-card {cls}"><b>{ic} Passo {s.step_number}: {s.step_name}</b>'
            html += f' <span style="float:right">{s.tempo_segundos:.1f}s</span><br>'
            html += f'<span style="color:#555">{s.resumo}</span>'
            if s.confianca > 0:
                html += f' | <span class="{conf_cls}">Confiança: {s.confianca:.0%}</span>'
            if s.detalhes:
                html += '<br><small style="color:#777">' + ' | '.join(s.detalhes[:4]) + '</small>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    try:
        dossie = gerar_dossie_completo(target, api_key, target_cnpj,
                                        log_cb=lambda m: st.session_state.logs.append(m),
                                        progress_cb=on_progress, step_cb=on_step)
        st.session_state.dossie = dossie
        st.session_state.historico.append({
            'empresa': dossie.dados_operacionais.nome_grupo or target,
            'score': dossie.sas_result.score, 'tier': dossie.sas_result.tier.value})
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        with st.expander("Log"): [st.text(l) for l in st.session_state.logs]

# === EXIBIÇÃO DO DOSSIÊ ===
if st.session_state.dossie:
    d: DossieCompleto = st.session_state.dossie
    nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
    op = d.dados_operacionais
    fi = d.dados_financeiros
    cv = d.cadeia_valor
    gr = d.grupo_economico

    # Header
    cs, ci, cq = st.columns([1, 2, 1])
    with cs:
        st.metric("SAS 4.0", f"{d.sas_result.score}/1000", d.sas_result.tier.value)
    with ci:
        st.subheader(f"📋 {nome}")
        badges = op.verticalizacao.listar_ativos()
        if badges: st.markdown(" ".join([f"`{b}`" for b in badges[:10]]))
        st.caption(f"⏱️ {d.tempo_total_segundos:.0f}s | 📅 {d.timestamp_geracao} | 🤖 {d.modelo_usado}")
    with cq:
        if d.quality_report:
            lc = {"EXCELENTE": "🟢", "BOM": "🔵", "ACEITÁVEL": "🟡", "INSUFICIENTE": "🔴"}
            st.metric("Quality Gate", f"{d.quality_report.score_qualidade:.0f}%",
                      f"{lc.get(d.quality_report.nivel.value, '')} {d.quality_report.nivel.value}")
    st.markdown("---")

    # Pipeline Steps Visual
    if d.pipeline_steps:
        with st.expander("📊 Resultado por Agente (clique para expandir)", expanded=False):
            for s in d.pipeline_steps:
                ic = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(s.status, "⏳")
                conf_c = "🟢" if s.confianca >= 0.7 else "🟡" if s.confianca >= 0.4 else "🔴" if s.confianca > 0 else ""
                st.markdown(f"**{ic} {s.step_name}** ({s.tempo_segundos:.1f}s) {conf_c}")
                st.markdown(f"  _{s.resumo}_")
                if s.detalhes:
                    for det in s.detalhes: st.markdown(f"  - {det}")
                st.markdown("---")

    # Financeiros
    if fi.movimentos_financeiros or fi.fiagros_relacionados:
        st.markdown("### 💰 Movimentos Financeiros & Governança")
        cm, cf2 = st.columns(2)
        with cm:
            for m in fi.movimentos_financeiros: st.markdown(f"- 🏦 **{m}**")
        with cf2:
            if fi.fiagros_relacionados:
                st.markdown("**Fiagros:**"); [st.markdown(f"- 📈 {f}") for f in fi.fiagros_relacionados]
            if fi.cras_emitidos:
                st.markdown("**CRAs:**"); [st.markdown(f"- 📜 {c}") for c in fi.cras_emitidos]
            if fi.auditorias:
                st.markdown("**Auditorias:**"); [st.markdown(f"- ✅ {a}") for a in fi.auditorias]
        st.markdown("---")

    # Raio-X
    st.markdown("### 📊 Raio-X da Operação")
    mc = st.columns(6)
    mc[0].metric("Área", f"{op.hectares_total:,} ha" if op.hectares_total else "N/D")
    mc[1].metric("Funcionários", f"{fi.funcionarios_estimados:,}" if fi.funcionarios_estimados else "N/D")
    mc[2].metric("Capital", f"R${fi.capital_social_estimado/1e6:.1f}M" if fi.capital_social_estimado else "N/D")
    mc[3].metric("Culturas", ", ".join(op.culturas[:3]) if op.culturas else "N/D")
    mc[4].metric("Fazendas", str(op.numero_fazendas) if op.numero_fazendas else "N/D")
    mc[5].metric("Grupo", f"{gr.total_empresas} empresas" if gr.total_empresas else "N/D")
    if op.cabecas_gado or op.cabecas_aves:
        mc2 = st.columns(4)
        if op.cabecas_gado: mc2[0].metric("Gado", f"{op.cabecas_gado:,} cab")
        if op.cabecas_aves: mc2[1].metric("Aves", f"{op.cabecas_aves:,} cab")
        if op.cabecas_suinos: mc2[2].metric("Suínos", f"{op.cabecas_suinos:,} cab")
        if op.area_irrigada_ha: mc2[3].metric("Irrigada", f"{op.area_irrigada_ha:,} ha")
    st.markdown("---")

    # Cadeia de Valor
    if cv.posicao_cadeia:
        st.markdown("### 🔗 Cadeia de Valor")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.markdown(f"**Posição:** {cv.posicao_cadeia}")
            st.markdown(f"**Integração:** {cv.integracao_vertical_nivel}")
            st.markdown(f"**Exporta:** {'Sim → ' + ', '.join(cv.mercados_exportacao[:3]) if cv.exporta else 'Não'}")
        with cc2:
            st.markdown("**Clientes:**"); [st.markdown(f"- {c}") for c in cv.clientes_principais[:5]]
        with cc3:
            st.markdown("**Certificações:**"); [st.markdown(f"- 🏅 {c}") for c in cv.certificacoes]
            if cv.fornecedores_principais:
                st.markdown("**Fornecedores:**"); [st.markdown(f"- {f}") for f in cv.fornecedores_principais[:3]]
        st.markdown("---")

    # Spider Chart
    st.markdown("### 📊 Score Breakdown")
    cch, ctb = st.columns([2, 1])
    with cch:
        b = d.sas_result.breakdown
        cats = ["Músculo\n(Porte)", "Complexidade", "Gente\n(Gestão)", "Momento\n(Gov/Tech)"]
        vals = [b.musculo, b.complexidade, b.gente, b.momento]
        maxs = [400, 250, 200, 150]
        pcts = [v/m*100 for v, m in zip(vals, maxs)]
        fig = go.Figure(go.Scatterpolar(r=pcts+[pcts[0]], theta=cats+[cats[0]], fill='toself',
                                         line_color='#1e3a5f', fillcolor='rgba(30,58,95,0.3)'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")),
                          showlegend=False, height=350, margin=dict(l=60, r=60, t=30, b=30))
        st.plotly_chart(fig, use_container_width=True)
    with ctb:
        df = pd.DataFrame([{"Pilar": "Músculo", "Pts": b.musculo, "Max": 400},
                           {"Pilar": "Complexidade", "Pts": b.complexidade, "Max": 250},
                           {"Pilar": "Gente", "Pts": b.gente, "Max": 200},
                           {"Pilar": "Momento", "Pts": b.momento, "Max": 150}])
        st.dataframe(df, hide_index=True, width="stretch")
        st.markdown(f"**Total: {d.sas_result.score}/1000** — {d.sas_result.tier.value}")
    if d.sas_result.justificativas:
        with st.expander("🔍 Justificativas"):
            for j in d.sas_result.justificativas: st.text(f"→ {j}")
    st.markdown("---")

    # Intel
    il = d.intel_mercado
    if il.noticias_recentes or il.sinais_compra:
        st.markdown("### 📡 Inteligência de Mercado")
        ti1, ti2, ti3 = st.tabs(["🎯 Sinais", "📰 Notícias", "⚠️ Riscos"])
        with ti1:
            for s in il.sinais_compra: st.markdown(f"- 🟢 {s}")
            if il.dores_identificadas:
                st.markdown("**Dores:**"); [st.markdown(f"- 🔴 {x}") for x in il.dores_identificadas]
        with ti2:
            for n in il.noticias_recentes:
                if isinstance(n, dict):
                    st.markdown(f"**{n.get('titulo','')}** ({n.get('data_aprox','')})"); st.caption(n.get('resumo',''))
                else: st.markdown(f"- {n}")
        with ti3:
            cr1, co1 = st.columns(2)
            with cr1: st.markdown("**Riscos:**"); [st.markdown(f"- {r}") for r in il.riscos]
            with co1: st.markdown("**Oportunidades:**"); [st.markdown(f"- {o}") for o in il.oportunidades]
        st.markdown("---")

    # Análise
    st.markdown("### 🧠 Inteligência Estratégica")
    for sec in d.secoes_analise:
        with st.expander(f"{sec.icone} {sec.titulo}", expanded=True):
            st.markdown(sec.conteudo)
    st.markdown("---")

    # CNPJ
    if d.dados_cnpj:
        with st.expander("📋 Dados Cadastrais"):
            dc = d.dados_cnpj
            ca, cb = st.columns(2)
            with ca:
                st.markdown(f"**Razão:** {dc.razao_social}"); st.markdown(f"**Fantasia:** {dc.nome_fantasia}")
                st.markdown(f"**CNPJ:** {formatar_cnpj(dc.cnpj)}"); st.markdown(f"**Situação:** {dc.situacao_cadastral}")
            with cb:
                st.markdown(f"**Nat. Jurídica:** {dc.natureza_juridica}"); st.markdown(f"**Capital:** R${dc.capital_social:,.2f}")
                st.markdown(f"**CNAE:** {dc.cnae_principal} — {dc.cnae_descricao}")
                st.markdown(f"**Local:** {dc.municipio}/{dc.uf}")
            if dc.qsa:
                st.markdown("**QSA:**"); st.dataframe(pd.DataFrame(dc.qsa), hide_index=True, width="stretch")

    # Grupo Econômico
    if gr.total_empresas > 0:
        with st.expander("🏛️ Grupo Econômico"):
            st.markdown(f"**Matriz:** {gr.cnpj_matriz}"); st.markdown(f"**Total:** {gr.total_empresas} empresas")
            st.markdown(f"**Controladores:** {', '.join(gr.controladores)}")
            if gr.cnpjs_coligadas:
                st.markdown("**Coligadas:**"); [st.markdown(f"- {c}") for c in gr.cnpjs_coligadas]

    # Quality
    if d.quality_report:
        with st.expander("✅ Quality Gate"):
            for ch in d.quality_report.checks:
                st.markdown(f"{'✅' if ch.passou else '❌'} **{ch.criterio}** — {ch.nota}")
            if d.quality_report.audit_ia:
                ai = d.quality_report.audit_ia
                st.markdown(f"**Nota IA:** {ai.get('nota_final', 'N/A')}/10 — {ai.get('nivel', '')}")
                if ai.get('scores'):
                    for k, v in ai['scores'].items():
                        if isinstance(v, dict): st.markdown(f"  - {k}: {v.get('nota', '')}/10 — {v.get('justificativa', '')}")
            if d.quality_report.recomendacoes:
                st.markdown("**Recomendações:**"); [st.markdown(f"- {r}") for r in d.quality_report.recomendacoes]

    # Export
    st.markdown("---")
    st.markdown("### 📤 Exportar")
    md = f"# Dossie: {nome}\n**Score:** {d.sas_result.score}/1000 — {d.sas_result.tier.value}\n\n"
    for sec in d.secoes_analise: md += f"## {sec.icone} {sec.titulo}\n\n{sec.conteudo}\n\n---\n\n"
    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        st.download_button("📝 Markdown", md, f"dossie_{nome.replace(' ','_')}.md", "text/markdown", use_container_width=True)
    with ex2:
        jd = json.dumps({"empresa": nome, "score": d.sas_result.score, "tier": d.sas_result.tier.value,
                         "breakdown": d.sas_result.breakdown.to_dict(), "hectares": op.hectares_total,
                         "culturas": op.culturas, "financeiro": {"movimentos": fi.movimentos_financeiros,
                         "fiagros": fi.fiagros_relacionados, "cras": fi.cras_emitidos}}, indent=2, ensure_ascii=False)
        st.download_button("📊 JSON", jd, f"dossie_{nome.replace(' ','_')}.json", "application/json", use_container_width=True)
    with ex3:
        try:
            pdf_path = gerar_pdf(d)
            with open(pdf_path, "rb") as pf:
                st.download_button("📕 PDF", pf.read(), f"dossie_{nome.replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
        except Exception as e:
            st.warning(f"PDF indisponível: {e}")

    # Log
    with st.expander("🖥️ Pipeline Log"):
        for l in st.session_state.logs: st.text(l)
        st.caption(f"Cache: {cache.stats} | Queue: {request_queue.stats}")
```

# === TAB COMPARADOR ===

with tab_compare:
st.header(“⚖️ Comparador de Leads”)
if len(st.session_state.historico) < 2:
st.info(“Investigue pelo menos 2 empresas para comparar.”)
else:
st.markdown(“Comparação lado a lado dos últimos leads investigados:”)
hist = st.session_state.historico[-5:]
df_comp = pd.DataFrame(hist)
st.dataframe(df_comp, hide_index=True, width=“stretch”)
if len(hist) >= 2:
fig = go.Figure(go.Bar(x=[h[‘empresa’] for h in hist], y=[h[‘score’] for h in hist],
marker_color=[’#1e3a5f’ if h[‘score’] >= 751 else ‘#2d5a87’ if h[‘score’] >= 501
else ‘#6c757d’ if h[‘score’] >= 251 else ‘#adb5bd’ for h in hist],
text=[h[‘tier’] for h in hist], textposition=‘auto’))
fig.update_layout(title=“Score SAS 4.0 Comparativo”, yaxis_title=“Score”, height=400)
st.plotly_chart(fig, use_container_width=True)

# === TAB ARSENAL ===

with tab_arsenal:
st.header(“⚔️ Arsenal Tático”)
tab_conc, tab_profiler = st.tabs([“🗡️ Matador de Concorrência”, “🧠 Profiler”])

```
with tab_conc:
    st.markdown("Selecione o concorrente para ver argumentos de troca:")
    conc = st.selectbox("Concorrente:", list(ARGUMENTOS_CONCORRENCIA.keys()),
                        format_func=lambda x: ARGUMENTOS_CONCORRENCIA[x]['nome'])
    if conc:
        info = ARGUMENTOS_CONCORRENCIA[conc]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### ❌ Fraquezas do {info['nome']}")
            for f in info['fraquezas']: st.markdown(f"- 🔴 {f}")
        with c2:
            st.markdown("### ✅ Vantagens Senior")
            for v in info['senior_vantagem']: st.markdown(f"- 🟢 {v}")

with tab_profiler:
    st.markdown("Perfil do decisor baseado no tipo de empresa:")
    tipo = st.selectbox("Tipo de operação:", ["Grande Grupo (10k+ ha)", "Usina Sucroenergética",
                        "Cooperativa", "Pecuária Intensiva", "HF / Culturas Especiais", "Florestal / Celulose"])
    perfis = {
        "Grande Grupo (10k+ ha)": {"decisor": "CEO ou CFO", "perfil": "Executivo corporativo, orientado a resultado. Fala de ROI, TCO, integração. Quer referências de empresas do mesmo porte.", "abordagem": "Apresentação executiva, business case, referências de pares.", "objecoes": "Já tenho ERP / Custo de troca / Tempo de implementação"},
        "Usina Sucroenergética": {"decisor": "Diretor Industrial ou CFO", "perfil": "Técnico, entende de processo. Quer saber de CTT, moagem, RenovaBio, manutenção.", "abordagem": "Demo técnica, visita a cliente referência, POC no módulo de manutenção.", "objecoes": "TOTVS está embarcado / Complexidade de troca em safra"},
        "Cooperativa": {"decisor": "Presidente ou Dir. Administrativo", "perfil": "Político, precisa de consenso do conselho. Lento para decidir. Foca em custo e cooperado.", "abordagem": "Apresentação ao conselho, piloto com uma unidade, ROI cooperado.", "objecoes": "Sistema próprio / Assembleia precisa aprovar"},
        "Pecuária Intensiva": {"decisor": "Dono ou Dir. Operações", "perfil": "Pragmático, quer simplicidade. Foca em rastreabilidade e custos. Decisão rápida.", "abordagem": "Demo de campo, mobilidade, rastreabilidade SISBOV.", "objecoes": "Planilha resolve / Operação é simples"},
        "HF / Culturas Especiais": {"decisor": "Dono ou Gerente Geral", "perfil": "Operacional, hands-on. Foca em rastreabilidade, qualidade, RH sazonal.", "abordagem": "Demo de rastreabilidade, caso de varejo (GPA, Carrefour).", "objecoes": "Muito caro para meu porte / Complexo demais"},
        "Florestal / Celulose": {"decisor": "Dir. Florestal ou CIO", "perfil": "Técnico, ciclo longo de decisão. Foca em inventário, manutenção pesada, ambiental.", "abordagem": "POC de manutenção, integração com GIS, compliance ambiental.", "objecoes": "SAP/Oracle já implantado / Ciclo de decisão de 12+ meses"},
    }
    p = perfis.get(tipo, {})
    if p:
        st.markdown(f"**Decisor:** {p['decisor']}")
        st.markdown(f"**Perfil:** {p['perfil']}")
        st.markdown(f"**Abordagem:** {p['abordagem']}")
        st.markdown(f"**Objeções comuns:** {p['objecoes']}")
```