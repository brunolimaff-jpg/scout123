"""
app.py — Senior Scout 360 v3.2
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time, random, json
from services.dossier_orchestrator import gerar_dossie_completo
from services.cnpj_service import formatar_cnpj, validar_cnpj, limpar_cnpj
from services.cache_service import cache
from services.request_queue import request_queue
from utils.market_intelligence import ARGUMENTOS_CONCORRENCIA
from utils.pdf_export import gerar_pdf
from scout_types import DossieCompleto, Tier, QualityLevel

st.set_page_config(page_title="Senior Scout 360 v3.2", page_icon="🕵️", layout="wide")

FRASES = ["🛰️ Ativando satelites...","📡 9 agentes Pro em campo...","💰 Rastreando CRAs...",
    "🧠 Deep Thinking 12k tokens...","🔗 Mapeando cadeia...","👔 Perfilando decisores...",
    "💻 Investigando tech stack...","🏛️ Varrendo grupo economico..."]

st.markdown("""<style>
div[data-testid="stMetric"]{background:linear-gradient(135deg,#1e3a5f,#2d5a87);padding:16px;border-radius:12px}
div[data-testid="stMetric"] label{color:rgba(255,255,255,.8)!important}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#fff!important;font-size:1.8rem!important}
div[data-testid="stMetric"] [data-testid="stMetricDelta"]{color:rgba(255,255,255,.9)!important}
.step-card{background:#f8f9fa;border-left:4px solid #2d5a87;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:8px}
.step-success{border-left-color:#28a745}.step-warning{border-left-color:#ffc107}
</style>""", unsafe_allow_html=True)

for k in ['dossie','logs','historico','step_results']:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ['logs','historico','step_results'] else None

# === SIDEBAR ===
with st.sidebar:
    st.title("🕵️ Senior Scout 360")
    st.caption("v3.2 | All Pro | 9 Agents | Full Agro")
    st.markdown("---")
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Key OK")
    except (FileNotFoundError, KeyError):
        api_key = st.text_input("Gemini API Key:", type="password")
        if not api_key: st.error("Insira API Key"); st.stop()
    st.markdown("---")
    target = st.text_input("🎯 Empresa / Grupo", placeholder="Ex: SLC Agricola...")
    target_cnpj = st.text_input("CNPJ (opcional)", placeholder="XX.XXX.XXX/XXXX-XX")
    if target_cnpj:
        cl = limpar_cnpj(target_cnpj)
        if cl and validar_cnpj(cl): st.caption(f"✅ {formatar_cnpj(cl)}")
        elif cl: st.caption("❌ Invalido")
    st.markdown("---")
    btn = st.button("🚀 Investigacao Completa", type="primary", disabled=not target, use_container_width=True)
    st.markdown("---")
    st.info("**Pipeline v3.2 (10 Passos)**\n\n"
        "1. 📋 CNPJ\n2. 🛰️ Recon Operacional\n3. 💰 Sniper Financeiro\n"
        "4. 🔗 Cadeia de Valor\n5. 🏛️ Grupo Economico\n6. 📡 Intel Mercado\n"
        "7. 👔 Profiler Decisores\n8. 💻 Tech Stack Hunter\n"
        "9. 🧠 Analise Estrategica\n10. ✅ Quality Gate\n\n*Todos no Gemini 2.5 Pro*")
    if st.session_state.historico:
        st.markdown("---")
        st.subheader("📚 Historico")
        for h in reversed(st.session_state.historico[-8:]):
            st.caption(f"- {h['empresa']} — {h['tier']} ({h['score']})")

# === TABS ===
tab_scout, tab_compare, tab_arsenal = st.tabs(["🕵️ Scout", "⚖️ Comparador", "⚔️ Arsenal"])

with tab_scout:
    if not target and not st.session_state.dossie:
        st.header("🕵️ Senior Scout 360")
        st.markdown("**9 agentes de IA** no Gemini 2.5 Pro investigam empresas do agro.")
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown("#### 🛰️ Recon\nHectares, culturas, vert.")
        with c2: st.markdown("#### 💰 Financas\nCRAs, Fiagros, gov.")
        with c3: st.markdown("#### 👔 Decisores\nNomes, cargos, LinkedIn")
        with c4: st.markdown("#### 💻 Tech Stack\nQual ERP usam hoje")

    elif btn and target:
        st.session_state.dossie = None; st.session_state.logs = []; st.session_state.step_results = []
        st.header(f"🔍 Investigando: {target}")
        progress_bar = st.progress(0.0); status = st.empty(); step_ctn = st.container()
        def on_progress(p, m):
            progress_bar.progress(min(p, 1.0)); status.markdown(f"**{m}** — _{random.choice(FRASES)}_")
        def on_step(s):
            st.session_state.step_results.append(s)
            ic = {"success":"✅","warning":"⚠️","error":"❌"}.get(s.status,"⏳")
            with step_ctn:
                cls = f"step-{s.status}"
                h = f'<div class="step-card {cls}"><b>{ic} {s.step_number}. {s.step_name}</b>'
                h += f' <span style="float:right">{s.tempo_segundos:.1f}s</span><br>'
                h += f'<span style="color:#555">{s.resumo}</span>'
                if s.confianca > 0: h += f' | Conf: {s.confianca:.0%}'
                if s.detalhes: h += '<br><small style="color:#777">' + ' | '.join(s.detalhes[:4]) + '</small>'
                h += '</div>'; st.markdown(h, unsafe_allow_html=True)
        try:
            dossie = gerar_dossie_completo(target, api_key, target_cnpj, log_cb=lambda m: st.session_state.logs.append(m),
                                            progress_cb=on_progress, step_cb=on_step)
            st.session_state.dossie = dossie
            st.session_state.historico.append({'empresa': dossie.dados_operacionais.nome_grupo or target,
                'score': dossie.sas_result.score, 'tier': dossie.sas_result.tier.value})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro: {e}")
            with st.expander("Log"): [st.text(l) for l in st.session_state.logs]

    # === RESULTADO ===
    if st.session_state.dossie:
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        op = d.dados_operacionais; fi = d.dados_financeiros; cv = d.cadeia_valor; gr = d.grupo_economico

        # Header
        cs,ci,cq = st.columns([1,2,1])
        with cs: st.metric("SAS 4.0", f"{d.sas_result.score}/1000", d.sas_result.tier.value)
        with ci:
            st.subheader(f"📋 {nome}")
            badges = op.verticalizacao.listar_ativos()
            if badges: st.markdown(" ".join([f"`{b}`" for b in badges[:10]]))
            st.caption(f"⏱️ {d.tempo_total_segundos:.0f}s | 📅 {d.timestamp_geracao} | 🤖 {d.modelo_usado}")
        with cq:
            if d.quality_report:
                lc = {"EXCELENTE":"🟢","BOM":"🔵","ACEITAVEL":"🟡","INSUFICIENTE":"🔴"}
                st.metric("Quality Gate", f"{d.quality_report.score_qualidade:.0f}%",
                    f"{lc.get(d.quality_report.nivel.value,'')} {d.quality_report.nivel.value}")
        st.markdown("---")

        # === PERFIL DA EMPRESA (novo - primeiro) ===
        st.markdown("### 🏢 Perfil da Empresa")
        cp1, cp2 = st.columns([2, 1])
        with cp1:
            desc_parts = []
            desc_parts.append(f"**{nome}** e um grupo do agronegocio brasileiro")
            if op.hectares_total: desc_parts.append(f"com **{op.hectares_total:,} hectares**")
            if op.culturas: desc_parts.append(f"atuando em **{', '.join(op.culturas)}**")
            if op.regioes_atuacao: desc_parts.append(f"nas regioes **{', '.join(op.regioes_atuacao)}**")
            if fi.funcionarios_estimados: desc_parts.append(f"com aproximadamente **{fi.funcionarios_estimados:,} funcionarios**")
            if fi.faturamento_estimado: desc_parts.append(f"e faturamento estimado de **R${fi.faturamento_estimado/1e6:.0f}M**")
            st.markdown(" ".join(desc_parts) + ".")
            if fi.resumo_financeiro: st.markdown(f"_{fi.resumo_financeiro}_")
            if cv.posicao_cadeia:
                st.markdown(f"**Posicao na cadeia:** {cv.posicao_cadeia} | **Integracao:** {cv.integracao_vertical_nivel}")
            if cv.exporta:
                st.markdown(f"**Exportacao:** {', '.join(cv.mercados_exportacao[:5])}")
            if cv.certificacoes:
                st.markdown(f"**Certificacoes:** {', '.join(cv.certificacoes)}")
        with cp2:
            if d.dados_cnpj:
                dc = d.dados_cnpj
                st.markdown(f"**CNPJ:** {formatar_cnpj(dc.cnpj)}")
                st.markdown(f"**CNAE:** {dc.cnae_principal}")
                st.markdown(f"**Capital:** R${dc.capital_social:,.0f}")
                st.markdown(f"**Nat. Jur.:** {dc.natureza_juridica}")
                st.markdown(f"**Local:** {dc.municipio}/{dc.uf}")
        st.markdown("---")

        # === MOVIMENTOS FINANCEIROS (com contexto) ===
        if fi.movimentos_financeiros or fi.fiagros_relacionados:
            st.markdown("### 💰 Movimentos Financeiros & Governanca")
            cm, cf2 = st.columns(2)
            with cm:
                for m in fi.movimentos_financeiros: st.markdown(f"- 🏦 **{m}**")
            with cf2:
                if fi.fiagros_relacionados: st.markdown("**Fiagros:**"); [st.markdown(f"- 📈 {f}") for f in fi.fiagros_relacionados]
                if fi.cras_emitidos: st.markdown("**CRAs:**"); [st.markdown(f"- 📜 {c}") for c in fi.cras_emitidos]
                if fi.auditorias: st.markdown("**Auditorias:**"); [st.markdown(f"- ✅ {a}") for a in fi.auditorias]
                if fi.parceiros_financeiros: st.markdown("**Parceiros:**"); [st.markdown(f"- 🤝 {p}") for p in fi.parceiros_financeiros]
            st.markdown("---")

        # === RAIO-X ===
        st.markdown("### 📊 Raio-X da Operacao")
        mc = st.columns(6)
        mc[0].metric("Area", f"{op.hectares_total:,} ha" if op.hectares_total else "N/D")
        mc[1].metric("Funcionarios", f"{fi.funcionarios_estimados:,}" if fi.funcionarios_estimados else "N/D")
        mc[2].metric("Capital", f"R${fi.capital_social_estimado/1e6:.1f}M" if fi.capital_social_estimado else "N/D")
        mc[3].metric("Culturas", ", ".join(op.culturas[:3]) if op.culturas else "N/D")
        mc[4].metric("Fazendas", str(op.numero_fazendas) if op.numero_fazendas else "N/D")
        mc[5].metric("Grupo", f"{gr.total_empresas} emp" if gr.total_empresas else "N/D")
        st.markdown("---")

        # === DECISORES ===
        decs = d.decisores.get('decisores', []) if d.decisores else []
        if decs:
            st.markdown("### 👔 Decisores-Chave")
            for dec in decs:
                rel = dec.get('relevancia_erp','')
                ic = "🔴" if rel == 'alta' else "🟡" if rel == 'media' else "⚪"
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**{ic} {dec.get('nome','')}** — {dec.get('cargo','')}")
                    det = []
                    if dec.get('formacao'): det.append(f"🎓 {dec['formacao']}")
                    if dec.get('experiencia_anterior'): det.append(f"📋 {dec['experiencia_anterior']}")
                    if dec.get('tempo_cargo'): det.append(f"⏱️ {dec['tempo_cargo']}")
                    if det: st.caption(" | ".join(det))
                with col2:
                    if dec.get('linkedin'): st.markdown(f"[🔗 LinkedIn]({dec['linkedin']})")
                    st.caption(f"Relevancia ERP: **{rel}**")
            est = d.decisores.get('estrutura_decisao','')
            mat = d.decisores.get('nivel_maturidade_gestao','')
            if est or mat: st.caption(f"Estrutura: {est} | Maturidade: {mat}")
            st.markdown("---")

        # === TECH STACK ===
        ts = d.tech_stack if d.tech_stack else {}
        if ts:
            st.markdown("### 💻 Tech Stack Atual")
            erp = ts.get('erp_principal', {})
            ct1, ct2 = st.columns(2)
            with ct1:
                if erp.get('sistema'):
                    st.markdown(f"**ERP Principal:** 🖥️ **{erp['sistema']}** {erp.get('versao','')}")
                    st.caption(f"Fonte: {erp.get('fonte_evidencia','')} | Conf: {erp.get('confianca',0):.0%}")
                else: st.markdown("**ERP Principal:** N/I")
                st.markdown(f"**Maturidade TI:** {ts.get('nivel_maturidade_ti','N/I')}")
                st.markdown(f"**Investimento TI:** {ts.get('investimento_ti_percebido','N/I')}")
            with ct2:
                outros = ts.get('outros_sistemas', [])
                if outros:
                    st.markdown("**Outros sistemas:**")
                    for o in outros: st.markdown(f"- {o.get('tipo','')}: **{o.get('sistema','')}**")
                vagas = ts.get('vagas_ti_abertas', [])
                if vagas:
                    st.markdown("**Vagas TI abertas:**")
                    for v in vagas: st.markdown(f"- 📋 {v.get('titulo','')} ({', '.join(v.get('sistemas_mencionados',[]))})")
            dores_t = ts.get('dores_tech_identificadas', [])
            if dores_t:
                st.markdown("**Dores tech:**"); [st.markdown(f"- ⚠️ {x}") for x in dores_t]
            st.markdown("---")

        # === GRUPO ECONOMICO EXPANDIDO ===
        if gr.total_empresas > 0:
            with st.expander(f"🏛️ Grupo Economico ({gr.total_empresas} empresas)", expanded=False):
                st.markdown(f"**CNPJ Matriz:** {gr.cnpj_matriz}")
                if hasattr(gr, 'holding_controladora') and gr.holding_controladora:
                    st.markdown(f"**Holding:** {gr.holding_controladora}")
                st.markdown(f"**Controladores:** {', '.join(gr.controladores)}")
                filiais = gr.cnpjs_filiais
                if filiais:
                    st.markdown(f"**Filiais ({len(filiais)}):**")
                    if isinstance(filiais[0], dict):
                        df_fil = pd.DataFrame(filiais)
                        st.dataframe(df_fil, hide_index=True, width="stretch")
                    else:
                        for f in filiais: st.markdown(f"- {f}")
                colig = gr.cnpjs_coligadas
                if colig:
                    st.markdown(f"**Coligadas ({len(colig)}):**")
                    if isinstance(colig[0], dict):
                        df_col = pd.DataFrame(colig)
                        st.dataframe(df_col, hide_index=True, width="stretch")
                    else:
                        for c in colig: st.markdown(f"- {c}")

        # === SPIDER CHART ===
        st.markdown("### 📊 Score Breakdown")
        cch, ctb = st.columns([2, 1])
        with cch:
            b = d.sas_result.breakdown
            cats = ["Musculo\n(Porte)","Complexidade","Gente\n(Gestao)","Momento\n(Gov/Tech)"]
            vals = [b.musculo, b.complexidade, b.gente, b.momento]; maxs = [400,250,200,150]
            pcts = [v/m*100 for v,m in zip(vals, maxs)]
            fig = go.Figure(go.Scatterpolar(r=pcts+[pcts[0]], theta=cats+[cats[0]], fill='toself',
                line_color='#1e3a5f', fillcolor='rgba(30,58,95,0.3)'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100], ticksuffix="%")),
                showlegend=False, height=350, margin=dict(l=60,r=60,t=30,b=30))
            st.plotly_chart(fig, use_container_width=True)
        with ctb:
            df = pd.DataFrame([{"Pilar":"Musculo","Pts":b.musculo,"Max":400},{"Pilar":"Complexidade","Pts":b.complexidade,"Max":250},
                {"Pilar":"Gente","Pts":b.gente,"Max":200},{"Pilar":"Momento","Pts":b.momento,"Max":150}])
            st.dataframe(df, hide_index=True, width="stretch")
            st.markdown(f"**Total: {d.sas_result.score}/1000** — {d.sas_result.tier.value}")
        if d.sas_result.justificativas:
            with st.expander("🔍 Justificativas"):
                for j in d.sas_result.justificativas: st.text(f"→ {j}")
        st.markdown("---")

        # === INTEL ===
        il = d.intel_mercado
        if il.noticias_recentes or il.sinais_compra:
            st.markdown("### 📡 Inteligencia de Mercado")
            ti1,ti2,ti3 = st.tabs(["🎯 Sinais","📰 Noticias","⚠️ Riscos"])
            with ti1:
                for s in il.sinais_compra: st.markdown(f"- 🟢 {s}")
                if il.dores_identificadas: st.markdown("**Dores:**"); [st.markdown(f"- 🔴 {x}") for x in il.dores_identificadas]
            with ti2:
                for n in il.noticias_recentes:
                    if isinstance(n, dict): st.markdown(f"**{n.get('titulo','')}** ({n.get('data_aprox','')})\n\n{n.get('resumo','')}")
                    else: st.markdown(f"- {n}")
            with ti3:
                cr1,co1 = st.columns(2)
                with cr1: [st.markdown(f"- ⚠️ {r}") for r in il.riscos]
                with co1: [st.markdown(f"- 💡 {o}") for o in il.oportunidades]
            st.markdown("---")

        # === ANALISE ===
        st.markdown("### 🧠 Inteligencia Estrategica")
        for sec in d.secoes_analise:
            with st.expander(f"{sec.icone} {sec.titulo}", expanded=True): st.markdown(sec.conteudo)
        st.markdown("---")

        # === QUALITY ===
        if d.quality_report:
            with st.expander("✅ Quality Gate"):
                for ch in d.quality_report.checks: st.markdown(f"{'✅' if ch.passou else '❌'} **{ch.criterio}** — {ch.nota}")
                if d.quality_report.audit_ia:
                    ai = d.quality_report.audit_ia
                    st.markdown(f"**Nota IA:** {ai.get('nota_final','N/A')}/10 — {ai.get('nivel','')}")

        # === EXPORT ===
        st.markdown("### 📤 Exportar")
        md = f"# Dossie: {nome}\n**Score:** {d.sas_result.score}/1000 — {d.sas_result.tier.value}\n\n"
        for sec in d.secoes_analise: md += f"## {sec.icone} {sec.titulo}\n\n{sec.conteudo}\n\n---\n\n"
        ex1,ex2,ex3 = st.columns(3)
        with ex1: st.download_button("📝 MD", md, f"dossie_{nome.replace(' ','_')}.md", "text/markdown", use_container_width=True)
        with ex2:
            jd = json.dumps({"empresa":nome,"score":d.sas_result.score,"tier":d.sas_result.tier.value,
                "decisores":d.decisores,"tech_stack":d.tech_stack}, indent=2, ensure_ascii=False, default=str)
            st.download_button("📊 JSON", jd, f"dossie_{nome.replace(' ','_')}.json", use_container_width=True)
        with ex3:
            try:
                pp = gerar_pdf(d); pf = open(pp,"rb")
                st.download_button("📕 PDF", pf.read(), f"dossie_{nome.replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
            except Exception: st.warning("PDF indisponivel (instale fpdf2)")
        with st.expander("🖥️ Pipeline Log"):
            for l in st.session_state.logs: st.text(l)
            st.caption(f"Cache: {cache.stats} | Queue: {request_queue.stats}")

# === COMPARADOR ===
with tab_compare:
    st.header("⚖️ Comparador")
    if len(st.session_state.historico) < 2: st.info("Investigue 2+ empresas.")
    else:
        hist = st.session_state.historico[-5:]
        st.dataframe(pd.DataFrame(hist), hide_index=True, width="stretch")
        fig = go.Figure(go.Bar(x=[h['empresa'] for h in hist], y=[h['score'] for h in hist],
            marker_color=['#1e3a5f' if h['score']>=751 else '#2d5a87' if h['score']>=501 else '#adb5bd' for h in hist],
            text=[h['tier'] for h in hist], textposition='auto'))
        fig.update_layout(title="Score SAS 4.0", yaxis_title="Score", height=400)
        st.plotly_chart(fig, use_container_width=True)

# === ARSENAL ===
with tab_arsenal:
    st.header("⚔️ Arsenal Tatico")
    tab_conc, tab_prof = st.tabs(["🗡️ Matador Concorrencia", "🧠 Profiler"])
    with tab_conc:
        conc = st.selectbox("Concorrente:", list(ARGUMENTOS_CONCORRENCIA.keys()),
            format_func=lambda x: ARGUMENTOS_CONCORRENCIA[x]['nome'])
        if conc:
            info = ARGUMENTOS_CONCORRENCIA[conc]
            c1,c2 = st.columns(2)
            with c1: st.markdown(f"### ❌ Fraquezas"); [st.markdown(f"- 🔴 {f}") for f in info['fraquezas']]
            with c2: st.markdown("### ✅ Senior"); [st.markdown(f"- 🟢 {v}") for v in info['senior_vantagem']]
    with tab_prof:
        tipo = st.selectbox("Tipo:", ["Grande Grupo (10k+ ha)","Usina","Cooperativa","Pecuaria","HF","Florestal"])
        perfis = {
            "Grande Grupo (10k+ ha)": {"d":"CEO/CFO","p":"Corporativo, ROI, TCO","a":"Business case, referencias","o":"Ja tenho ERP"},
            "Usina": {"d":"Dir. Industrial/CFO","p":"Tecnico, CTT, RenovaBio","a":"Demo tecnica, POC manutencao","o":"TOTVS embarcado"},
            "Cooperativa": {"d":"Presidente/Dir. Admin","p":"Politico, consenso conselho","a":"Piloto 1 unidade, ROI","o":"Sistema proprio"},
            "Pecuaria": {"d":"Dono/Dir. Ops","p":"Pragmatico, simplicidade","a":"Demo campo, SISBOV","o":"Planilha resolve"},
            "HF": {"d":"Dono/Gerente","p":"Operacional, rastreabilidade","a":"Demo rastreabilidade","o":"Caro demais"},
            "Florestal": {"d":"Dir. Florestal/CIO","p":"Tecnico, ciclo longo","a":"POC manutencao, GIS","o":"SAP implantado"},
        }
        p = perfis.get(tipo, {})
        if p:
            st.markdown(f"**Decisor:** {p['d']}"); st.markdown(f"**Perfil:** {p['p']}")
            st.markdown(f"**Abordagem:** {p['a']}"); st.markdown(f"**Objecoes:** {p['o']}")
