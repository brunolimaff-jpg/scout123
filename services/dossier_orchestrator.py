"""
services/dossier_orchestrator.py — MODO PROTOCOLO BRUNO LIMA (ESTILO CIRO)
Gera o relatório com tom de Auditoria Forense, buscando contradições e dados duros.
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
        Gera o texto 'Análise Estratégica' no estilo CIRO:
        Forense, Agressivo, Focado em Contradições e Oportunidades.
        """
        logger.info(f"[Orchestrator] Gerando Relatório Protocolo Bruno Lima para: {dados_consolidados['empresa_alvo']}")
        
        prompt = f"""
        ATUE COMO: CIRO, O AUDITOR FORENSE DE VENDAS (Expert em Agronegócio e TI).
        
        DADOS DA VÍTIMA (ALVO):
        - Nome: {dados_consolidados['empresa_alvo']}
        - Área: {dados_consolidados['dados_operacionais']['area_total']} hectares (Isso define o porte).
        - Faturamento Real/Estimado: {dados_consolidados['dados_financeiros']['faturamento_estimado']}
        - Infra Industrial: {dados_consolidados['dados_operacionais']['detalhes_industriais']}
        - ERP Identificado: {dados_consolidados['tech_stack']['erp_principal']}
        - Notícias/Escândalos: {str(dados_consolidados['auditoria_noticias'])[:1000]}
        - Decisores/Vagas: {str(dados_consolidados['dados_organizacionais'])}
        
        SUA MISSÃO: Escrever o "PROTOCOLO BRUNO LIMA" (Relatório de Inteligência).
        
        TOM DE VOZ:
        - Use termos como: "Smoking Gun", "Frankenstein Tecnológico", "Auditoria Forense", "Dívida", "CRA", "Big 4".
        - Seja cético. Se eles dizem que usam SAP mas tem vaga pra Totvs, aponte a mentira.
        - Se o faturamento é alto, assuma que são auditados por Big 4 (KPMG/Deloitte/PwC) e use isso.
        
        ESTRUTURA OBRIGATÓRIA DA RESPOSTA (Markdown):
        
        # 🕵️‍♂️ DOSSIÊ DE INTELIGÊNCIA: {dados_consolidados['empresa_alvo']}
        **STATUS:** [Defina: ALTO VALOR ESTRATÉGICO / RISCO DE CHURN / BIG FISH]
        **RESUMO DO ESPIÃO:** [Uma frase de impacto resumindo a bagunça tecnológica ou a oportunidade de ouro].
        
        ## 1. 🧬 RAIO-X CORPORATIVO (HARD DATA)
        * **Faturamento:** [Valor] (Fonte: Auditoria Digital).
        * **Porte Real:** [Área] ha → Isso exige governança de [Nível].
        * **Saúde/Auditoria:** [Se faturar >300M, diga que provável emissor de CRA e auditado. Se achar notícias de dívida, cite].
        
        ## 2. 🚜 INFRAESTRUTURA (ATIVOS OCULTOS)
        * **Fábricas a Céu Aberto:** [Liste Algodoeiras, UBS, Armazéns encontrados].
        * **O Pulo do Gato:** [Explique por que o ERP atual falha em gerir esses ativos industriais. Ex: "GAtec não faz PCP de algodoeira"].
        
        ## 3. 💻 A "SMOKING GUN" (TECNOLOGIA)
        * **O Cenário:** Identificamos ERP [{dados_consolidados['tech_stack']['erp_principal']}].
        * **A Contradição:** [Se tiver vaga de outro sistema, aponte. Se não tiver ERP, chame de "Caixa Preta". Se tiver Senior, elogie mas aponte brechas].
        * **Veredito:** [É um Frankenstein? É uma planilha de luxo?]
        
        ## 4. 🎯 OPPORTUNITY MAP (PLANO DE GUERRA)
        | Vertical | O Fato (Evidência) | O Argumento de Venda (Pitch Matador) |
        |---|---|---|
        | Backoffice | [Ex: Usam Totvs/Excel] | [Argumento de unificação/TCO] |
        | Agro | [Ex: Usam GAtec/Outro] | [Argumento de integração nativa] |
        | Indústria | [Tem Algodoeira/Silo] | "Transforme o beneficiamento em Indústria 4.0" |
        | Fintech | [Muitos funcionários] | "Bancarize a safra com Wiipo" |
        
        ## 📝 SCRIPT PARA O EXECUTIVO (Copie e Cole)
        > [Escreva uma mensagem de WhatsApp curta, grossa e baseada em dados para o Diretor, citando a auditoria e o problema técnico encontrado].
        """
        
        try:
            # Temperatura um pouco mais alta (0.4) para ele ser criativo nos argumentos, mas fiel aos dados
            response = await self.gemini.call_with_retry(prompt, max_retries=2, use_search=False, temperature=0.4)
            return response
        except Exception as e:
            logger.error(f"Erro ao gerar relatório Ciro: {e}")
            return "Relatório Forense indisponível. Dados insuficientes para análise de profundidade."

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
        
        # 2. Execução Paralela (Coleta de Evidências)
        if callback: callback("📡 Coletando evidências forenses (Balanços, Vagas, Terras)...")
        
        t_infra = self.infra.buscar_sigef_car(razao_social, [])
        t_fin = self.financial.mineracao_cra_debentures(razao_social, cnpj_info.get('cnpj', ''))
        t_tech = self.intel.mapeamento_stack_tecnologico(razao_social, "")
        t_ind = self._investigacao_industrial(razao_social) # Metodo interno existente
        t_news = self._buscar_noticias_relevantes(razao_social) # Metodo interno existente
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
            # Fallback se não achar balanço: Estimativa Forense
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

        # 5. Estrutura de Dados Intermediária
        dados_consolidados = {
            "empresa_alvo": razao_social,
            "dados_operacionais": {
                "area_total": area_total,
                "detalhes_industriais": ind_data
            },
            "dados_financeiros": {
                "faturamento_estimado": faturamento
            },
            "tech_stack": tech_data,
            "auditoria_noticias": news_data,
            "dados_organizacionais": {
                "decisores": people_data,
                "capex": capex_data
            }
        }

        # 6. GERAÇÃO DO RELATÓRIO "CIRO" (O Grande Diferencial)
        if callback: callback("🧠 Processando Dossiê Forense (Protocolo Bruno Lima)...")
        analise_ciro = await self._gerar_relatorio_ciro(dados_consolidados)

        # 7. Montagem Final
        dossie = {
            "empresa_alvo": razao_social,
            "cnpj": cnpj_info.get('cnpj', ''),
            "sas_score": sas_score,
            "sas_tier": sas_tier,
            
            # Dados estruturados para o PDF
            "dados_operacionais": {
                "area_total": area_total,
                "regioes_atuacao": sigef_data.get("estados_operacao", []),
                "numero_fazendas": len(sigef_data.get('car_records', []))
            },
            
            "dados_financeiros": {
                "faturamento_estimado": faturamento,
                "capital_social_estimado": cnpj_info.get("capital_social", 0),
                "ebitda_ajustado": cra_data.get("ebitda_consolidado", "N/D")
            },
            
            "tech_stack": {
                "erp_principal": tech_data.get("erp_atual", "N/D"),
                "maturidade_ti": tech_data.get("maturidade_digital", "N/D")
            },
            
            "dados_organizacionais": {
                "quadro_estimado": people_data.get("estimativa_funcionarios", "N/D"),
                "decisores_chave": people_data,
                "investimentos_futuros": capex_data
            },
            
            # AQUI ESTÁ A MÁGICA: O Texto do Ciro vai direto para a Análise Estratégica
            "analise_estrategica": {
                "quem_e_empresa": "Ver Relatório Forense Abaixo", # Placeholder
                "complexidade_dores": "Ver Relatório Forense Abaixo",
                "arsenal_recomendado": "Ver Relatório Forense Abaixo",
                "plano_ataque": "Ver Relatório Forense Abaixo",
                "relatorio_completo_ciro": analise_ciro # Nova chave para o frontend exibir
            },
            
            "auditoria_noticias": news_data,
            "sigef_car": sigef_data,
            "infra_industrial": ind_data
        }
        
        if callback: callback("✅ Dossiê Forense concluído.")
        return dossie

    # Métodos auxiliares (mantidos para o código funcionar)
    async def _buscar_noticias_relevantes(self, nome_alvo: str) -> List[Dict]:
        """(Mantido do código anterior - Auditoria de Notícias)"""
        prompt = f"ATUE COMO: Auditor. ALVO: {nome_alvo}. Busque 5 notícias recentes (Investimentos, Crimes, M&A). JSON: [{{'titulo':..., 'fonte':..., 'data':..., 'link':...}}]"
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else []
        except: return []

    async def _investigacao_industrial(self, nome_alvo: str) -> Dict:
        """(Mantido do código anterior - Auditoria Industrial)"""
        prompt = f"ATUE COMO: Engenheiro. ALVO: {nome_alvo}. Liste capacidade de silos, usinas, algodoeiras. JSON: {{'capacidade_armazenagem':..., 'plantas_industriais':...}}"
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            return json.loads(match.group(0)) if match else {}
        except: return {}
