"""
app.py — RADAR FOX-3 v2.1 | Intelligence System COMPLETO
DOSSIÊ ULTRA-DETALHADO: Decisores, Grupo Econômico, Intel Completa, Tech Stack
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
    from services.market_estimator import calcular_sas
    from services.data_validator import safe_float, safe_int, safe_str
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

.section-header {
    font-family: 'Rajdhani', sans-serif;
    color: #38BDF8;
    font-size: 1.6rem;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 2px solid #334155;
    padding-bottom: 5px;
    margin-top: 30px;
    margin-bottom: 20px;
}

.info-card {
    background: #1E293B;
    border-left: 4px solid #38BDF8;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 4px;
}

.warning-card {
    background: #1E293B;
    border-left: 4px solid #F59E0B;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 4px;
}

.success-card {
    background: #1E293B;
    border-left: 4px solid #10B981;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 4px;
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
        <div style="font-family:'Rajdhani';font-weight:900;font-size:2.5rem;color:#38BDF8;letter-spacing:6px;">RADAR</div>
        <div style="font-family:'JetBrains Mono';font-size:0.65rem;color:#64748B;letter-spacing:2px;margin-top:10px;">
            SYSTEM: ONLINE<br>
            v2.1 | FULL INTEL
        </div>
    </div>""", unsafe_allow_html=True)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        api_key = st.text_input("🔑 API KEY", type="password")
    
    st.markdown('---')
    target = st.text_input("🎯 Empresa Alvo", placeholder="Ex: GRUPO SCHEFFER")
    target_cnpj = st.text_input("🏷️ CNPJ (Opcional)", placeholder="XX.XXX.XXX/XXXX-XX")
    st.markdown('---')
    
    btn_label = "🦊 FOX 3 - DISPARAR" if target else "⛔ AGUARDANDO ALVO"
    btn = st.button(btn_label, type="primary", disabled=not target, use_container_width=True)

# ==============================================================================
# MAIN — FLIGHT DECK (HUD)
# ==============================================================================
tab_dossie, tab_raw = st.tabs(["📋 DOSSIÊ COMPLETO", "📦 RAW DATA"])

with tab_dossie:
    # TELA DE ESPERA
    if not target and not st.session_state.dossie:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;">
            <div style="font-size:4rem;opacity:0.3;">⌖</div>
            <div style="font-family:'Rajdhani';font-size:1.5rem;color:#64748B;">NO TARGET ACQUIRED</div>
            <div style="font-family:'JetBrains Mono';font-size:0.8rem;color:#475569;margin-top:10px;">
                INSIRA COORDENADAS NO PAINEL LATERAL
            </div>
        </div>""", unsafe_allow_html=True)

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

    # RESULTADO COMPLETO
    if st.session_state.dossie:
        d = st.session_state.dossie
        nome = d.dados_operacionais.nome_grupo or d.empresa_alvo
        
        # =================================================================
        # HEADER COM SCORE
        # =================================================================
        col_nome, col_score = st.columns([3, 1])
        with col_nome:
            st.markdown(f"# {nome.upper()}")
            st.markdown(f"✅ **Target Locked** | {d.timestamp_geracao}")
        with col_score:
            tier_color = "#10B981" if d.sas_result.score >= 700 else "#38BDF8" if d.sas_result.score >= 500 else "#F59E0B"
            st.markdown(f"""
            <div style="text-align:right;padding:15px;background:#1E293B;border-left:4px solid {tier_color};">
                <div style="color:#64748B;font-size:0.7rem;">SAS SCORE</div>
                <div style="color:{tier_color};font-size:2.5rem;font-weight:700;line-height:1;">{d.sas_result.score}</div>
                <div style="color:{tier_color};font-size:0.9rem;font-weight:700;">{d.sas_result.tier.value}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('---')
        
        # =================================================================
        # MÉTRICAS PRINCIPAIS
        # =================================================================
        op = d.dados_operacionais
        fi = d.dados_financeiros
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🌾 Área Total", f"{safe_float(op.hectares_total, 0):,.0f} ha")
        m2.metric("💰 Capital Social", f"R$ {safe_float(fi.capital_social_estimado, 0)/1e6:.1f}M" if fi.capital_social_estimado else "N/D")
        m3.metric("🏭 Fazendas", safe_int(op.numero_fazendas, 0) or "N/D")
        m4.metric("👥 Funcionários", f"~{safe_int(fi.funcionarios_estimados, 0)}" if fi.funcionarios_estimados else "N/D")
        m5.metric("📈 Faturamento", f"R$ {safe_float(fi.faturamento_estimado, 0)/1e6:.0f}M" if fi.faturamento_estimado else "N/D")
        
        # =================================================================
        # 1. DADOS CADASTRAIS (CNPJ)
        # =================================================================
        if d.dados_cnpj:
            st.markdown('### 📋 DADOS CADASTRAIS')
            dc = d.dados_cnpj
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="info-card">
                    <strong>Razão Social:</strong> {dc.razao_social}<br>
                    <strong>CNPJ:</strong> {formatar_cnpj(dc.cnpj) if dc.cnpj else 'N/D'}<br>
                    <strong>Situação:</strong> {dc.situacao_cadastral}<br>
                    <strong>Abertura:</strong> {dc.data_abertura}<br>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="info-card">
                    <strong>Natureza Jurídica:</strong> {dc.natureza_juridica}<br>
                    <strong>Porte:</strong> {dc.porte}<br>
                    <strong>CNAE Principal:</strong> {dc.cnae_principal} - {dc.cnae_descricao}<br>
                    <strong>Localização:</strong> {dc.municipio}/{dc.uf}<br>
                </div>
                """, unsafe_allow_html=True)
            
            # QSA - Quadro Societário
            if dc.qsa:
                st.markdown("#### 👥 Quadro Societário (QSA)")
                qsa_data = []
                for socio in dc.qsa[:10]:  # Top 10
                    qsa_data.append({
                        "Nome": socio.get('nome', 'N/D'),
                        "Qualificação": socio.get('qualificacao', 'N/D'),
                        "Data Entrada": socio.get('data_entrada', 'N/D')
                    })
                if qsa_data:
                    st.dataframe(pd.DataFrame(qsa_data), use_container_width=True, hide_index=True)
        
        # =================================================================
        # 2. DADOS OPERACIONAIS DETALHADOS
        # =================================================================
        st.markdown('### 🚜 DADOS OPERACIONAIS')
        
        col_op1, col_op2 = st.columns(2)
        
        with col_op1:
            st.markdown(f"""
            <div class="success-card">
                <strong>🌾 Culturas:</strong> {_sj(op.culturas) or 'Não identificado'}<br>
                <strong>🗺️ Regiões de Atuação:</strong> {_sj(op.regioes_atuacao) or 'Não identificado'}<br>
                <strong>💧 Área Irrigada:</strong> {safe_int(op.area_irrigada_ha, 0):,} ha<br>
                <strong>🌲 Área Florestal:</strong> {safe_int(op.area_florestal_ha, 0):,} ha
            </div>
            """, unsafe_allow_html=True)
        
        with col_op2:
            st.markdown(f"""
            <div class="success-card">
                <strong>🐂 Cabeças de Gado:</strong> {safe_int(op.cabecas_gado, 0):,}<br>
                <strong>🐔 Cabeças de Aves:</strong> {safe_int(op.cabecas_aves, 0):,}<br>
                <strong>🐷 Cabeças de Suínos:</strong> {safe_int(op.cabecas_suinos, 0):,}<br>
                <strong>💡 Tecnologias:</strong> {_sj(op.tecnologias_identificadas, 5) or 'Não identificado'}
            </div>
            """, unsafe_allow_html=True)
        
        # Verticalização
        if hasattr(op, 'verticalizacao'):
            ativos = op.verticalizacao.listar_ativos()
            if ativos:
                st.markdown("#### ⚙️ Verticalização")
                st.write(", ".join(ativos))
        
        # =================================================================
        # 3. DADOS FINANCEIROS DETALHADOS
        # =================================================================
        st.markdown('### 💰 DADOS FINANCEIROS')
        
        col_fin1, col_fin2 = st.columns(2)
        
        with col_fin1:
            st.markdown("#### 📊 Indicadores")
            st.markdown(f"""
            <div class="info-card">
                <strong>Capital Social:</strong> R$ {safe_float(fi.capital_social_estimado, 0):,.2f}<br>
                <strong>Faturamento Estimado:</strong> R$ {safe_float(fi.faturamento_estimado, 0):,.2f}<br>
                <strong>Funcionários:</strong> ~{safe_int(fi.funcionarios_estimados, 0):,}<br>
                <strong>Governança Corporativa:</strong> {'Sim' if fi.governanca_corporativa else 'Não'}
            </div>
            """, unsafe_allow_html=True)
        
        with col_fin2:
            st.markdown("#### 🤝 Parceiros Financeiros")
            if fi.parceiros_financeiros:
                st.write(", ".join(fi.parceiros_financeiros))
            else:
                st.write("Não identificados")
            
            if fi.auditorias:
                st.markdown("**📋 Auditorias:**")
                st.write(", ".join(fi.auditorias))
        
        # Movimentações Financeiras
        if fi.movimentos_financeiros:
            st.markdown("#### 💸 Movimentações Financeiras Recentes")
            for mov in fi.movimentos_financeiros[:10]:
                st.markdown(f"- {mov}")
        
        # FIAgros e CRAs
        if fi.fiagros_relacionados or fi.cras_emitidos:
            col_fiagro, col_cra = st.columns(2)
            
            with col_fiagro:
                if fi.fiagros_relacionados:
                    st.markdown("#### 📊 FIAgros Relacionados")
                    for fiagro in fi.fiagros_relacionados:
                        st.markdown(f"- {fiagro}")
            
            with col_cra:
                if fi.cras_emitidos:
                    st.markdown("#### 📜 CRAs Emitidos")
                    for cra in fi.cras_emitidos:
                        st.markdown(f"- {cra}")
        
        # =================================================================
        # 4. CADEIA DE VALOR
        # =================================================================
        st.markdown('### 🔗 CADEIA DE VALOR')
        
        cv = d.cadeia_valor
        col_cv1, col_cv2 = st.columns(2)
        
        with col_cv1:
            st.markdown(f"""
            <div class="info-card">
                <strong>Posição na Cadeia:</strong> {cv.posicao_cadeia or 'N/D'}<br>
                <strong>Integração Vertical:</strong> {cv.integracao_vertical_nivel or 'N/D'}<br>
                <strong>Exporta:</strong> {'Sim' if cv.exporta else 'Não'}<br>
                <strong>Canais de Venda:</strong> {_sj(cv.canais_venda) or 'N/D'}
            </div>
            """, unsafe_allow_html=True)
            
            if cv.certificacoes:
                st.markdown("**🏅 Certificações:**")
                st.write(", ".join(cv.certificacoes))
        
        with col_cv2:
            if cv.clientes_principais:
                st.markdown("**🎯 Clientes Principais:**")
                for cliente in cv.clientes_principais[:5]:
                    st.markdown(f"- {cliente}")
            
            if cv.fornecedores_principais:
                st.markdown("**📦 Fornecedores Principais:**")
                for forn in cv.fornecedores_principais[:5]:
                    st.markdown(f"- {forn}")
        
        if cv.mercados_exportacao:
            st.markdown("**🌍 Mercados de Exportação:**")
            st.write(", ".join(cv.mercados_exportacao))
        
        # =================================================================
        # 5. GRUPO ECONÔMICO
        # =================================================================
        st.markdown('### 🏛️ GRUPO ECONÔMICO')
        
        ge = d.grupo_economico
        col_ge1, col_ge2 = st.columns(2)
        
        with col_ge1:
            st.markdown(f"""
            <div class="info-card">
                <strong>CNPJ Matriz:</strong> {formatar_cnpj(ge.cnpj_matriz) if ge.cnpj_matriz else 'N/D'}<br>
                <strong>Total de Empresas:</strong> {safe_int(ge.total_empresas, 0)}<br>
                <strong>Filiais:</strong> {len(ge.cnpjs_filiais)}<br>
                <strong>Coligadas:</strong> {len(ge.cnpjs_coligadas)}
            </div>
            """, unsafe_allow_html=True)
            
            if ge.holding_controladora:
                st.markdown(f"**🏛️ Holding Controladora:** {ge.holding_controladora}")
        
        with col_ge2:
            if ge.controladores:
                st.markdown("**👔 Controladores:**")
                for ctrl in ge.controladores:
                    st.markdown(f"- {ctrl}")
        
        # =================================================================
        # 6. DECISORES E PROFILER
        # =================================================================
        st.markdown('### 👥 MAPA DE DECISORES')
        
        if d.decisores and isinstance(d.decisores, dict):
            dec_list = d.decisores.get('decisores', [])
            estrutura = d.decisores.get('estrutura_decisao', 'N/D')
            
            st.markdown(f"**Estrutura de Decisão:** {estrutura}")
            
            if dec_list:
                decisores_data = []
                for dec in dec_list:
                    decisores_data.append({
                        "Nome": dec.get('nome', 'N/D'),
                        "Cargo": dec.get('cargo', 'N/D'),
                        "LinkedIn": dec.get('linkedin', 'N/D'),
                        "Email": dec.get('email', 'N/D'),
                        "Perfil": dec.get('perfil_decisorio', 'N/D')
                    })
                
                st.dataframe(pd.DataFrame(decisores_data), use_container_width=True, hide_index=True)
        
        # =================================================================
        # 7. TECH STACK
        # =================================================================
        st.markdown('### 💻 TECH STACK')
        
        if d.tech_stack and isinstance(d.tech_stack, dict):
            ts = d.tech_stack
            
            col_tech1, col_tech2 = st.columns(2)
            
            with col_tech1:
                erp_info = ts.get('erp_principal', {})
                st.markdown(f"""
                <div class="info-card">
                    <strong>📦 ERP Principal:</strong> {erp_info.get('sistema', 'N/D')}<br>
                    <strong>🏭 Fornecedor:</strong> {erp_info.get('fornecedor', 'N/D')}<br>
                    <strong>🔍 Status:</strong> {erp_info.get('status', 'N/D')}<br>
                    <strong>📈 Maturidade TI:</strong> {ts.get('nivel_maturidade_ti', 'N/D')}
                </div>
                """, unsafe_allow_html=True)
            
            with col_tech2:
                outros = ts.get('outros_sistemas', [])
                if outros:
                    st.markdown("**🛠️ Outros Sistemas:**")
                    for sist in outros[:5]:
                        st.markdown(f"- **{sist.get('tipo', 'N/D')}:** {sist.get('sistema', 'N/D')}")
            
            vagas = ts.get('vagas_ti_abertas', [])
            if vagas:
                st.markdown("#### 💼 Vagas de TI Abertas")
                for vaga in vagas[:5]:
                    st.markdown(f"- **{vaga.get('titulo', 'N/D')}** | Sistemas: {_sj(vaga.get('sistemas_mencionados', []))}")
        
        # =================================================================
        # 8. INTELIGÊNCIA DE MERCADO
        # =================================================================
        st.markdown('### 📡 INTELIGÊNCIA DE MERCADO')
        
        im = d.intel_mercado
        
        # Notícias
        if im.noticias_recentes:
            st.markdown("#### 📰 Notícias Recentes")
            for noticia in im.noticias_recentes[:5]:
                titulo = noticia.get('titulo', 'N/D')
                data = noticia.get('data', 'N/D')
                fonte = noticia.get('fonte', 'N/D')
                st.markdown(f"- **{titulo}** ({data}) - _{fonte}_")
        
        # Sinais de Compra
        col_sinais, col_riscos = st.columns(2)
        
        with col_sinais:
            if im.sinais_compra:
                st.markdown("#### 🟢 Sinais de Compra")
                for sinal in im.sinais_compra:
                    st.markdown(f"- {sinal}")
            
            if im.oportunidades:
                st.markdown("#### 💡 Oportunidades")
                for op in im.oportunidades:
                    st.markdown(f"- {op}")
        
        with col_riscos:
            if im.riscos:
                st.markdown("#### ⚠️ Riscos")
                for risco in im.riscos:
                    st.markdown(f"- {risco}")
            
            if im.dores_identificadas:
                st.markdown("#### 💔 Dores Identificadas")
                for dor in im.dores_identificadas:
                    st.markdown(f"- {dor}")
        
        if im.concorrentes:
            st.markdown("**⚔️ Concorrentes:**")
            st.write(", ".join(im.concorrentes))
        
        # =================================================================
        # 9. ANÁLISE ESTRATÉGICA
        # =================================================================
        st.markdown('### 🧠 ANÁLISE ESTRATÉGICA')
        
        for secao in d.secoes_analise:
            with st.expander(f"{secao.icone} {secao.titulo}", expanded=False):
                st.markdown(secao.conteudo)
        
        # =================================================================
        # 10. BREAKDOWN DO SCORE
        # =================================================================
        st.markdown('### 📊 BREAKDOWN DO SCORE SAS')
        
        breakdown = d.sas_result.breakdown
        col_bd1, col_bd2, col_bd3, col_bd4 = st.columns(4)
        
        col_bd1.metric("💪 Músculo", f"{breakdown.musculo}/300")
        col_bd2.metric("⚙️ Complexidade", f"{breakdown.complexidade}/250")
        col_bd3.metric("👥 Gente", f"{breakdown.gente}/250")
        col_bd4.metric("⏱️ Momento", f"{breakdown.momento}/200")
        
        if d.sas_result.justificativas:
            st.markdown("#### Justificativas")
            for just in d.sas_result.justificativas:
                st.markdown(f"- {just}")
        
        # =================================================================
        # DOWNLOAD
        # =================================================================
        st.markdown('---')
        csv_data = gerar_csv_report(d)
        st.download_button(
            "📥 BAIXAR DOSSIÊ COMPLETO (CSV)",
            csv_data,
            f"dossie_completo_{nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )

with tab_raw:
    st.markdown('### 📦 RAW DATA (JSON)')
    if st.session_state.dossie:
        st.json(json.loads(json.dumps(st.session_state.dossie, default=lambda o: o.__dict__)))
    else:
        st.info("📍 Execute uma missão para visualizar dados brutos")
