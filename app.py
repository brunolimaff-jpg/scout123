"""app.py — BANDEIRANTE DIGITAL INTERFACE COM RESUMO DE ACHADOS"""

import streamlit as st
import asyncio
import json
from datetime import datetime
import time

from services.gemini_service import GeminiService
from services.orchestrator import BandeiranteOrchestrator
from services.dossie_generator import DossieGenerator

st.set_page_config(
    page_title="Bandeirante Digital",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 BANDEIRANTE DIGITAL")
st.markdown("**MODO DEUS COMPLETO** - Inteligência de Mercado Ultra-Avançada")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ CONFIGURAÇÕES")
    
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        help="Sua chave de API do Google Gemini"
    )
    
    st.markdown("---")
    st.info("""
    **Versão:** 3.0 MODO DEUS  
    **Desenvolvido por:** Bruno Lima  
    **Empresa:** Senior Sistemas  
    **Localidade:** Cuiabá, MT
    """)

# Função para executar com status visual
async def executar_com_status_visual(orch, empresa_nome, empresa_cnpj, empresa_uf):
    """Executa investigação com status visual e resumo de achados."""
    
    start_time = time.time()
    results = {
        "metadata": {
            "empresa": empresa_nome,
            "cnpj": empresa_cnpj,
            "uf": empresa_uf,
            "timestamp_inicio": datetime.now().isoformat(),
            "versao": "3.0-MODO-DEUS"
        },
        "fases": {}
    }
    
    # FASE -1: REPUTATION
    with st.status("🔍 **FASE -1:** Shadow Reputation", expanded=True) as status:
        st.write("🔍 Buscando registros públicos...")
        st.write("📊 Analisando histórico...")
        try:
            reputation = await orch.reputation_layer.checagem_completa(empresa_nome, empresa_cnpj)
            results["fases"]["fase_-1_reputation"] = reputation
            
            # RESUMO DE ACHADOS
            st.write("")
            st.write("✅ **Reputation verificada!**")
            st.write("📊 **Principais achados:**")
            flag = reputation.get("flag_risco", "N/D")
            processos = reputation.get("processos_judiciais", {}).get("total", 0)
            st.write(f"  • Flag de risco: **{flag}**")
            st.write(f"  • Processos judiciais: **{processos}**")
            
            status.update(label="✅ FASE -1 COMPLETA", state="complete")
        except Exception as e:
            st.write(f"⚠️ Erro: {str(e)}")
            results["fases"]["fase_-1_reputation"] = {"flag_risco": "ERRO"}
            status.update(label="⚠️ FASE -1 com erro", state="error")
    
    # FASE 1: INCENTIVOS
    with st.status("💰 **FASE 1:** Incentivos Fiscais", expanded=True) as status:
        st.write("🔍 Mapeando incentivos estaduais...")
        st.write("📊 Verificando sanções e multas...")
        try:
            incentivos = await orch.tax_layer.mapeamento_completo(empresa_nome, empresa_cnpj, empresa_uf)
            results["fases"]["fase_1_incentivos"] = incentivos
            
            # RESUMO DE ACHADOS
            st.write("")
            total_inc = incentivos.get("incentivos_estaduais", {}).get("total_incentivos", 0)
            valor_anual = incentivos.get("incentivos_estaduais", {}).get("valor_beneficio_anual_estimado", "N/D")
            multas = incentivos.get("sancoes_multas", {}).get("total_multas_quantidade", 0)
            
            st.write("✅ **Incentivos mapeados!**")
            st.write("📊 **Principais achados:**")
            st.write(f"  • Incentivos fiscais: **{total_inc}**")
            st.write(f"  • Benefício anual estimado: **{valor_anual}**")
            st.write(f"  • Multas fiscais: **{multas}**")
            
            status.update(label="✅ FASE 1 COMPLETA", state="complete")
        except Exception as e:
            st.write(f"⚠️ Erro: {str(e)}")
            results["fases"]["fase_1_incentivos"] = {"incentivos_estaduais": {"total_incentivos": 0}}
            status.update(label="⚠️ FASE 1 com erro", state="error")
    
    # FASE 2: TERRITORIAL
    with st.status("🗺️ **FASE 2:** Inteligência Territorial", expanded=True) as status:
        st.write("🔍 Buscando dados fundiários no INCRA...")
        st.write("🌳 Verificando licenças ambientais...")
        st.write("📍 Analisando adjacências e logística...")
        try:
            territorial = await orch.territorial_layer.mapeamento_territorial_completo(empresa_nome, empresa_cnpj)
            results["fases"]["fase_2_territorial"] = territorial
            
            # RESUMO DE ACHADOS
            st.write("")
            fundiario = territorial.get("dados_fundiarios", {})
            area = fundiario.get("area_total_ha", 0)
            total_imoveis = fundiario.get("total_imoveis", 0)
            estados = fundiario.get("estados_presenca", [])
            licencas_total = territorial.get("licencas_ambientais", {}).get("total_licencas", 0)
            licencas_recentes = territorial.get("licencas_ambientais", {}).get("licencas_recentes_6m", 0)
            
            st.write("✅ **Dados territoriais obtidos!**")
            st.write("📊 **Principais achados:**")
            st.write(f"  • Área total: **{area:,.0f} hectares**")
            st.write(f"  • Total de imóveis: **{total_imoveis}**")
            st.write(f"  • Estados presença: **{', '.join(estados) if estados else 'N/D'}**")
            st.write(f"  • Licenças ambientais: **{licencas_total}** ({licencas_recentes} recentes)")
            
            status.update(label="✅ FASE 2 COMPLETA", state="complete")
        except Exception as e:
            st.write(f"⚠️ Erro: {str(e)}")
            results["fases"]["fase_2_territorial"] = {"dados_fundiarios": {"area_total_ha": 0}}
            status.update(label="⚠️ FASE 2 com erro", state="error")
    
    # FASE 3: LOGÍSTICA
    with st.status("🚛 **FASE 3:** Logística & Supply Chain", expanded=True) as status:
        st.write("🔍 Mapeando armazenagem...")
        st.write("🚚 Verificando frota e RNTRC...")
        try:
            logistica = await orch.logistics_layer.mapeamento_logistico_completo(empresa_nome, empresa_cnpj)
            results["fases"]["fase_3_logistica"] = logistica
            
            # RESUMO DE ACHADOS
            st.write("")
            armazenagem = logistica.get("armazenagem", {})
            capacidade = armazenagem.get("capacidade_total_toneladas", 0)
            unidades = armazenagem.get("total_unidades", 0)
            frota = logistica.get("frota_logistica", {})
            rntrc_ativo = frota.get("rntrc", {}).get("ativo", False)
            veiculos = frota.get("rntrc", {}).get("quantidade_veiculos", 0)
            
            st.write("✅ **Logística analisada!**")
            st.write("📊 **Principais achados:**")
            st.write(f"  • Capacidade armazenagem: **{capacidade:,.0f} toneladas**")
            st.write(f"  • Unidades de armazenagem: **{unidades}**")
            st.write(f"  • RNTRC: **{'Ativo' if rntrc_ativo else 'Inativo'}**")
            st.write(f"  • Veículos cadastrados: **{veiculos}**")
            
            status.update(label="✅ FASE 3 COMPLETA", state="complete")
        except Exception as e:
            st.write(f"⚠️ Erro: {str(e)}")
            results["fases"]["fase_3_logistica"] = {"armazenagem": {"capacidade_total_toneladas": 0}}
            status.update(label="⚠️ FASE 3 com erro", state="error")
    
    # FASE 4: SOCIETÁRIO
    with st.status("🏢 **FASE 4:** Estrutura Societária", expanded=True) as status:
        st.write("🔍 Mapeando grupo econômico...")
        st.write("📊 Analisando capital social...")
        try:
            societario = await orch.corporate_layer.mapeamento_societario_completo(empresa_nome, empresa_cnpj, [])
            results["fases"]["fase_4_societario"] = societario
            
            # RESUMO DE ACHADOS
            st.write("")
            estrutura = societario.get("estrutura", {})
            grupo = estrutura.get("grupo_economico", {})
            total_empresas = grupo.get("total_empresas_grupo", 0)
            holding = grupo.get("holding_controladora", "N/D")
            capital = grupo.get("capital_social_total_grupo", "N/D")
            
            st.write("✅ **Estrutura mapeada!**")
            st.write("📊 **Principais achados:**")
            st.write(f"  • Holding controladora: **{holding}**")
            st.write(f"  • Total de empresas: **{total_empresas}**")
            st.write(f"  • Capital social total: **{capital}**")
            
            status.update(label="✅ FASE 4 COMPLETA", state="complete")
        except Exception as e:
            st.write(f"⚠️ Erro: {str(e)}")
            results["fases"]["fase_4_societario"] = {"estrutura": {"grupo_economico": {}}}
            status.update(label="⚠️ FASE 4 com erro", state="error")
    
    # FASE 5: EXECUTIVOS
    with st.status("👔 **FASE 5:** Profiling de Executivos", expanded=True) as status:
        st.write("🔍 Perfilando liderança...")
        st.write("💼 Buscando perfis LinkedIn...")
        try:
            executivos = await orch.executive_profiler.profiling_completo(empresa_nome)
            results["fases"]["fase_5_executivos"] = executivos
            
            # RESUMO DE ACHADOS
            st.write("")
            hierarquia = executivos.get("hierarquia", {})
            tem_ti = hierarquia.get("tem_area_ti", False)
            tipo_decisao = hierarquia.get("tipo_decisao", "N/D")
            vagas_ti = len(hierarquia.get("vagas_ti_abertas", []))
            
            st.write("✅ **Executivos mapeados!**")
            st.write("📊 **Principais achados:**")
            st.write(f"  • Área de TI: **{'Sim' if tem_ti else 'Não'}**")
            st.write(f"  • Tipo de decisão: **{tipo_decisao}**")
            st.write(f"  • Vagas TI abertas: **{vagas_ti}**")
            
            status.update(label="✅ FASE 5 COMPLETA", state="complete")
        except Exception as e:
            st.write(f"⚠️ Erro: {str(e)}")
            results["fases"]["fase_5_executivos"] = {"hierarquia": {}}
            status.update(label="⚠️ FASE 5 com erro", state="error")
    
    # FASE 6: TRIGGERS
    with st.status("⏰ **FASE 6:** Identificando Triggers", expanded=False) as status:
        st.write("🔍 Analisando contexto sazonal...")
        triggers = await orch._identificar_triggers(results)
        results["fases"]["fase_6_triggers"] = triggers
        
        total_triggers = triggers.get("total_triggers", 0)
        urgencia = triggers.get("urgencia_geral", "N/D")
        st.write(f"✅ **{total_triggers} trigger(s) identificado(s)** | Urgência: **{urgencia}**")
        status.update(label="✅ FASE 6 COMPLETA", state="complete")
    
    # FASE 7: PSICOLOGIA
    with st.status("🧠 **FASE 7:** Mapeamento Psicológico", expanded=False) as status:
        st.write("🔍 Definindo gatilhos e abordagem...")
        psicologia = await orch._mapear_psicologia(results)
        results["fases"]["fase_7_psicologia"] = psicologia
        
        gatilho = psicologia.get("gatilho_psicologico", "N/D")
        canal = psicologia.get("canal_preferido", "N/D")
        st.write(f"✅ **Gatilho:** {gatilho} | **Canal:** {canal}")
        status.update(label="✅ FASE 7 COMPLETA", state="complete")
    
    # FASE 10: MATRIZ
    with st.status("🎯 **FASE 10:** Calculando Matriz de Priorização", expanded=False) as status:
        st.write("📊 Calculando score final...")
        matriz = orch._calcular_matriz_priorizacao(results)
        results["matriz_priorizacao"] = matriz
        results["recomendacoes"] = orch._gerar_recomendacoes(results)
        
        score = matriz.get('score_final', 0)
        status_final = matriz.get('status', 'N/D')
        st.write(f"✅ **Score: {score}/100** | **Status: {status_final}**")
        status.update(label="✅ FASE 10 COMPLETA", state="complete")
    
    # Finaliza
    end_time = time.time()
    duracao = end_time - start_time
    results["metadata"]["timestamp_fim"] = datetime.now().isoformat()
    results["metadata"]["duracao_segundos"] = duracao
    
    return results, duracao

# Input
st.header("🔍 Nova Investigação")

empresa_nome = st.text_input(
    "📋 Nome da Empresa *",
    placeholder="Ex: GRUPO SCHEFFER"
)

col1, col2 = st.columns(2)
with col1:
    empresa_cnpj = st.text_input("🔢 CNPJ (opcional)")
with col2:
    empresa_uf = st.selectbox("🌎 Estado", ["", "MT", "MS", "GO", "BA", "TO"])

if st.button("🔥 EXECUTAR MODO DEUS", type="primary", use_container_width=True):
    if not empresa_nome:
        st.error("❌ Digite o nome da empresa!")
    elif not api_key:
        st.error("❌ Configure a API Key na sidebar!")
    else:
        try:
            st.markdown("---")
            st.markdown("## 🔄 EXECUTANDO INVESTIGAÇÃO...")
            
            gemini = GeminiService(api_key=api_key)
            orch = BandeiranteOrchestrator(gemini)
            
            # Executa com status visual
            results, duracao = asyncio.run(
                executar_com_status_visual(
                    orch,
                    empresa_nome,
                    empresa_cnpj,
                    empresa_uf or "MT"
                )
            )
            
            st.markdown("---")
            st.success(f"✅ **INVESTIGAÇÃO COMPLETA EM {duracao:.1f} SEGUNDOS!**")
            st.balloons()
            
            st.session_state["results"] = results
            st.session_state["empresa"] = empresa_nome
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            st.exception(e)

st.markdown("---")

# Resultados
if "results" in st.session_state:
    results = st.session_state["results"]
    
    st.markdown("## 📊 RESULTADOS DA INVESTIGAÇÃO")
    
    matriz = results.get("matriz_priorizacao", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("SCORE", f"{matriz.get('score_final', 0)}/100")
    
    with col2:
        st.metric("STATUS", matriz.get('status', 'N/D'))
    
    with col3:
        area = matriz.get('area_total_ha', 0)
        st.metric("ÁREA", f"{area:,.0f} ha")
    
    with col4:
        st.metric("CLASSIFICAÇÃO", matriz.get('classificacao', 'N/D')[:15])
    
    st.markdown("---")
    
    # Recomendações
    rec = results.get("recomendacoes", {})
    
    st.markdown("### 🚀 RECOMENDAÇÕES DE AÇÃO")
    st.markdown(f"**{rec.get('acao_recomendada', 'N/D')}**")
    
    st.markdown("**Próximos Passos:**")
    for passo in rec.get("proximos_passos", []):
        st.markdown(f"- {passo}")
    
    st.markdown("---")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 GERAR DOSSIÊ COMPLETO", use_container_width=True):
            with st.spinner("📝 Gerando dossiê..."):
                gen = DossieGenerator()
                dossie = gen.gerar_dossie_completo(results)
                st.session_state["dossie"] = dossie
                st.success("✅ Dossiê gerado!")
    
    with col2:
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 Download JSON",
            data=json_str,
            file_name=f"investigacao_{st.session_state['empresa']}_{datetime.now():%Y%m%d}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        if "dossie" in st.session_state:
            st.download_button(
                label="📄 Download Dossiê MD",
                data=st.session_state["dossie"],
                file_name=f"dossie_{st.session_state['empresa']}_{datetime.now():%Y%m%d}.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    # Exibir dossiê
    if "dossie" in st.session_state:
        st.markdown("---")
        st.markdown("### 📄 DOSSIÊ COMPLETO")
        st.markdown(st.session_state["dossie"])

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <strong>🎯 Bandeirante Digital - MODO DEUS COMPLETO</strong><br>
    Desenvolvido por Bruno Lima | Senior Sistemas | Cuiabá, MT<br>
    © 2026 - Sistema de Inteligência de Mercado Ultra-Avançada
</div>
""", unsafe_allow_html=True)
