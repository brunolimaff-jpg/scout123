"""app.py — BANDEIRANTE DIGITAL INTERFACE COM STATUS EM TEMPO REAL"""

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
        # Container para status em tempo real
        status_container = st.container()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with status_container:
            st.markdown("### 🔄 EXECUTANDO INVESTIGAÇÃO...")
            
            # Placeholder para logs de cada fase
            fase_logs = st.empty()
            
        try:
            gemini = GeminiService(api_key=api_key)
            orch = BandeiranteOrchestrator(gemini)
            
            # Inicia tempo
            start_time = time.time()
            
            # FASE -1: REPUTATION
            status_text.markdown("⏳ **FASE -1:** Shadow Reputation...")
            progress_bar.progress(10)
            fase_logs.markdown("""
            - ✅ Iniciando checagem de reputação
            - 🔍 Buscando registros públicos
            - 📊 Analisando histórico
            """)
            
            results = {"metadata": {"empresa": empresa_nome, "cnpj": empresa_cnpj, "uf": empresa_uf or "MT", "timestamp_inicio": datetime.now().isoformat(), "versao": "3.0-MODO-DEUS"}, "fases": {}}
            
            # Simula execução com feedback
            try:
                # FASE -1
                status_text.markdown("⏳ **FASE -1:** Shadow Reputation... (30s)")
                progress_bar.progress(10)
                reputation = await asyncio.wait_for(
                    orch.reputation_layer.checagem_completa(empresa_nome, empresa_cnpj),
                    timeout=30.0
                )
                results["fases"]["fase_-1_reputation"] = reputation
                fase_logs.markdown("- ✅ **FASE -1 COMPLETA** - Reputation verificada")
                
                # FASE 1
                status_text.markdown("⏳ **FASE 1:** Incentivos Fiscais... (30s)")
                progress_bar.progress(25)
                incentivos = await asyncio.wait_for(
                    orch.tax_layer.mapeamento_completo(empresa_nome, empresa_cnpj, empresa_uf or "MT"),
                    timeout=30.0
                )
                results["fases"]["fase_1_incentivos"] = incentivos
                fase_logs.markdown("- ✅ **FASE 1 COMPLETA** - Incentivos mapeados")
                
                # FASE 2
                status_text.markdown("⏳ **FASE 2:** Inteligência Territorial... (30s)")
                progress_bar.progress(40)
                territorial = await asyncio.wait_for(
                    orch.territorial_layer.mapeamento_territorial_completo(empresa_nome, empresa_cnpj),
                    timeout=30.0
                )
                results["fases"]["fase_2_territorial"] = territorial
                fase_logs.markdown("- ✅ **FASE 2 COMPLETA** - Dados territoriais obtidos")
                
                # FASE 3
                status_text.markdown("⏳ **FASE 3:** Logística & Supply Chain... (30s)")
                progress_bar.progress(55)
                logistica = await asyncio.wait_for(
                    orch.logistics_layer.mapeamento_logistico_completo(empresa_nome, empresa_cnpj),
                    timeout=30.0
                )
                results["fases"]["fase_3_logistica"] = logistica
                fase_logs.markdown("- ✅ **FASE 3 COMPLETA** - Logística analisada")
                
                # FASE 4
                status_text.markdown("⏳ **FASE 4:** Estrutura Societária... (30s)")
                progress_bar.progress(70)
                societario = await asyncio.wait_for(
                    orch.corporate_layer.mapeamento_societario_completo(empresa_nome, empresa_cnpj, []),
                    timeout=30.0
                )
                results["fases"]["fase_4_societario"] = societario
                fase_logs.markdown("- ✅ **FASE 4 COMPLETA** - Estrutura societária mapeada")
                
                # FASE 5
                status_text.markdown("⏳ **FASE 5:** Profiling de Executivos... (30s)")
                progress_bar.progress(85)
                executivos = await asyncio.wait_for(
                    orch.executive_profiler.profiling_completo(empresa_nome),
                    timeout=30.0
                )
                results["fases"]["fase_5_executivos"] = executivos
                fase_logs.markdown("- ✅ **FASE 5 COMPLETA** - Executivos perfilados")
                
            except asyncio.TimeoutError as te:
                st.warning(f"⚠️ Timeout na fase: {str(te)}. Continuando com dados parciais...")
            
            # FASE 6: Triggers (local, sem API)
            status_text.markdown("⏳ **FASE 6:** Identificando Triggers...")
            progress_bar.progress(90)
            triggers = await orch._identificar_triggers(results)
            results["fases"]["fase_6_triggers"] = triggers
            fase_logs.markdown("- ✅ **FASE 6 COMPLETA** - Triggers identificados")
            
            # FASE 7: Psicologia (local, sem API)
            status_text.markdown("⏳ **FASE 7:** Mapeamento Psicológico...")
            progress_bar.progress(95)
            psicologia = await orch._mapear_psicologia(results)
            results["fases"]["fase_7_psicologia"] = psicologia
            fase_logs.markdown("- ✅ **FASE 7 COMPLETA** - Perfil psicológico criado")
            
            # FASE 10: Matriz (local, sem API)
            status_text.markdown("⏳ **FASE 10:** Calculando Matriz de Priorização...")
            progress_bar.progress(98)
            matriz = orch._calcular_matriz_priorizacao(results)
            results["matriz_priorizacao"] = matriz
            results["recomendacoes"] = orch._gerar_recomendacoes(results)
            fase_logs.markdown("- ✅ **FASE 10 COMPLETA** - Matriz calculada")
            
            # Finaliza
            end_time = time.time()
            duracao = end_time - start_time
            results["metadata"]["timestamp_fim"] = datetime.now().isoformat()
            results["metadata"]["duracao_segundos"] = duracao
            
            progress_bar.progress(100)
            status_text.markdown(f"✅ **INVESTIGAÇÃO COMPLETA!** ({duracao:.1f}s)")
            
            fase_logs.markdown(f"""
            ---
            ### ✅ TODAS AS FASES CONCLUÍDAS
            
            **Tempo total:** {duracao:.1f} segundos  
            **Score final:** {matriz.get('score_final', 0)}/100  
            **Status:** {matriz.get('status', 'N/D')}
            """)
            
            st.session_state["results"] = results
            st.session_state["empresa"] = empresa_nome
            st.success(f"✅ Investigação completa em {duracao:.1f}s!")
            st.balloons()
            
        except asyncio.TimeoutError:
            st.error("❌ Timeout geral! A investigação demorou mais de 5 minutos.")
            st.info("💡 Dica: Tente novamente ou verifique sua conexão.")
        except Exception as e:
            st.error(f"❌ Erro durante execução: {str(e)}")
            st.exception(e)
            if "results" in locals() and results.get("fases"):
                st.warning("⚠️ Dados parciais foram coletados. Salvando o que foi possível...")
                st.session_state["results"] = results
                st.session_state["empresa"] = empresa_nome

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
