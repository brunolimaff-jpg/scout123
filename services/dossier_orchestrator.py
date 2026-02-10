"""
services/dossier_orchestrator.py — MODO AUDITORIA DE PRECISÃO
Foco total em evidências (Links e Notícias) e Dados Industriais Reais.
Sem inferências mágicas.
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
    Orquestrador focado em AUDITORIA e EVIDÊNCIAS.
    Prioriza links, notícias reais e dados técnicos confirmados.
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

    async def _buscar_noticias_relevantes(self, nome_alvo: str) -> List[Dict]:
        """
        Busca notícias recentes e links para auditoria humana.
        Foca em: Investimentos, Processos, Expansão, M&A, Escândalos.
        """
        logger.info(f"[Auditoria] Buscando notícias para: {nome_alvo}")
        prompt = f"""
        ATUE COMO: Auditor de Compliance e Risco Agro.
        ALVO: "{nome_alvo}"
        
        TAREFA: Localize 5 notícias ou fatos relevantes recentes (2023-2026) sobre esta empresa.
        FOCO:
        1. Novos investimentos (ex: usinas, armazéns, aquisições de terra).
        2. Problemas jurídicos ou ambientais (embargos, multas).
        3. Parcerias estratégicas ou M&A.
        
        RETORNE APENAS JSON:
        [
            {{
                "titulo": "Resumo da notícia em 1 frase",
                "fonte": "Nome do Site/Jornal",
                "data_aprox": "Ano ou Mês/Ano",
                "link": "URL se tiver ou termo de busca sugerido"
            }}
        ]
        """
        try:
            # Temperatura 0.0 para evitar alucinação de notícias falsas
            response = await self.gemini.call_with_retry(prompt, max_retries=2, use_search=True, temperature=0.0)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []
        except Exception as e:
            logger.warning(f"[Auditoria] Erro ao buscar notícias: {e}")
            return []

    async def _investigacao_industrial(self, nome_alvo: str) -> Dict:
        """
        Busca dados industriais pesados que o SIGEF não pega.
        Ex: Capacidade de armazenagem, Usinas, Confinamento, Algodoeira.
        """
        logger.info(f"[Industrial] Mapeando ativos físicos de: {nome_alvo}")
        prompt = f"""
        ATUE COMO: Engenheiro Industrial Agrícola.
        ALVO: "{nome_alvo}"
        
        TAREFA: Liste a capacidade instalada industrial e infraestrutura.
        BUSQUE POR:
        - Unidades de Beneficiamento de Sementes (UBS)
        - Armazéns Gerais (Capacidade estática em sacas/toneladas)
        - Usinas (Etanol de milho, Bioenergia)
        - Algodoeiras (Descaroçamento)
        - Confinamento (Cabeças estáticas)
        
        RETORNE JSON:
        {{
            "capacidade_armazenagem": "ex: 2 milhões de sacas (Estimado)",
            "plantas_industriais": ["Lista de unidades encontradas"],
            "segmentos_atuacao": ["Soja", "Milho", "Etanol", etc],
            "infraestrutura_logistica": "Detalhes sobre frota ou ramais ferroviários se houver"
        }}
        """
        try:
            response = await self.gemini.call_with_retry(prompt, use_search=True, temperature=0.1)
            clean = response.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {}
        except:
            return {}

    async def executar_dosier_completo(self, razao_social: str, cnpj: str = "", callback=None) -> Dict:
        """Pipeline Auditoria Total."""
        from services.cnpj_service import consultar_cnpj
        
        if callback: callback(f"🚀 Iniciando Auditoria Digital: {razao_social}...")
        
        # 1. Identificação Corporativa
        cnpj_info = {}
        cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ""
        if cnpj_limpo and len(cnpj_limpo) == 14:
            c_data = consultar_cnpj(cnpj_limpo)
            if c_data:
                cnpj_info = {"cnpj": c_data.cnpj, "capital_social": c_data.capital_social, "nome": c_data.razao_social}
        
        # 2. Execução Paralela de Inteligência (Todas as camadas + Auditoria)
        if callback: callback("📡 Varrendo bases públicas, notícias e dados industriais...")
        
        t_infra = self.infra.buscar_sigef_car(razao_social, []) # Terras
        t_fin = self.financial.mineracao_cra_debentures(razao_social, cnpj_info.get('cnpj', '')) # Dinheiro
        t_tech = self.intel.mapeamento_stack_tecnologico(razao_social, "") # TI
        t_ind = self._investigacao_industrial(razao_social) # Fábricas/Silos
        t_news = self._buscar_noticias_relevantes(razao_social) # Auditoria/Escândalos
        
        results = await asyncio.gather(t_infra, t_fin, t_tech, t_ind, t_news, return_exceptions=True)
        
        sigef_data = results[0] if not isinstance(results[0], Exception) else {}
        cra_data = results[1] if not isinstance(results[1], Exception) else {}
        tech_data = results[2] if not isinstance(results[2], Exception) else {}
        ind_data = results[3] if not isinstance(results[3], Exception) else {}
        news_data = results[4] if not isinstance(results[4], Exception) else []

        # 3. Consolidação de Fatos (Sem inferência cega)
        area_total = sigef_data.get('area_total_hectares', 0)
        faturamento = cra_data.get("faturamento_real", "N/D (Não divulgado)")
        
        # Se não achou faturamento mas tem ativos gigantes, avisa
        if faturamento == "N/D (Não divulgado)" and area_total > 0:
            faturamento = "Não público (Verificar ativos)"

        # 4. Cálculo de Score Técnico (SAS)
        dados_sas = {
            "hectares_total": area_total,
            "faturamento_estimado": 0, # Zera para não influenciar errado se não tiver balanço
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

        # 5. Montagem do Dossiê Final (Rico em Texto e Links)
        dossie = {
            "empresa_alvo": razao_social,
            "cnpj": cnpj_info.get('cnpj', ''),
            "sas_score": sas_score,
            "sas_tier": sas_tier,
            
            "dados_operacionais": {
                "area_total": area_total,
                "hectares_total": area_total,
                "regioes_atuacao": sigef_data.get("estados_operacao", []),
                "numero_fazendas": len(sigef_data.get('car_records', [])),
                "detalhes_industriais": ind_data # Nova chave rica
            },
            
            "dados_financeiros": {
                "faturamento_estimado": faturamento,
                "capital_social_estimado": cnpj_info.get("capital_social", 0),
                "ebitda_ajustado": cra_data.get("ebitda_consolidado", "N/D"),
                "fontes_auditoria": "Balanços, CRAs e Mídia Especializada"
            },
            
            "tech_stack": {
                "erp_principal": tech_data.get("erp_atual", "Não Identificado (Gap Crítico)"),
                "maturidade_ti": tech_data.get("maturidade_digital", "Baixa Visibilidade")
            },
            
            "analise_estrategica": {
                "quem_e_empresa": f"Grupo com {area_total} ha mapeados e operação industrial em: {', '.join(ind_data.get('segmentos_atuacao', []))}.",
                "complexidade_dores": self._gerar_resumo_dores(ind_data, tech_data),
                "arsenal_recomendado": "Audit: Validar integração Planta Industrial x Campo (ERP + MES)",
                "plano_ataque": "Usar notícias recentes de expansão como gancho de entrada."
            },
            
            # SEÇÃO DE AUDITORIA (NOVA)
            "auditoria_noticias": news_data,
            
            # Dados brutos preservados
            "sigef_car": sigef_data,
            "infra_industrial": ind_data
        }
        
        if callback: callback("✅ Dossiê de Auditoria gerado com sucesso!")
        return dossie

    def _gerar_resumo_dores(self, ind_data: Dict, tech_data: Dict) -> str:
        """Gera texto de dores baseado em fatos industriais, não genéricos."""
        dores = []
        
        if ind_data.get("capacidade_armazenagem"):
            dores.append("Gestão complexa de estoques (Armazéns Gerais) e quebra técnica.")
            
        if "Etanol" in str(ind_data.get("segmentos_atuacao", [])):
            dores.append("Alta complexidade fiscal/industrial (Indústria de Transformação).")
            
        erp = tech_data.get("erp_atual", "").lower()
        if not erp or erp == "n/d":
            dores.append("Risco crítico de governança por falta de ERP Tier-1 visível.")
        elif "excel" in erp:
            dores.append("Operação de alto risco rodando em planilhas/sistemas legados.")
            
        if not dores:
            return "Necessário aprofundamento em reunião (Dores não públicas)."
            
        return " | ".join(dores)
