"""app.py — BANDEIRANTE DIGITAL INTERFACE"""

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
        # Container para status
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        try:
            gemini = GeminiService(api_key=api_key)
            orch = BandeiranteOrchestrator(gemini)
            
            start_time = time.time()
            
            # Mostra status inicial
            status_container.info("🔄 Iniciando investigação...")
            progress_bar.progress(5)
            
            # EXECUTA DE VERDADE (SEM TIMEOUT FAKE)
            results = asyncio.run(
                orch.investigacao_completa(
                    empresa=empresa_nome,
                    cnpj=empresa_cnpj,
                    uf=empresa_uf or "MT"
                )
            )
            
            # Finaliza
            end_time = time.time()
            duracao = end_time - start_time
            
            progress_bar.progress(100)
            status_container.success(f"✅ Investigação completa em {duracao:.1f}s!")
            
            st.session_state["results"] = results
            st.session_state["empresa"] = empresa_nome
            st.balloons()
            
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
