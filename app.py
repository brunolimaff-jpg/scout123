"""app.py — BANDEIRANTE DIGITAL v3.0 INTERFACE"""

import streamlit as st
import asyncio
import json
from datetime import datetime

from services.gemini_service import GeminiService
from services.orchestrator_v3 import BandeiranteOrchestratorV3
from services.dossie_generator_v3 import DossieGeneratorV3

st.set_page_config(
    page_title="Bandeirante v3.0",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 BANDEIRANTE DIGITAL V3.0")
st.markdown("**MODO DEUS COMPLETO**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ CONFIG")
    api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    st.info("**v3.0 MODO DEUS**\nBruno Lima\nSenior Sistemas")

# Input
st.header("🔍 Nova Investigação")

empresa_nome = st.text_input("📋 Nome da Empresa *", placeholder="GRUPO SCHEFFER")

col1, col2 = st.columns(2)
with col1:
    empresa_cnpj = st.text_input("🔢 CNPJ (opcional)")
with col2:
    empresa_uf = st.selectbox("🌎 UF", ["", "MT", "MS", "GO"])

if st.button("🔥 EXECUTAR MODO DEUS", type="primary", use_container_width=True):
    if not empresa_nome:
        st.error("❌ Digite o nome da empresa!")
    elif not api_key:
        st.error("❌ Configure a API Key!")
    else:
        with st.spinner("🔄 Executando..."):
            gemini = GeminiService(api_key=api_key)
            orch = BandeiranteOrchestratorV3(gemini)
            
            results = asyncio.run(
                orch.investigacao_completa(
                    empresa=empresa_nome,
                    cnpj=empresa_cnpj,
                    uf=empresa_uf or "MT"
                )
            )
            
            st.session_state["results"] = results
            st.session_state["empresa"] = empresa_nome
            st.success("✅ Completo!")
            st.balloons()

st.markdown("---")

# Resultados
if "results" in st.session_state:
    results = st.session_state["results"]
    
    st.markdown("## 📊 RESULTADOS")
    
    matriz = results.get("matriz_priorizacao", {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("SCORE", f"{matriz.get('score_final', 0)}/100")
    with col2:
        st.metric("STATUS", matriz.get('status', 'N/D'))
    with col3:
        st.metric("ÁREA", f"{matriz.get('area_total_ha', 0):,.0f} ha")
    
    st.markdown("---")
    
    rec = results.get("recomendacoes", {})
    st.markdown("### 🚀 RECOMENDAÇÕES")
    st.markdown(f"**{rec.get('acao_recomendada', 'N/D')}**")
    
    for passo in rec.get("proximos_passos", []):
        st.markdown(f"- {passo}")
    
    st.markdown("---")
    
    # Botões
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 GERAR DOSSIÊ"):
            gen = DossieGeneratorV3()
            dossie = gen.gerar_dossie_completo(results)
            st.session_state["dossie"] = dossie
            st.success("✅ Dossiê gerado!")
    
    with col2:
        json_str = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button(
            "💾 Download JSON",
            json_str,
            f"investigacao_{st.session_state['empresa']}.json",
            "application/json"
        )
    
    if "dossie" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["dossie"])

st.markdown("---")
st.markdown("<div style='text-align:center'>🎯 Bandeirante Digital v3.0 | Bruno Lima</div>", unsafe_allow_html=True)
