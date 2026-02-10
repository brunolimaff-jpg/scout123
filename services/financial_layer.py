import requests
import json
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FinancialLayer:
    """
    Camada de inteligência financeira:
    - CRAs e Debêntures (CVM/B3)
    - Incentivos fiscais (SUDAM/SUDENE)
    - Multas ambientais (Ibama/SEMA)
    - Processos trabalhistas (TRT/Jusbrasil)
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    # ======== CRA / DEBÊNTURES ========
    async def mineracao_cra_debentures(self, razao_social: str, cnpj: str) -> Dict:
        """
        Busca prospectos de CRA (Certificados de Recebíveis do Agronegócio) na CVM e B3.
        Esses documentos OBRIGAM auditoria e revelam faturamento real, EBITDA, alavancagem.
        """
        logger.info(f"[CRA] Mineração: {razao_social}")
        
        prompt = f"""Você é especialista em mercado de capitais agrícola.

ALVO: {razao_social} ({cnpj})

BUSQUE ESPECIFICAMENTE:
1. Prospectos de CRA (Certificado de Recebível do Agronegócio) na CVM
2. Debêntures agrícolas na B3
3. Relatórios de oferta pública
4. Notas explicativas de balanços auditados

ESTAS EMISSÕES OBRIGAM:
- Auditoria externa (Big 4 ou auditora registrada)
- Publicação de balanço consolidado
- Demonstração de EBITDA ajustado
- Índices de alavancagem (Dívida/EBITDA)
- Fluxo de caixa real

BUSQUE ESPECIFICAMENTE:
- Receita Operacional Líquida (ROL)
- EBITDA ou LAJIDA
- Dívida Total
- Taxa média ponderada de juros (TMPU)
- Datas de emissão e vencimento
- Avalistas ou garantidores

RETORNE JSON:
{{
    "emissoes_cra": [
        {{
            "serie": "CRA Série A 2023",
            "valor_emissao": "R$ 500 milhões",
            "data_emissao": "2023-06-15",
            "data_vencimento": "2028-06-15",
            "taxa_juros": "IPCA + 3.5% a.a.",
            "rol_auditada": "R$ 2.3 bilhões",
            "ebitda_ajustado": "R$ 850 milhões",
            "divida_total": "R$ 1.2 bilhão",
            "alavancagem": 1.41,
            "auditor": "Deloitte"
        }}
    ],
    "emissoes_debentures": [],
    "faturamento_real": "R$ 2.3 bilhões",
    "ebitda_consolidado": "R$ 850 milhões",
    "margem_ebitda": "37%",
    "indice_dps": 1.41,
    "capacidade_investimento": "R$ 300-400 milhões/ano",
    "observacoes": "Empresa com acesso a mercado de capitais, financiamento estruturado, fluxo de caixa robusto."
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[CRA] ✅ Faturamento real: {data.get('faturamento_real', 'N/D')}")
            return data
        except Exception as e:
            logger.error(f"[CRA] ❌ Erro: {e}")
            return {"emissoes_cra": [], "faturamento_real": "N/D", "status": "erro"}
    
    # ======== INCENTIVOS FISCAIS ========
    async def rastreio_incentivos_fiscais(self, cnpj: str, estados_operacao: List[str]) -> Dict:
        """
        Verifica SUDAM, SUDENE, PADIS, etc.
        Indica fluxo de caixa livre e áreas de expansão no Matopiba.
        """
        logger.info(f"[INCENTIVOS] Verificando {', '.join(estados_operacao)}")
        
        estados_str = ", ".join(estados_operacao)
        
        prompt = f"""Você é especialista em incentivos fiscais agrícolas brasileiros.

CNPJ: {cnpj}
ESTADOS DE OPERAÇÃO: {estados_str}

BUSQUE BENEFÍCIOS FISCAIS ATIVOS:
1. SUDAM (Superintendência do Desenvolvimento da Amazônia)
   - Isenção de IRPJ/CSLL
   - Redução de IPI
   - Estados: AM, RO, AC, AP, PA, TO

2. SUDENE (Superintendência do Desenvolvimento do Nordeste)
   - Isenção IRPJ/CSLL
   - Estados: BA, PE, AL, SE, RN, PB, CE, PI, MA

3. PADIS/PADCT (Tecnologia)
   - Se houver R&D em biotech

4. Lei Rouanet (se houver projetos culturais)

5. Lei de Informática (se houver software)

VERIFICAR:
- Nome da lei/decreto
- Percentual de isenção
- Data de vigência
- Data de vencimento
- Unidades elegíveis (qual fazenda tem benefício)

RETORNE JSON:
{{
    "beneficios_ativos": [
        {{
            "tipo": "SUDAM",
            "isenção_irpj": "75%",
            "isenção_csll": "75%",
            "unidade": "Fazenda Porto Velho, RO",
            "data_inicio": "2020-01-01",
            "data_vencimento": "2030-12-31",
            "valor_economizado_anual": "R$ 45 milhões",
            "status": "Ativo"
        }},
        {{
            "tipo": "SUDENE",
            "isenção_irpj": "75%",
            "isenção_csll": "75%",
            "unidade": "Fazenda São Luís, MA",
            "data_inicio": "2019-01-01",
            "data_vencimento": "2029-12-31",
            "valor_economizado_anual": "R$ 32 milhões",
            "status": "Ativo"
        }}
    ],
    "economia_fiscal_anual_total": "R$ 77 milhões",
    "proximos_vencimentos": "2030",
    "recomendacao": "Empresa tem fluxo de caixa livre significativo. Capacidade de investimento em tecnologia: R$ 50-100M/ano."
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[INCENTIVOS] ✅ Economia anual: {data.get('economia_fiscal_anual_total', 'N/D')}")
            return data
        except Exception as e:
            logger.error(f"[INCENTIVOS] ❌ Erro: {e}")
            return {"beneficios_ativos": [], "economia_fiscal_anual_total": "N/D", "status": "erro"}
    
    # ======== MULTAS AMBIENTAIS ========
    async def varredura_multas_ambientais(self, cnpj: str, razao_social: str) -> Dict:
        """
        Busca em listas de embargos do Ibama e SEMA.
        Se tem multa = tem dor. Se tem dor = precisa de consultoria ambiental ou compliance.
        """
        logger.info(f"[MULTAS] Varredura ambiental: {razao_social}")
        
        prompt = f"""Você é especialista em compliance ambiental e regularização fundiária.

CNPJ: {cnpj}
RAZÃO SOCIAL: {razao_social}

BUSQUE:
1. Embargos do IBAMA (lista pública de propriedades embargadas)
2. Multas do IBAMA (em reais, data, motivo)
3. Autos de infração ambiental (federal)
4. Multas estaduais de SEMA (Santa Catarina, Paraná, etc)
5. Débitos de multas (pagas ou pendentes)
6. Ações civis públicas por dano ambiental
7. Passivos ambientais (desmatamento ilegal, APP degradada)

NÃO É SÓ "RISCO":
- Se tem multa = tem dor
- Dor = necessidade de solução
- Soluciones: consultoria ambiental, software de compliance (Klassmatt, Agrosmart, etc)

RETORNE JSON:
{{
    "multas_ativas": [
        {{
            "id_processo": "IBM-2024-001234",
            "data": "2024-01-15",
            "valor_multa": "R$ 2.5 milhões",
            "motivo": "Desmatamento em APP",
            "status": "Embargada",
            "propriedade": "Fazenda X, MT",
            "data_vencimento_pagamento": "2024-03-15",
            "paga": false
        }}
    ],
    "debitos_ambientais_total": "R$ 8.7 milhões",
    "multas_pagas": [
        {{"valor": "R$ 1.2M", "data": "2023-12-01", "motivo": "Queimada irregular"}}
    ],
    "propriedades_embargadas": 2,
    "score_risco_ambiental": "Alto",
    "oportunidades_remedicao": [
        "Consultoria em regularização de APP (WRI Brasil, TNC)",
        "Software de compliance ambiental (Klassmatt P2M)",
        "Programa de rastreabilidade de grãos (Mercado de Crédito de Carbono)"
    ]
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[MULTAS] ✅ Débitos identificados: {data.get('debitos_ambientais_total', 'N/D')}")
            return data
        except Exception as e:
            logger.error(f"[MULTAS] ❌ Erro: {e}")
            return {"multas_ativas": [], "debitos_ambientais_total": "N/D", "status": "erro"}
    
    # ======== PROCESSOS TRABALHISTAS ========
    async def rastreio_processos_trabalhistas(self, cnpj: str, razao_social: str) -> Dict:
        """
        Quantidade de processos ativos no TRT/Jusbrasil/Escavador.
        Se maioria é horas extras = dor em gestão de turno no campo.
        """
        logger.info(f"[TRT] Rastreando processos: {razao_social}")
        
        prompt = f"""Você é especialista em direito trabalhista agrícola.

CNPJ: {cnpj}
RAZÃO SOCIAL: {razao_social}

BUSQUE EM:
1. Jusbrasil (processos públicos)
2. Escavador (banco de processos)
3. TRT (Tribunal Regional do Trabalho) de cada estado onde opera

PROCURE POR:
- Número total de processos ativos
- Natureza dos processos (horas extras, acidente, FGTS, rescisão, etc)
- Valores reclamados (em reais)
- Sentença (favorável/desfavorável)
- Executados/em execução

ANÁLISE DE PADRÃO:
- Se >60% são "horas extras" = falha em sistema de ponto/turno
- Se >40% são "acidente de trabalho" = falha em segurança
- Se crescimento ano/ano = problema sistêmico, não pontual

OPORTUNIDADE SENIOR HCM:
- Sistema de ponto biométrico no campo
- Gestão de turno mobile
- Compliance trabalhista automático

RETORNE JSON:
{{
    "total_processos_ativos": 156,
    "processos_por_tipo": {{
        "horas_extras": 98,
        "acidente_trabalho": 23,
        "fgts_indevido": 18,
        "rescisao_indevida": 12,
        "equipamento_protecao": 5
    }},
    "valor_total_reclamado": "R$ 47 milhões",
    "sentencas_desfavoraveis": 89,
    "sentencas_favoraveis": 34,
    "em_execucao": 78,
    "padrão_identificado": "Horas extras (63% dos casos) - Indica falha crítica em gestão de turno e sistema de ponto",
    "dor_principal": "Gestão de turno agrícola inadequada, sistema de ponto manual ou ausente",
    "oportunidade_venda": [
        "Senior HCM com módulo de Gestão de Turno Agrícola",
        "Sistema de Ponto Biométrico Mobile",
        "Compliance Trabalhista Automático"
    ],
    "potencial_redução": "R$ 20-30M/ano com implantação de sistema adequado"
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[TRT] ✅ {data.get('total_processos_ativos', 0)} processos identificados")
            return data
        except Exception as e:
            logger.error(f"[TRT] ❌ Erro: {e}")
            return {"total_processos_ativos": 0, "processos_por_tipo": {}, "status": "erro"}
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse seguro de JSON."""
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            logger.warning("Falha ao parsear JSON financeiro")
            return {}
