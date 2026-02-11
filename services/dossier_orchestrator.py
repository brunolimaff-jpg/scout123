"""
services/dossier_orchestrator.py — VERSÃO FINAL INTEGRADA
Conecta a Infraestrutura Profunda (Raio-X) ao Protocolo Ciro.
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
    Agora capaz de interpretar dados complexos de geolocalização e logística.
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
        Gera o texto 'Análise Estratégica' no estilo CIRO, usando os dados profundos.
        """
        logger.info(f"[Orchestrator] Gerando Relatório Protocolo Bruno Lima para: {dados_consolidados['empresa_alvo']}")
        
        empresa = dados_consolidados.get('empresa_alvo', 'Alvo')
        
        # Extração Inteligente dos Novos Dados de Infra
        infra_raw = dados_consolidados.get('sigef_car', {})
        
        fazendas = infra_raw.get('lista_fazendas', [])
        qtd_fazendas = len(fazendas)
        nomes_fazendas = ", ".join([f.get('nome', '') for f in fazendas[:5]]) # Pega as 5 primeiras para citar
        
        logistica = infra_raw.get('logistica_bimodal', {})
        frota = logistica.get('frota_rodoviaria', 'N/D')
        aviacao = logistica.get('frota_aerea', 'N/D')
        
        corp = infra_raw.get('corporativo', {})
        sede = corp.get('matriz_endereco', 'N/D')
        
        # Dados Financeiros e Tech
        faturamento = dados_consolidados.get('dados_financeiros', {}).get('faturamento_estimado', 'N/D')
        erp = dados_consolidados.get('tech_stack', {}).get('erp_principal', 'N/D')
        
        # Contexto Rico para o Prompt
        prompt = f"""
        ATUE COMO: CIRO, O AUDITOR FORENSE DE VENDAS (Expert em Agronegócio).
        
        ALVO: {empresa}
        
        DADOS FORENSES COLETADOS (USE ISSO NO TEXTO):
        1. 🧬 PORTE:
           - Faturamento: {faturamento}
           - Sede: {sede}
           
        2. 🚜 INFRAESTRUTURA REAL (Cite nomes):
           - Quantidade de Fazendas Mapeadas: {qtd_fazendas}
           - Principais Unidades: {nomes_fazendas}... (e outras)
           
        3. 🚚 LOGÍSTICA & MAQUINÁRIO (Ativos):
           - Frota: {frota}
           - Aviação: {aviacao}
           
        4. 💻 TECNOLOGIA:
           - ERP Identificado: {erp}
           
        SUA MISSÃO: Escrever o "PROTOCOLO BRUNO LIMA".
        Seja cirúrgico. Se eles têm hangar e aviões, mencione o custo de manutenção disso. Se têm frota própria, fale da gestão de pneus e combustível. Conecte o mundo físico ao software.
        
        ESTRUTURA OBRIGATÓRIA (Markdown):
        
        # 🕵️‍♂️ DOSSIÊ DE INTELIGÊNCIA: {empresa}
        **STATUS:** [Defina com base nos ativos: BIG FISH / OPERAÇÃO COMPLEXA]
        **RESUMO DO ESPIÃO:** [Resumo agressivo focado na complexidade logística x gestão].
        
        ## 1. 🧬 RAIO-X CORPORATIVO
        [Analise o porte. Cite onde fica a sede. Se o faturamento for alto e a sede for simples, elogie a eficiência. Se for suntuosa, cite custo.]
        
        ## 2. 🚜 O IMPÉRIO FÍSICO (TERRAS & ATIVOS)
        * **Território:** Mapeamos {qtd_fazendas} unidades produtivas, incluindo [{nomes_fazendas}].
        * **Poder de Fogo Logístico:** [Analise a frota: "{frota}" e a aviação "{aviacao}". Explique que gerir isso sem software de ponta é impossível.]
        
        ## 3. 💻 A "SMOKING GUN" (TECNOLOGIA)
        * **O Cenário:** Identificamos ERP [{erp}].
        * **A Contradição:** [O ERP atual suporta essa frota e essas fazendas? Onde está o buraco? Manutenção? Compras?]
        
        ## 4. 🎯 PLANO DE GUERRA
        | Vertical | O Fato (Ativo Real) | O Argumento de Venda |
        |---|---|---|
        | Logística | [Cite a frota/avião] | "Controle de pneus e combustível em tempo real" |
        | Agrícola | [Cite as fazendas] | "Gestão multi-unidade centralizada" |
        
        ## 📝 SCRIPT PARA O EXECUTIVO
        > [Mensagem direta citando os aviões ou a frota para chamar atenção].
        """
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=2, use_search=False, temperature=0.5)
            return response
        except Exception as e:
            logger.error(f"Erro ao gerar relatório Ciro: {e}")
            return "Relatório Forense indisponível."

    async def executar_dosier_completo(self, razao_social: str, cnpj: str = "", callback=None) -> Dict:
        """Pipeline Auditoria Total."""
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
        if callback: callback("📡 Coletando evidências forenses (Balanços, Frota, Terras)...")
        
        t_infra = self.infra.mapeamento_geografico_completo(razao_social) # NOVA CHAMADA
        t_fin = self.financial.mineracao_cra_debentures(razao_social, cnpj_info.get('cnpj', ''))
        t_tech = self.intel.mapeamento_stack_tecnologico(razao_social, "")
        t_news = self._buscar_noticias_relevantes(razao_social)
        t_people = self.intel.mapeamento_decisores(razao_social)
        t_capex = self.intel.mapeamento_investimentos_capex(razao_social)
        
        # Removido t_ind separado pois agora está dentro do t_infra (mapeamento completo)
        results = await asyncio.gather(t_infra, t_fin, t_tech, t_news, t_people, t_capex, return_exceptions=True)
        
        infra_data = results[0] if not isinstance(results[0], Exception) else {}
        cra_data = results[1] if not isinstance(results[1], Exception) else {}
        tech_data = results[2] if not isinstance(results[2], Exception) else {}
        news_data = results[3] if not isinstance(results[3], Exception) else []
        people_data = results[4] if not isinstance(results[4], Exception) else {}
        capex_data = results[5] if not isinstance(results[5], Exception) else []

        # 3. Consolidação Inteligente (Adaptação à nova estrutura de infra)
        # Tenta pegar area_total_ha (novo) ou area_total_hectares (antigo/fallback)
        area_total = infra_data.get('resumo_territorial', {}).get('area_total_ha', 0)
        if area_total == 0:
            area_total = infra_data.get('area_total_hectares', 0)

        faturamento = cra_data.get("faturamento_real", "N/D")
        
        # Estimativa Forense se não tiver balanço
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

        # 5. Normalização de Dados Tech
        tech_normalized = {
            "erp_principal": tech_data.get("erp_atual", "N/D"),
            "maturidade_ti": tech_data.get("maturidade_digital", "N/D"),
            "infra_nuvem": tech_data.get("infra_nuvem", "N/D")
        }

        # 6. Estrutura de Consolidação (Passando o objeto infra_data inteiro para o relatório Ciro)
        dados_consolidados = {
            "empresa_alvo": razao_social,
            "sigef_car": infra_data, # Passa a estrutura nova completa
            "dados_financeiros": {"faturamento_estimado": faturamento},
            "tech_stack": tech_normalized,
            "auditoria_noticias": news_data,
            "dados_organizacionais": {"decisores": people_data, "capex": capex_data}
        }

        # 7. Geração do Relatório Ciro
        if callback: callback("🧠 Processando Dossiê Forense (Protocolo Bruno Lima)...")
        analise_ciro = await self._gerar_relatorio_ciro(dados_consolidados)

        # 8. Montagem Final do Dossiê (Compatível com App e PDF)
        dossie = {
            "empresa_alvo": razao_social,
            "cnpj": cnpj_info.get('cnpj', ''),
            "sas_score": sas_score,
            "sas_tier": sas_tier,
            
            "dados_operacionais": {
                "area_total": area_total,
                "regioes_atuacao": infra_data.get('resumo_territorial', {}).get('estados', []),
                "numero_fazendas": len(infra_data.get('lista_fazendas', [])),
                # Mapeia os dados industriais novos para a chave que o PDF espera
                "detalhes_industriais": {
                    "plantas_industriais": [item['detalhe'] for item in infra_data.get('complexo_industrial', [])],
                    "capacidade_armazenagem": infra_data.get('complexo_industrial', [{}])[0].get('detalhe', 'N/D') if infra_data.get('complexo_industrial') else "N/D",
                    "segmentos_atuacao": ["Multicultura (Soja/Milho/Algodão)"]
                }
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
            "sigef_car": infra_data,
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
