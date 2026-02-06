"""
app.py — Senior Scout 360 v3.3
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


def _sj(lst, n=None):
    if not lst: return ''
    items = lst[:n] if n else lst
    return ', '.join(
        str(x) if not isinstance(x, dict) else x.get('nome', x.get('titulo', x.get('sistema', str(x))))
        for x in items)


def _fmt_movimento(m):
    """Format a financial movement — handles both str and dict."""
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
    """Format a news item."""
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


st.set_page_config(page_title="Senior Scout 360", page_icon="🕵️", layout="wide")

FRASES = ["Ativando satelites...","Agentes em campo...","Rastreando CRAs...",
    "Deep Thinking ativado...","Mapeando cadeia...","Perfilando decisores...",
    "Investigando tech stack...","Varrendo grupo economico..."]

st.markdown("""<style>
div[data-testid="stMetric"]{background:linear-gradient(135deg,#1e3a5f,#2d5a87);padding:16px;border-radius:12px}
div[data-testid="stMetric"] label{color:rgba(255,255,255,.8)!important}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#fff!important;font-size:1.8rem!important}
div[data-testid="stMetric"] [data-testid="stMetricDelta"]{color:rgba(255,255,255,.9)!important}
.step-card{background:#f8f9fa;border-left:4px solid #2d5a87;padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:8px}
.step-success{border-left-color:#28a745}.step-warning{border-left-color:#ffc107}
.news-card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px}
.reco-badge{display:inline-block;padding:4px 12px;border-radius:16px;font-weight:600;font-size:0.85em}
</style>""", unsafe_allow_html=True)

for k in ['dossie','logs','historico','step_results']:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ['logs','historico','step_results'] else None

# === SIDEBAR ===
with st.sidebar:
    st.title("🕵️ Senior Scout 360")
    st.caption("Intelligence Platform")
    st.markdown("---")
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Key OK")
    except (FileNotFoundError, KeyError):
        api_key = st.text_input("API Key:", type="password")
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
        st.markdown("Plataforma de inteligencia comercial para o agronegocio.")
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
            import traceback; st.code(traceback.format_exc())

    # === RESULTADO ===
    if st.session_state.dossie:
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        op = d.dados_operacionais; fi = d.dados_financeiros; cv = d.cadeia_valor; gr = d.grupo_economico

        # Header
        cs,ci,cq = st.columns([1,2,1])
        with cs:
            st.metric("Score", f"{d.sas_result.score}/1000", d.sas_result.tier.value)
            if d.sas_result.recomendacao_comercial:
                st.caption(f"🎯 {d.sas_result.recomendacao_comercial}")
        with ci:
            st.subheader(f"📋 {nome}")
            badges = op.verticalizacao.listar_ativos()
            if badges: st.markdown(" ".join([f"`{b}`" for b in badges[:10]]))
            st.caption(f"⏱️ {d.tempo_total_segundos:.0f}s | 📅 {d.timestamp_geracao}")
        with cq:
            if d.quality_report:
                lc = {"EXCELENTE":"🟢","BOM":"🔵","ACEITAVEL":"🟡","INSUFICIENTE":"🔴"}
                st.metric("Quality Gate", f"{d.quality_report.score_qualidade:.0f}%",
                    f"{lc.get(d.quality_report.nivel.value,'')} {d.quality_report.nivel.value}")
                if d.sas_result.confidence_score:
                    st.caption(f"Confidence: {d.sas_result.confidence_score:.0f}%")
        st.markdown("---")

        # === PERFIL DA EMPRESA (enriquecido) ===
        st.markdown("### 🏢 Perfil da Empresa")
        cp1, cp2 = st.columns([2, 1])
        with cp1:
            # Build rich description
            parts = [f"**{nome}**"]
            if fi.faturamento_estimado: parts.append(f"com faturamento estimado de **R${fi.faturamento_estimado/1e6:.0f}M**")
            elif fi.capital_social_estimado: parts.append(f"com capital de **R${fi.capital_social_estimado/1e6:.0f}M**")
            if op.hectares_total: parts.append(f"e **{op.hectares_total:,} hectares**")
            if op.culturas: parts.append(f"atuando em **{_sj(op.culturas)}**")
            if op.regioes_atuacao: parts.append(f"nas regioes **{_sj(op.regioes_atuacao)}**")
            st.markdown(" ".join(parts) + ".")
            # Infrastructure
            if badges:
                infra = ", ".join(badges)
                st.markdown(f"**Infraestrutura:** {infra}")
            if fi.funcionarios_estimados:
                st.markdown(f"**Funcionarios:** ~{fi.funcionarios_estimados:,}")
            if op.numero_fazendas:
                st.markdown(f"**Fazendas/Unidades:** {op.numero_fazendas}")
            if cv.posicao_cadeia:
                st.markdown(f"**Posicao na cadeia:** {cv.posicao_cadeia} | **Integracao:** {cv.integracao_vertical_nivel}")
            if cv.exporta and cv.mercados_exportacao:
                st.markdown(f"**Exportacao:** {_sj(cv.mercados_exportacao, 5)}")
            if cv.certificacoes:
                st.markdown(f"**Certificacoes:** {_sj(cv.certificacoes)}")
            if fi.resumo_financeiro:
                st.info(fi.resumo_financeiro)
        with cp2:
            if d.dados_cnpj:
                dc = d.dados_cnpj
                st.markdown(f"**CNPJ:** {formatar_cnpj(dc.cnpj)}")
                st.markdown(f"**CNAE:** {dc.cnae_principal}")
                st.markdown(f"**Capital:** R${dc.capital_social:,.0f}")
                if dc.natureza_juridica:
                    st.markdown(f"**Nat. Jur.:** {dc.natureza_juridica}")
                st.markdown(f"**Local:** {dc.municipio}/{dc.uf}")
                if dc.qsa:
                    st.markdown(f"**Socios (QSA):** {len(dc.qsa)}")
        st.markdown("---")

        # === MOVIMENTOS FINANCEIROS ===
        movs = fi.movimentos_financeiros
        cras = fi.cras_emitidos
        fiagros = fi.fiagros_relacionados
        if movs or cras or fiagros:
            st.markdown("### 💰 Movimentos Financeiros & Governanca")
            cm, cf2 = st.columns(2)
            with cm:
                if movs:
                    for m in movs:
                        st.markdown(f"🏦 {_fmt_movimento(m)}")
            with cf2:
                if cras:
                    st.markdown("**CRAs:**")
                    for c in cras:
                        st.markdown(f"📜 {_fmt_movimento(c)}")
                if fiagros:
                    st.markdown("**Fiagros:**")
                    for f in fiagros:
                        st.markdown(f"📈 {_fmt_movimento(f)}")
                if fi.auditorias:
                    st.markdown("**Auditorias:**")
                    for a in fi.auditorias:
                        st.markdown(f"✅ {_fmt_movimento(a)}")
                if fi.parceiros_financeiros:
                    st.markdown("**Parceiros:**")
                    for p in fi.parceiros_financeiros:
                        st.markdown(f"🤝 {_fmt_movimento(p)}")
            st.markdown("---")

        # === RAIO-X ===
        st.markdown("### 📊 Raio-X da Operacao")
        mc = st.columns(6)
        mc[0].metric("Area", f"{op.hectares_total:,} ha" if op.hectares_total else "N/D")
        mc[1].metric("Funcionarios", f"{fi.funcionarios_estimados:,}" if fi.funcionarios_estimados else "N/D")
        mc[2].metric("Capital", f"R${fi.capital_social_estimado/1e6:.1f}M" if fi.capital_social_estimado else "N/D")
        mc[3].metric("Culturas", _sj(op.culturas, 3) if op.culturas else "N/D")
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
                    if dec.get('formacao') and dec['formacao'] not in ['Nao encontrado','N/I','']:
                        det.append(f"🎓 {dec['formacao']}")
                    if dec.get('experiencia_anterior') and dec['experiencia_anterior'] not in ['Nao encontrado','N/I','']:
                        det.append(f"📋 {dec['experiencia_anterior']}")
                    if dec.get('tempo_cargo') and dec['tempo_cargo'] not in ['Nao encontrado','N/I','']:
                        det.append(f"⏱️ {dec['tempo_cargo']}")
                    if det: st.caption(" | ".join(det))
                with col2:
                    lnk = dec.get('linkedin','')
                    if lnk and lnk not in ['Nao encontrado','N/I','']:
                        st.markdown(f"[🔗 LinkedIn]({lnk})")
                    st.caption(f"Relevancia: **{rel}**")
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
                if erp.get('sistema') and erp['sistema'] not in ['N/I','']:
                    st.markdown(f"**ERP Principal:** 🖥️ **{erp['sistema']}** {erp.get('versao','')}")
                    st.caption(f"Fonte: {erp.get('fonte_evidencia','')} | Conf: {erp.get('confianca',0):.0%}")
                else:
                    st.markdown("**ERP Principal:** Nao identificado")
                mat_ti = ts.get('nivel_maturidade_ti','')
                inv_ti = ts.get('investimento_ti_percebido','')
                if mat_ti: st.markdown(f"**Maturidade TI:** {mat_ti}")
                if inv_ti: st.markdown(f"**Investimento TI:** {inv_ti}")
            with ct2:
                outros = ts.get('outros_sistemas', [])
                if outros:
                    st.markdown("**Outros sistemas:**")
                    for o in outros:
                        if isinstance(o, dict):
                            st.markdown(f"- {o.get('tipo','')}: **{o.get('sistema','')}**")
                        else:
                            st.markdown(f"- {o}")
                vagas = ts.get('vagas_ti_abertas', [])
                if vagas:
                    st.markdown("**Vagas TI abertas:**")
                    for v in vagas:
                        if isinstance(v, dict):
                            st.markdown(f"- 📋 {v.get('titulo','')} ({_sj(v.get('sistemas_mencionados',[]))})")
                        else:
                            st.markdown(f"- {v}")
            dores_t = ts.get('dores_tech_identificadas', [])
            if dores_t:
                st.markdown("**Dores tech:**")
                for x in dores_t:
                    st.markdown(f"- ⚠️ {x}")
            st.markdown("---")

        # === GRUPO ECONOMICO ===
        if gr.total_empresas > 0:
            with st.expander(f"🏛️ Grupo Economico ({gr.total_empresas} empresas)", expanded=False):
                if gr.cnpj_matriz: st.markdown(f"**CNPJ Matriz:** {gr.cnpj_matriz}")
                if hasattr(gr, 'holding_controladora') and gr.holding_controladora:
                    st.markdown(f"**Holding:** {gr.holding_controladora}")
                if gr.controladores:
                    st.markdown(f"**Controladores:** {_sj(gr.controladores)}")
                filiais = gr.cnpjs_filiais
                if filiais:
                    st.markdown(f"#### Filiais ({len(filiais)})")
                    if isinstance(filiais[0], dict):
                        df_fil = pd.DataFrame(filiais)
                        st.dataframe(df_fil, hide_index=True, use_container_width=True)
                    else:
                        for f_item in filiais:
                            st.markdown(f"- {f_item}")
                colig = gr.cnpjs_coligadas
                if colig:
                    st.markdown(f"#### Coligadas ({len(colig)})")
                    if isinstance(colig[0], dict):
                        df_col = pd.DataFrame(colig)
                        st.dataframe(df_col, hide_index=True, use_container_width=True)
                    else:
                        for c_item in colig:
                            st.markdown(f"- {c_item}")

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
            df = pd.DataFrame([
                {"Pilar":"Musculo","Pts":b.musculo,"Max":400,"Pct":f"{b.musculo/4:.0f}%"},
                {"Pilar":"Complexidade","Pts":b.complexidade,"Max":250,"Pct":f"{b.complexidade/2.5:.0f}%"},
                {"Pilar":"Gente","Pts":b.gente,"Max":200,"Pct":f"{b.gente/2:.0f}%"},
                {"Pilar":"Momento","Pts":b.momento,"Max":150,"Pct":f"{b.momento/1.5:.0f}%"},
            ])
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.markdown(f"**Total: {d.sas_result.score}/1000** — {d.sas_result.tier.value}")
            if d.sas_result.vertical_detectada:
                st.caption(f"Vertical: {d.sas_result.vertical_detectada} | Conf: {d.sas_result.confidence_score:.0f}%")
        if d.sas_result.justificativas:
            with st.expander("🔍 Justificativas"):
                for j in d.sas_result.justificativas:
                    st.text(f"→ {j}")
        st.markdown("---")

        # === INTEL ===
        il = d.intel_mercado
        if il.sinais_compra or il.dores_identificadas:
            st.markdown("### 📡 Inteligencia de Mercado")
            ti1,ti2,ti3 = st.tabs(["🎯 Sinais","📰 Noticias","⚠️ Riscos"])
            with ti1:
                for s in il.sinais_compra:
                    st.markdown(f"🟢 {s}")
                if il.dores_identificadas:
                    st.markdown("**Dores:**")
                    for x in il.dores_identificadas:
                        st.markdown(f"🔴 {x}")
            with ti2:
                for n in il.noticias_recentes:
                    st.markdown(_fmt_noticia(n))
                    st.markdown("---")
            with ti3:
                cr1,co1 = st.columns(2)
                with cr1:
                    st.markdown("**Riscos:**")
                    for r in il.riscos:
                        st.markdown(f"⚠️ {r}")
                with co1:
                    st.markdown("**Oportunidades:**")
                    for o in il.oportunidades:
                        st.markdown(f"💡 {o}")
            st.markdown("---")

        # === NOTICIAS RELEVANTES (nova secao dedicada) ===
        noticias = il.noticias_recentes if il.noticias_recentes else []
        if noticias and any(isinstance(n, dict) for n in noticias):
            st.markdown("### 📰 Noticias Relevantes")
            for n in noticias:
                if isinstance(n, dict):
                    titulo = n.get('titulo', '')
                    resumo = n.get('resumo', '')
                    data = n.get('data_aprox', n.get('data', ''))
                    fonte = n.get('fonte', '')
                    rel = n.get('relevancia', '')
                    with st.container():
                        st.markdown(f"**{titulo}**" + (f" — {data}" if data else ""))
                        if resumo: st.caption(resumo)
                        tags_html = ""
                        if fonte: tags_html += f"`{fonte}`  "
                        if rel: tags_html += f"{'🔴' if rel=='alta' else '🟡' if rel=='media' else '⚪'} {rel}"
                        if tags_html: st.markdown(tags_html)
                        st.markdown("---")

        # === ANALISE ===
        st.markdown("### 🧠 Inteligencia Estrategica")
        for sec in d.secoes_analise:
            with st.expander(f"{sec.icone} {sec.titulo}", expanded=True):
                st.markdown(sec.conteudo)
        st.markdown("---")

        # === QUALITY ===
        if d.quality_report:
            with st.expander("✅ Quality Gate"):
                for ch in d.quality_report.checks:
                    st.markdown(f"{'✅' if ch.passou else '❌'} **{ch.criterio}** — {ch.nota}")
                if d.quality_report.audit_ia:
                    ai = d.quality_report.audit_ia
                    st.markdown(f"**Nota IA:** {ai.get('nota_final','N/A')}/10 — {ai.get('nivel','')}")

        # === EXPORT ===
        st.markdown("### 📤 Exportar")
        md = f"# Dossie: {nome}\n**Score:** {d.sas_result.score}/1000 — {d.sas_result.tier.value}\n\n"
        for sec in d.secoes_analise:
            md += f"## {sec.icone} {sec.titulo}\n\n{sec.conteudo}\n\n---\n\n"
        ex1,ex2,ex3 = st.columns(3)
        with ex1:
            st.download_button("📝 MD", md, f"dossie_{nome.replace(' ','_')}.md", "text/markdown", use_container_width=True)
        with ex2:
            jd = json.dumps({"empresa":nome,"score":d.sas_result.score,"tier":d.sas_result.tier.value,
                "recomendacao":d.sas_result.recomendacao_comercial,
                "decisores":d.decisores,"tech_stack":d.tech_stack}, indent=2, ensure_ascii=False, default=str)
            st.download_button("📊 JSON", jd, f"dossie_{nome.replace(' ','_')}.json", use_container_width=True)
        with ex3:
            try:
                pp = gerar_pdf(d)
                pf = open(pp, "rb")
                st.download_button("📕 PDF", pf.read(), f"dossie_{nome.replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
            except Exception:
                st.warning("PDF indisponivel (instale fpdf2)")

# === COMPARADOR ===
with tab_compare:
    st.header("⚖️ Comparador")
    if len(st.session_state.historico) < 2:
        st.info("Investigue 2+ empresas.")
    else:
        hist = st.session_state.historico[-5:]
        st.dataframe(pd.DataFrame(hist), hide_index=True, use_container_width=True)
        fig = go.Figure(go.Bar(x=[h['empresa'] for h in hist], y=[h['score'] for h in hist],
            marker_color=['#1e3a5f' if h['score']>=751 else '#2d5a87' if h['score']>=501 else '#adb5bd' for h in hist],
            text=[h['tier'] for h in hist], textposition='auto'))
        fig.update_layout(title="Score SAS", yaxis_title="Score", height=400)
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
            with c1:
                st.markdown("### ❌ Fraquezas")
                for f_item in info['fraquezas']:
                    st.markdown(f"🔴 {f_item}")
            with c2:
                st.markdown("### ✅ Senior")
                for v_item in info['senior_vantagem']:
                    st.markdown(f"🟢 {v_item}")
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
            st.markdown(f"**Decisor:** {p['d']}")
            st.markdown(f"**Perfil:** {p['p']}")
            st.markdown(f"**Abordagem:** {p['a']}")
            st.markdown(f"**Objecoes:** {p['o']}")
