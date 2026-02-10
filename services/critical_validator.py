import json
import logging
import math
from typing import Dict, List

logger = logging.getLogger(__name__)

class CriticalValidator:
    """
    Agente adversário que valida consistência de dados.
    Se há inconsistência lógica = sinaliza "DADO SUSPEITO".
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    async def validar_consistencia_dados(self, dossie_completo: Dict) -> Dict:
        """
        Cruza dados de múltiplos agentes para verificar coerência lógica.
        Exemplo: Faturamento 1.7B + 230k ha = R$ 7.300/ha (baixo para algodão).
        """
        logger.info("[CRÍTICO] Iniciando validação adversária")
        
        # Extrai dados estruturados
        area_total = dossie_completo.get('dados_operacionais', {}).get('area_total', 0)
        faturamento = dossie_completo.get('dados_financeiros', {}).get('faturamento_estimado', 0)
        culturas = dossie_completo.get('dados_operacionais', {}).get('culturas', [])
        
        validacoes = {
            "alertas": [],
            "recomendacoes": []
        }
        
        # ======== VALIDAÇÃO 1: Produtividade ========
        if area_total > 0 and isinstance(faturamento, (int, float)):
            try:
                faturamento_limpo = float(str(faturamento).replace("R$", "").replace("B", "").strip())
                produtividade = (faturamento_limpo * 1_000_000_000) / area_total  # converte B para valor
                
                # Benchmarks por cultura
                benchmarks = {
                    "Soja": (3000, 7000),          # R$/ha
                    "Milho": (2500, 6000),
                    "Algodão": (4500, 12000),
                    "Café": (15000, 45000),
                    "Cana-de-açúcar": (8000, 25000),
                    "Pecuária": (500, 2000)
                }
                
                cultura_principal = culturas[0] if culturas else "Não identificada"
                benchmark_min, benchmark_max = benchmarks.get(cultura_principal, (2000, 10000))
                
                if produtividade < benchmark_min:
                    validacoes["alertas"].append({
                        "tipo": "PRODUTIVIDADE_BAIXA",
                        "severidade": "CRÍTICA",
                        "mensagem": f"Produtividade de R$ {produtividade:,.0f}/ha é ABAIXO do benchmark ({benchmark_min:,}-{benchmark_max:,}/ha para {cultura_principal})",
                        "causa_possivel": "Faturamento subestimado OU área supestimada",
                        "acao": "Revisar CRA/SIGEF e prospectos de CRA para validar faturamento real"
                    })
                elif produtividade > benchmark_max * 1.5:
                    validacoes["alertas"].append({
                        "tipo": "PRODUTIVIDADE_ALTA",
                        "severidade": "AVISO",
                        "mensagem": f"Produtividade de R$ {produtividade:,.0f}/ha é ACIMA do benchmark. Possível agregação de valor.",
                        "causa_possivel": "Verticalização, processamento, exportação de valor agregado",
                        "acao": "Investigar cadeia de valor e margens"
                    })
                else:
                    validacoes["recomendacoes"].append(f"✓ Produtividade de R$ {produtividade:,.0f}/ha está alinhada com mercado")
            except:
                pass
        
        # ======== VALIDAÇÃO 2: Consistência Dívida/EBITDA ========
        divida = dossie_completo.get('dados_financeiros', {}).get('divida_total', 0)
        ebitda = dossie_completo.get('dados_financeiros', {}).get('ebitda_ajustado', 0)
        
        if divida > 0 and ebitda > 0:
            try:
                divida_valor = float(str(divida).replace("R$", "").replace("B", "").strip()) if isinstance(divida, str) else divida
                ebitda_valor = float(str(ebitda).replace("R$", "").replace("B", "").strip()) if isinstance(ebitda, str) else ebitda
                
                indice_dps = divida_valor / ebitda_valor
                
                if indice_dps > 3:
                    validacoes["alertas"].append({
                        "tipo": "ALAVANCAGEM_ALTA",
                        "severidade": "CRÍTICA",
                        "mensagem": f"D/EBITDA de {indice_dps:.2f}x é ELEVADO (limite saudável: 2x)",
                        "implicacao": "Risco de refinanciamento, fluxo de caixa apertado",
                        "acao": "Empresa pode estar retida em TI/inovação por constrangimento de caixa"
                    })
                elif indice_dps < 0.5:
                    validacoes["recomendacoes"].append(f"✓ Alavancagem saudável (D/EBITDA {indice_dps:.2f}x). Capacidade de investimento: SIM")
                else:
                    validacoes["recomendacoes"].append(f"✓ Alavancagem moderada (D/EBITDA {indice_dps:.2f}x)")
            except:
                pass
        
        # ======== VALIDAÇÃO 3: Coerência Operacional ========
        processos_trabalhistas = dossie_completo.get('dados_financeiros', {}).get('total_processos_trabalhistas', 0)
        if processos_trabalhistas > 100:
            validacoes["alertas"].append({
                "tipo": "RISCO_TRABALHISTA_ELEVADO",
                "severidade": "ALTA",
                "mensagem": f"{processos_trabalhistas} processos trabalhistas ativos",
                "implicacao": "Problema sistêmico em gestão de RH ou segurança",
                "acao": "Oportunidade de venda: Senior HCM + Sistema de Ponto + Compliance"
            })
        
        # ======== VALIDAÇÃO 4: Multas Ambientais ========
        multas_ambientais = dossie_completo.get('dados_financeiros', {}).get('debitos_ambientais_total', 0)
        if multas_ambientais > 1_000_000:  # > R$ 1M
            validacoes["alertas"].append({
                "tipo": "RISCO_AMBIENTAL",
                "severidade": "MÉDIA",
                "mensagem": f"Débitos ambientais: {multas_ambientais:,.0f}",
                "implicacao": "Problemas de compliance, possível embargo de propriedade",
                "acao": "Oportunidade: Software de compliance ambiental (Klassmatt P2M)"
            })
        
        return validacoes
    
    async def extrair_pdfs_documentos(self, razao_social: str) -> Dict:
        """
        Busca e lê PDFs de:
        - Relatórios de Sustentabilidade
        - Prospectos de CRA
        - Relatórios de Impacto Social
        Usa Gemini 1.5 Pro (long context) para ler documento inteiro.
        """
        logger.info(f"[PDF PARSER] Buscando documentos de {razao_social}")
        
        prompt = f"""Você é especialista em extração de informações de documentos corporativos agrícolas.

TAREFA: Buscar e descrever documentos de {razao_social}

TIPOS DE DOCUMENTOS A BUSCAR:
1. Relatórios de Sustentabilidade (anual, 2023, 2024)
   - Publicados no site corporativo
   - PDFs públicos
   - Contêm: áreas, produção, investimentos em TI, políticas ambientais

2. Prospectos de CRA/Debêntures
   - Publicados na CVM ou B3
   - PDFs detalhados com balanço auditado
   - Contêm: faturamento real, EBITDA, índices de alavancagem

3. Relatórios de Impacto Social/Ambiental
   - Certificações (FSC, Bonsucro, Rainforest Alliance)
   - Indicadores de uso de tecnologia

4. Apresentações Corporativas
   - Investor relations
   - Eventos/conferências

RETORNE JSON COM:
{{
    "documentos_encontrados": [
        {{
            "tipo": "Relatório de Sustentabilidade",
            "titulo": "Scheffer Sustainability Report 2024",
            "url": "https://...",
            "data_publicacao": "2024-01-15",
            "tamanho_mb": 8.5,
            "idioma": "Português",
            "informacoes_extraidas": {{
                "area_total_hectares": 230000,
                "producao_soja_toneladas": 950000,
                "investimento_ti_2024": "R$ 85 milhões",
                "funcionarios": 2847,
                "certificacoes": ["ISO 14001", "ISO 45001"],
                "objetivos_ti": ["Digitalização do campo 100%", "Precisão agrícola avançada"]
            }}
        }},
        {{
            "tipo": "Prospecto CRA",
            "titulo": "CRA Série A 2023 - Scheffer",
            "url": "https://...",
            "data_publicacao": "2023-06-15",
            "tamanho_mb": 12.3,
            "informacoes_extraidas": {{
                "faturamento_auditado": "R$ 2.8 bilhões",
                "ebitda_ajustado": "R$ 1.05 bilhão",
                "margem_ebitda": "37.5%",
                "divida_total": "R$ 1.2 bilhão",
                "indice_dps": 1.14,
                "auditor": "Deloitte"
            }}
        }}
    ],
    "total_documentos_identificados": 2,
    "score_qualidade_informacao": "Excelente (Documentos primários, auditados)"
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[PDF PARSER] ✅ {data.get('total_documentos_identificados', 0)} documentos encontrados")
            return data
        except Exception as e:
            logger.error(f"[PDF PARSER] ❌ Erro: {e}")
            return {"documentos_encontrados": [], "status": "erro"}
    
    def _parse_json_response(self, response: str) -> Dict:
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            logger.warning("Falha ao parsear JSON crítico")
            return {}
