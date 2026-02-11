"""
services/dossier_orchestrator.py — VERSÃO ESTÁVEL (CORREÇÃO ERP_KEY)
Corrige o erro de chave 'erp_principal' normalizando os dados antes da chamada do Protocolo Ciro.
"""
import asyncio
import logging
import re
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DossierOrchestrator:
    """
    Orquestrador que encarna o 'Auditor Forense'.
    Gera o 'Protocolo Bruno Lima': Dados Duros + Contradições (Smoking Gun) + Ataque.
    """
    
    def __init__(
        self, 
        gemini_service,
        infrastructure_layer,
        financial_layer,
        intelligence_layer,
        market_estimator
    ):
        self.gemini = gemini_service
        self.infra = infrastructure_layer
        self.financial = financial_layer
        self.intel = intelligence_layer
        self.market = market_estimator

    async def _gerar_relatorio_ciro(self, dados_consolidados: Dict) -> str:
        """
        Gera o texto 'Análise Estratégica' no estilo CIRO.
        """
        logger.info(f"[Orchestrator] Gerando Relatório Protocolo Bruno Lima para: {dados_consolidados['empresa_alvo']}")
        
        # Extração segura para evitar KeyErrors no prompt f-string
        empresa = dados_consolidados.get('empresa_alvo', 'Alvo')
        area = dados_consolidados.get('dados_operacionais', {}).get('area_total', 0)
        faturamento = dados_consolidados.get('dados_financeiros', {}).get('faturamento_estimado', 'N/D')
        infra = str(dados_consolidados.get('dados_operacionais', {}).get('detalhes_industriais', {}))[:500]
        # AQUI ESTAVA O ERRO ANTERIOR -> Agora usa .get() seguro
        erp = dados_consolidados.get('tech_stack', {}).get('erp_principal', 'Não Identificado')
        noticias = str(dados_consolidados.get('auditoria_noticias', []))[:800]
        org = str(dados_consolidados.get('dados_organizacionais', {}))[:800]
        
        prompt = f"""
        ATUE COMO: CIRO, O AUDITOR FORENSE DE VENDAS (Expert em Agronegócio e TI).
        
        DADOS DA VÍTIMA (ALVO):
        - Nome: {empresa}
        - Área: {area} hectares.
        - Faturamento Real/Estimado: {faturamento}
        - Infra Industrial: {infra}
        - ERP Identificado: {erp}
        - Notícias/Escândalos: {noticias}
        - Decisores/Vagas: {org}
        
        SUA MISSÃO: Escrever o "PROTOCOLO BRUNO LIMA" (Relatório de Inteligência).
        
        TOM DE VOZ:
        - Use termos como: "Smoking Gun", "Frankenstein Tecnológico", "Auditoria Forense", "Dívida", "CRA", "Big 4".
        - Seja cético e analítico.
        
        ESTRUTURA OBRIGATÓRIA DA RESPOSTA (Markdown):
        
        # 🕵️‍♂️ DOSSIÊ DE INTELIGÊNCIA: {empresa}
        **STATUS:** [ALTO VALOR ESTRATÉGICO / RISCO DE CHURN / BIG FISH]
        **RESUMO DO ESPIÃO:** [Resumo de impacto].
        
        ## 1. 🧬 RAIO-X CORPORATIVO (HARD DATA)
        * **Faturamento:** {faturamento} (Fonte: Auditoria Digital).
        * **Porte Real:** {area} ha.
        
        ## 2. 🚜 INFRAESTRUTURA (ATIVOS OCULTOS)
        * **Fábricas a Céu Aberto:** [Liste Algodoeiras, UBS, Armazéns encontrados na infra].
        
        ## 3. 💻 A "SMOKING GUN" (TECNOLOGIA)
        * **O Cenário:** Identificamos ERP [{erp}].
        * **A Contradição:** [Analise se o ERP é compatível com o porte. Se for Senior, elogie mas aponte brechas de módulos. Se for Totvs/Outro, ataque].
        
        ## 4. 🎯 OPPORTUNITY MAP (PLANO DE GUERRA)
        | Vertical | O Fato (Evidência) | O Argumento de Venda (Pitch Matador) |
        |---|---|---|
        | Backoffice | [ERP Atual] | [Argumento] |
        | Agro | [Gestão Campo] | [Argumento] |
        
        ## 📝 SCRIPT PARA O EXECUTIVO (Copie e Cole)
        > [Mensagem de WhatsApp curta e agressiva para o Diretor].
        """
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=2, use_search=False, temperature=0.4)
            return response
        except Exception as e:
            logger.error(f"Erro ao gerar relatório Ciro: {e}")
            return "Relatório Forense indisponível. Dados insuficientes."

    async def executar_dosier_completo(self, razao_social: str, cnpj: str = "", callback=None) -> Dict:
        """Pipeline Auditoria Total com Saída 'Ciro'."""
        from services.cnpj_service import consultar_cnpj
        
        if callback: callback(f"🕵️‍♂️ Iniciando Protocolo Bruno Lima: {razao_social}...")
        
        # 1. Identificação Corporativa
        cnpj_info = {}
        cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ""
        if cnpj_limpo and len(cnpj_limpo) == 14:
            c_data = consultar_cnpj(cnpj_limpo)
            if c_data:
                cnpj_info = {"cnpj": c_data.cnpj, "capital_social": c_data.capital_social, "nome": c_data.razao_social}
        
        # 2. Execução Paralela
        if callback: callback("📡 Coletando evidências forenses (Balanços, Vagas, Terras)...")
        
        t_infra = self.infra.buscar_sigef_car(razao_social, [])
        t_fin = self.financial.mineracao_cra_debentures(razao_social, cnpj_info.get('cnpj', ''))
        t_tech = self.intel.mapeamento_stack_tecnologico(razao_social, "")
        t_ind = self._investigacao_industrial(razao_social)
        t_news = self._buscar_noticias_relevantes(razao_social)
        t_people = self.intel.mapeamento_decisores(razao_social)
        t_capex = self.intel.mapeamento_investimentos_capex(razao_social)
        
        results = await asyncio.gather(t_infra, t_fin, t_tech, t_ind, t_news, t_people, t_capex, return_exceptions=True)
        
        sigef_data = results[0] if not isinstance(results[0], Exception) else {}
        cra_data = results[1] if not isinstance(results[1], Exception) else {}
        tech_data = results[2] if not isinstance(results[2], Exception) else {}
        ind_data = results[3] if not isinstance(results[3], Exception) else {}
        news_data = results[4] if not isinstance(results[4], Exception) else []
        people_data = results[5] if not isinstance(results[5], Exception) else {}
        capex_data = results[6] if not isinstance(results[6], Exception) else []

        # 3. Consolidação dos Fatos
        area_total = sigef_data.get('area_total_hectares', 0)
        faturamento = cra_data.get("faturamento_real", "N/D")
        
        if faturamento == "N/D" and area_total > 0:
            faturamento = f"R$ {area_total * 12000 / 1_000_000:,.0f} Milhões (Estimativa Forense)"

        # 4. Score Técnico
        dados_sas = {
            "hectares_total": area_total,
            "faturamento_estimado": 0, 
            "tech_stack": tech_data,
            "funcionarios_estimados": 0
        }
        try:
            sas_result = self.market.calcular_sas(dados_sas)
            sas_score = sas_result.score
            sas_tier = sas_result.tier.value
        except:
            sas_score = 0
            sas_tier = "N/A"

        # 5. Estrutura de Dados Intermediária (NORMALIZADA)
        # CORREÇÃO: Mapeia 'erp_atual' para 'erp_principal' AQUI
        tech_normalized = {
            "erp_principal": tech_data.get("erp_atual", "N/D"),
            "maturidade_ti": tech_data.get("maturidade_digital", "N/D"),
            "infra_nuvem": tech_data.get("infra_nuvem", "N/D")
        }

        dados_consolidados = {
            "empresa_alvo": razao_social,
            "dados_operacionais": {
                "area_total": area_total,
                "detalhes_industriais": ind_data
            },
            "dados_financeiros": {
                "faturamento_estimado": faturamento
            },
            "tech_stack": tech_normalized, # Usa o dicionário normalizado
            "auditoria_noticias": news_data,
            "dados_organizacionais": {
                "decisores": people_data,
                "capex": capex_data
            }
        }

        # 6. Geração do Relatório Ciro
        if callback: callback("🧠 Processando Dossiê Forense (Protocolo Bruno Lima)...")
        analise_ciro = await self._gerar_relatorio_ciro(dados_consolidados)

        # 7. Montagem Final
        dossie = {
            "empresa_alvo": razao_social,
            "cnpj": cnpj_info.get('cnpj', ''),
            "sas_score": sas_score,
            "sas_tier": sas_tier,
            
            "dados_operacionais": {
                "area_total": area_total,
                "regioes_atuacao": sigef_data.get("estados_operacao", []),
                "numero_fazendas": len(sigef_data.get('car_records', [])),
                "detalhes_industriais": ind_data
            },
            
            "dados_financeiros": {
                "faturamento_estimado": faturamento,
                "capital_social_estimado": cnpj_info.get("capital_social", 0),
                "ebitda_ajustado": cra_data.get("ebitda_consolidado", "N/D"),
                "fontes_auditoria": "Auditoria Digital"
            },
            
            "tech_stack": tech_normalized,
            
            "dados_organizacionais": {
                "quadro_estimado": people_data.get("estimativa_funcionarios", "N/D"),
                "decisores_chave": people_data,
                "investimentos_futuros": capex_data
            },
            
            "analise_estrategica": {
                "quem_e_empresa": "Ver Relatório Forense Abaixo",
                "relatorio_completo_ciro": analise_ciro
            },
            
            "auditoria_noticias": news_data,
            "sigef_car": sigef_data,
            "infra_industrial": ind_data
        }
        
        if callback: callback("✅ Dossiê Forense concluído.")
        return dossie

    # Helpers
    async def _buscar_noticias_relevantes(self, nome_alvo: str) -> List[Dict]:
        prompt = f"ATUE COMO: Auditor. ALVO: {nome_alvo}. Busque 5 notícias recentes (Investimentos, Crimes, M&A). JSON: [{{'titulo':..., 'fonte':..., 'data':..., 'link':...}}]"
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else []
        except: return []

    async def _investigacao_industrial(self, nome_alvo: str) -> Dict:
        prompt = f"ATUE COMO: Engenheiro. ALVO: {nome_alvo}. Liste capacidade de silos, usinas, algodoeiras. JSON: {{'capacidade_armazenagem':..., 'plantas_industriais':...}}"
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except: return {}
