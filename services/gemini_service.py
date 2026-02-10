"""
services/gemini_service.py — RADAR Intelligence Engine ULTRA-PROFUNDO
Motor IA com 9 Agentes TURBINADOS para Extração Máxima de Inteligência
PRECISÃO > CUSTO | SEM DO DE TOKENS
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import json, re, time
from typing import Optional, Any
from google import genai
from google.genai import types
from services.cache_service import cache
from services.request_queue import request_queue, Priority

# Voltando para o modelo rapido e estavel
MODEL = "gemini-2.0-flash"

# Ferramenta de Busca Nativa
SEARCH = types.Tool(google_search=types.GoogleSearch())

# === IDENTIDADE DO SISTEMA (RADAR AWACS) ===
RADAR_IDENTITY = """VOCE E O SISTEMA RADAR (PROTOCOLO FOX-3) — Inteligencia de Mercado Tatica ULTRA-PROFUNDA.
SUA MISSAO: VARREDURA COMPLETA E EXAUSTIVA. ZERO LIMITES. PRECISAO > CUSTO.

DIRETRIZES DE COMBATE (MODO AGRESSIVO):
1. BUSQUE EM MÚLTIPLAS FONTES: Sites oficiais, notícias, LinkedIn, vagas de emprego, relatórios públicos, CVM, B3.
2. NÃO LIMITE A BUSCA: Se encontrou 5 notícias, busque mais 10. Se achou 3 decisores, procure mais 7.
3. CRUZE INFORMAÇÕES: Valide dados em múltiplas fontes. Se houver discordância, reporte ambas.
4. SEJA ESPECÍFICO: Não diga "grande produtor". Diga "230.000 hectares em MT e MA".
5. INCLUA FONTES: Sempre que possível, mencione de onde veio a informação.
6. VÁ FUNDO: Procure balanços, DRE, relatórios de sustentabilidade, apresentações institucionais em PDF.

TOM DE VOZ: Militar, Objetivo, Preciso, Sem enrolacao.
"""

# === BASE DE CONHECIMENTO (SENIOR / GATEC) ===
PORTFOLIO_SENIOR = """
=== ARSENAL SENIOR SISTEMAS + GATEC ===
A Senior Sistemas oferece a suite completa "Farm-to-Fork" via parceria GAtec:

1. GATEC (OPERACIONAL / CAMPO):
- SimpleFarm: O "ERP do Campo". Planejamento de safra, custos por talhão, gestão de insumos.
- SimpleViewer: Cockpit de BI Agrícola.
- Operis: Gestão de Pátios e Armazens (Silos).
- Mapfy: Agricultura de precisão e mapas.

2. SENIOR ERP (BACKOFFICE / CORPORATIVO):
- ERP Gestão Empresarial: O Core. Financeiro, Contábil, Fiscal (Compliance nativo Brasil).
- Diferencial: Compliance fiscal nativo (SPED, Funrural, LCDPR) vs SAP/Oracle (que precisam de localização).

3. SENIOR HCM (PESSOAS):
- Folha, Ponto (com regras rurais NR-31), SST.
- Diferencial: eSocial nativo e gestão de safra/turnos.

4. SENIOR LOGÍSTICA & CRM:
- WMS (Armazém), TMS (Transporte).
- CRM Senior X: Pipeline de vendas e relacionamento.

ARGUMENTOS DE ATAQUE (FOX-3):
- "A única plataforma que conecta o Talhão (GAtec) ao Balanço (Senior) sem gambiarras."
- "SAP é caro e rígido. Senior é flexível e compliance Brasil nativo."
- "Totvs é colcha de retalhos (sistemas comprados que não se falam). Senior + GAtec é integração nativa."
"""


def _clean_json(text):
    """Limpa o output do Gemini para garantir JSON válido."""
    if not text: return None
    try:
        m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if m: return json.loads(m.group(1))
    except: pass
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m: return json.loads(m.group(0))
    except: pass
    try: return json.loads(text.replace('```json','').replace('```','').strip())
    except: return None

def _call(client, prompt, config, prio=Priority.NORMAL):
    """Executa a chamada ao Gemini via fila de prioridade."""
    def _do():
        return client.models.generate_content(model=MODEL, contents=prompt, config=config).text
    try: return request_queue.execute(_do, priority=prio)
    except Exception as e:
        print(f"❌ ERRO GEMINI: {e}")
        return None


# ==============================================================================
# AGENTE 1: RECON OPERACIONAL (ULTRA-PROFUNDO)
# ==============================================================================
def agent_recon_operacional(client, empresa):
    ck = {"a":"recon_v5_ultra","e":empresa}
    c = cache.get("recon", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO OPERACIONAL ULTRA-PROFUNDO (DEEP SCAN MÁXIMO).
ALVO: "{empresa}"

INSTRUCOES DETALHADAS:

1. BUSQUE EM MÚLTIPLAS FONTES:
   - Site oficial da empresa
   - Relatórios de sustentabilidade (PDF)
   - Notícias de expansão/aquisições dos últimos 3 anos
   - Entrevistas com executivos
   - LinkedIn da empresa
   - Páginas institucionais

2. IDENTIFIQUE O GRUPO ECONÔMICO:
   - Se a empresa for filial, identifique a HOLDING MÃE
   - Busque por "Grupo [Nome]" ou "[Nome] Participações"
   - Procure por "quem somos" / "institucional"

3. MAPEIE TODAS AS OPERAÇÕES:
   - Liste TODAS as fazendas/unidades (nome, cidade, UF, hectares)
   - Some TUDO para obter hectares_total
   - Identifique TODAS as culturas (não só principais)

4. IDENTIFIQUE INFRAESTRUTURA:
   - Silos próprios? Quantos? Capacidade?
   - Algodoeira? Usina? Indústria?
   - Frota própria? Portos/terminais?

5. TECNOLOGIAS EM USO:
   - Procure por "tecnologia", "digitalização", "agricultura de precisão"
   - Busque vagas de emprego que mencionem sistemas (JDLink, Climate FieldView, SAP, etc.)

6. PECUARIA (SE APLICÁVEL):
   - Cabeças de gado, aves, suínos
   - Sistemas de confina mento/integração

7. ÁREAS ESPECIAIS:
   - Área irrigada (pivôs)
   - Área florestal (eucalipto, teca)
   - Reserva legal

RETORNE JSON COMPLETO (sem omitir nada):
{{
  "nome_grupo": "Nome OFICIAL do grupo/holding",
  "hectares_total": 0,
  "culturas": ["Lista COMPLETA de culturas"],
  "verticalizacao": {{
    "industria": false,
    "logistica": false,
    "comercializacao": false,
    "pecuaria": false,
    "florestal": false,
    "algodoeira": false,
    "usina_cana": false,
    "silos": false,
    "porto_terminal": false,
    "trading": false
  }},
  "regioes_atuacao": ["Estados onde atua"],
  "numero_fazendas": 0,
  "fazendas_detalhadas": [
    {{"nome": "", "cidade": "", "uf": "", "hectares": 0, "culturas": []}}
  ],
  "tecnologias_identificadas": ["TODOS os sistemas/tecnologias encontrados"],
  "cabecas_gado": 0,
  "cabecas_aves": 0,
  "cabecas_suinos": 0,
  "area_florestal_ha": 0,
  "area_irrigada_ha": 0,
  "confianca": 0.9
}}

LEMBRETE: PRECISAO > CUSTO. Faça quantas buscas forem necessárias.
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"nome_grupo":empresa,"confianca":0.0}
    cache.set("recon", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 2: SNIPER FINANCEIRO (ULTRA-PROFUNDO)
# ==============================================================================
def agent_sniper_financeiro(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"fin_v5_ultra","e":alvo}
    c = cache.get("fin", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RASTREAMENTO FINANCEIRO E GOVERNANCA ULTRA-PROFUNDO.
ALVO: "{alvo}"

PROTOCOLO "FOLLOW THE MONEY" (VERSÃO COMPLETA):

1. BUSQUE BALANCOS E DEMONSTRATIVOS:
   - Site de Relação com Investidores (se listada)
   - Relatórios anuais PDF
   - Apresentações institucionais
   - Notícias sobre resultados financeiros

2. RASTREIE EMISSÕES (CRA, FIAGRO, DEBENTURES):
   - Busque no site da CVM (Comissão de Valores Mobiliários)
   - Notícias sobre "emissão de CRA [empresa]"
   - FIAgros que mencionam a empresa

3. IDENTIFIQUE PARCEIROS FINANCEIROS:
   - Bancos que financiam (Rabobank, Santander, BB, Sicoob, etc.)
   - Notícias sobre "financiamento [empresa]"
   - Contratos de crédito rural

4. AUDITORIAS E GOVERNANCA:
   - Busque por "auditoria independente [empresa]"
   - KPMG, Deloitte, PwC, EY?
   - Comitês de auditoria, conselhos?

5. MOVIMENTACOES RECENTES (M&A, EXPANSAO):
   - Aquisições de terras nos últimos 2 anos
   - Compra/venda de ativos
   - Fusões
   - Investimentos em novas unidades

6. ESTIMATIVAS:
   - Se não achar balanço, estime baseado em: hectares x produtividade x preço
   - Funcionários: busque no LinkedIn quantos funcionários listam a empresa

RETORNE JSON COMPLETO:
{{
  "capital_social_estimado": 0,
  "faturamento_estimado": 0,
  "funcionarios_estimados": 0,
  "movimentos_financeiros": [
    "Lista TODAS as movimentações encontradas (com datas e valores)"
  ],
  "fiagros_relacionados": ["Todos os FIAgros encontrados"],
  "cras_emitidos": ["Todos os CRAs com valores e datas"],
  "parceiros_financeiros": ["Todos os bancos/instituições"],
  "auditorias": ["Auditorias externas identificadas"],
  "governanca_corporativa": false,
  "resumo_financeiro": "Parágrafo detalhado sobre saúde financeira",
  "confianca": 0.9
}}
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("fin", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 3: GRUPO ECONÔMICO (ULTRA-PROFUNDO)
# ==============================================================================
def agent_grupo_economico(client, empresa, cnpj_matriz=""):
    ck = {"a":"grupo_v5_ultra","e":empresa}
    c = cache.get("grupo", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: MAPEAR A TEIA CORPORATIVA COMPLETA (HOLDING, FILIAIS, COLIGADAS).
ALVO: "{empresa}" {f'(CNPJ Raiz: {cnpj_matriz})' if cnpj_matriz else ''}

PROCEDIMENTO DE VARREDURA EXAUSTIVA:

1. IDENTIFIQUE A HOLDING CONTROLADORA:
   - Busque por "[Nome] Participações S.A."
   - Procure em relatórios "estrutura acionária"
   - Site institucional > "quem somos" > "estrutura"

2. LISTE TODAS AS FILIAIS:
   - Busque "unidades [empresa]"
   - Procure por CNPJs relacionados
   - Notícias sobre novas unidades
   - Liste: CNPJ, cidade, UF, atividade principal

3. IDENTIFIQUE COLIGADAS:
   - Transportadoras do grupo
   - Tradings relacionadas
   - Empresas de insumos
   - Imobiliárias rurais
   - Consultorias

4. MAPEIE OS CONTROLADORES:
   - Pessoas físicas (sócios principais)
   - Outras empresas controladoras
   - Família controladora

5. CROSS-REFERENCE:
   - Se encontrar PF, busque outras empresas deles
   - Crie mapa de poder

RETORNE JSON COMPLETO:
{{
  "cnpj_matriz": "",
  "holding_controladora": "Nome da holding mãe",
  "cnpjs_filiais": [
    {{"cnpj": "", "razao_social": "", "cidade": "", "uf": "", "atividade": ""}}
  ],
  "cnpjs_coligadas": [
    {{"cnpj": "", "razao_social": "", "atividade": "", "relacionamento": ""}}
  ],
  "total_empresas": 0,
  "controladores": [
    {{"nome": "", "tipo": "PF|PJ", "participacao": "majoritario|minoritario"}}
  ],
  "mapa_societario": "Descrição da estrutura de controle",
  "confianca": 0.9
}}
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("grupo", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 4: CADEIA DE VALOR (ULTRA-PROFUNDO)
# ==============================================================================
def agent_cadeia_valor(client, empresa, dados_ops):
    ck = {"a":"cadeia_v5_ultra","e":empresa}
    c = cache.get("cadeia", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: POSICIONAMENTO COMPLETO NA CADEIA DE VALOR.
ALVO: "{empresa}"

MAPEIE TODA A CADEIA:

1. POSICAO NA CADEIA:
   - Produtor primário? Processador? Trading? Integração vertical?

2. CLIENTES PRINCIPAIS:
   - Para quem vendem? (Tradings, indústrias, exportação direta?)
   - Busque "parceria [empresa]" ou "contrato [empresa]"

3. FORNECEDORES PRINCIPAIS:
   - Quem fornece insumos? (Bayer, Syngenta, Yara, etc.)
   - Busque "fornecedor preferencial [empresa]"

4. PARCERIAS ESTRATEGICAS:
   - Joint ventures
   - Acordos de exclusividade
   - Programas de fidelidade

5. EXPORTACAO:
   - Empresa exporta? Para onde?
   - Busque "exportação [empresa]" ou "mercado externo"
   - China, Europa, Ásia?

6. CERTIFICACOES:
   - RTRS (soja responsável)
   - Rainforest Alliance
   - Bonsucro (cana)
   - RenovaBio
   - ISO 14001
   - Busque "certificações [empresa]"

RETORNE JSON COMPLETO:
{{
  "posicao_cadeia": "Descrição detalhada da posição",
  "clientes_principais": ["Lista COMPLETA de clientes identificados"],
  "fornecedores_principais": ["Lista COMPLETA de fornecedores"],
  "parcerias_estrategicas": ["Todas as parcerias"],
  "canais_venda": ["Como vendem: trading, direto, cooperativa, etc."],
  "integracao_vertical_nivel": "BAIXA|MEDIA|ALTA",
  "exporta": false,
  "mercados_exportacao": ["Países de destino"],
  "certificacoes": ["Todas as certificações"],
  "confianca": 0.9
}}
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("cadeia", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 5: INTEL MERCADO (ULTRA-PROFUNDO)
# ==============================================================================
def agent_intel_mercado(client, empresa, setor_info=""):
    ck = {"a":"intel_v5_ultra","e":empresa}
    c = cache.get("intel", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: SIGINT (SINAIS DE INTELIGENCIA) - ÚLTIMOS 24 MESES (ULTRA-PROFUNDO).
ALVO: "{empresa}"

RAST REIE TODOS OS SINAIS:

1. NOTICIAS RECENTES (24 MESES):
   - Busque "[empresa]" em sites de notícias do agro
   - Globo Rural, Canal Rural, Notícias Agrícolas, AgroLink
   - Liste TODAS as notícias relevantes (título, data, fonte, resumo)

2. SINAIS DE COMPRA (BUYING SIGNALS):
   - Investimentos anunciados
   - Expansão de área
   - Obras em andamento
   - Vagas abertas (indica crescimento)
   - Troca de sistemas/modernização

3. DORES E PROBLEMAS:
   - Prejuízos reportados
   - Problemas climáticos
   - Multas ambientais
   - Processos trabalhistas
   - Reclamações de funcionários (Glassdoor, Reclame Aqui)

4. OPORTUNIDADES:
   - Gaps que Senior/GAtec pode preencher
   - Problemas com ERP atual
   - Necessidade de integração

5. RISCOS:
   - End ividamento alto
   - Dependência de poucos clientes
   - Exposição cambial

6. CONCORRENTES:
   - Quem são os principais concorrentes da empresa?

7. TENDENCIAS DO SETOR:
   - O que está acontecendo no setor?

RETORNE JSON COMPLETO:
{{
  "noticias_recentes": [
    {{
      "titulo": "",
      "resumo": "",
      "data": "",
      "fonte": "",
      "relevancia": "alta|media|baixa"
    }}
  ],
  "sinais_compra": ["TODOS os sinais identificados"],
  "riscos": ["TODOS os riscos"],
  "oportunidades": ["TODAS as oportunidades para Senior/GAtec"],
  "dores_identificadas": ["TODAS as dores"],
  "concorrentes": ["Lista de concorrentes"],
  "tendencias_setor": ["Tendências relevantes"],
  "confianca": 0.9
}}
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.2)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("intel", ck, r, ttl=3600)
    return r


# ==============================================================================
# AGENTE 6: PROFILER DECISORES (ULTRA-PROFUNDO)
# ==============================================================================
def agent_profiler_decisores(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"decisores_v5_ultra","e":alvo}
    c = cache.get("decisores", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: HUMINT - MAPEAMENTO COMPLETO DE DECISORES.
ALVO: "{alvo}"

IDENTIFIQUE TODOS OS DECISORES:

1. C-LEVEL E DIRETORIA:
   - CEO / Presidente
   - CFO / Diretor Financeiro
   - CIO / Diretor de TI
   - COO / Diretor de Operações
   - Diretor Agrícola / Industrial
   - Controller

2. BUSQUE EM MÚLTIPLAS FONTES:
   - LinkedIn: busque "[empresa] CEO", "[empresa] CFO", etc.
   - Site oficial: página "equipe" ou "diretoria"
   - Notícias: entrevistas com executivos
   - Relatórios anuais: mensagem da diretoria

3. PARA CADA DECISOR, COLETE:
   - Nome completo
   - Cargo
   - LinkedIn (URL completo)
   - Email (se disponível ou estime: nome.sobrenome@empresa.com.br)
   - Formação acadêmica
   - Histórico profissional (empresas anteriores)
   - Perfil decisório (técnico, conservador, inovador, etc.)

4. ESTRUTURA DE DECISAO:
   - É família? Profissional? Mista?
   - Quem tem poder de veto em tecnologia?

RETORNE JSON COMPLETO:
{{
  "decisores": [
    {{
      "nome": "",
      "cargo": "",
      "linkedin": "",
      "email": "",
      "formacao": "",
      "experiencia": "",
      "relevancia_erp": "ALTA|MEDIA|BAIXA",
      "perfil_decisorio": "conservador|inovador|analitico|etc"
    }}
  ],
  "estrutura_decisao": "FAMILIAR|PROFISSIONAL|MISTA",
  "influenciadores": ["Pessoas que influenciam decisões mas não estão no C-level"],
  "confianca": 0.9
}}
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"decisores":[],"confianca":0.0}
    cache.set("decisores", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 7: TECH STACK (ULTRA-PROFUNDO)
# ==============================================================================
def agent_tech_stack(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"tech_v5_ultra","e":alvo}
    c = cache.get("tech", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO COMPLETO DE SISTEMAS (TECH INTEL ULTRA-PROFUNDO).
ALVO: "{alvo}"

DESCUBRA TUDO QUE ELES USAM:

1. ERP PRINCIPAL:
   - Busque vagas de emprego: "[empresa] + vaga + SAP|TOTVS|Senior|Oracle"
   - LinkedIn: funcionários listam sistemas que usam
   - Notícias: "[empresa] + implanta + ERP"
   - Reclamações: Glassdoor, Reclame Aqui (problemas com sistemas)

2. SISTEMAS DE CAMPO:
   - JDLink (John Deere)
   - Climate FieldView
   - Solinftec
   - Agrímetrics
   - Outros

3. OUTROS SISTEMAS:
   - WMS (logística)
   - TMS (transporte)
   - CRM
   - BI (Power BI, Tableau, Qlik)
   - Contábil/fiscal

4. VAGAS DE TI ABERTAS:
   - LinkedIn Jobs: "[empresa]"
   - Indeed, Catho, Gupy
   - Liste TODAS as vagas de TI e sistemas mencionados

5. NIVEL DE MATURIDADE TI:
   - Baseado nos sistemas, vagas e notícias:
   - BAIXO: Planilhas, sistemas básicos
   - MEDIO: ERP, mas sem integração campo
   - ALTO: ERP + Campo + BI integrado

RETORNE JSON COMPLETO:
{{
  "erp_principal": {{
    "sistema": "",
    "fornecedor": "",
    "versao": "",
    "modulos": [],
    "status": "em uso|em implantação|insatisfeito",
    "fonte_evidencia": ""
  }},
  "outros_sistemas": [
    {{
      "tipo": "campo|logistica|bi|etc",
      "sistema": "",
      "fornecedor": ""
    }}
  ],
  "vagas_ti_abertas": [
    {{
      "titulo": "",
      "link": "",
      "sistemas_mencionados": [],
      "data_publicacao": ""
    }}
  ],
  "nivel_maturidade_ti": "BAIXO|MEDIO|ALTO",
  "gaps_identificados": ["Sistemas que faltam ou problemas identificados"],
  "confianca": 0.9
}}
"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("tech", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 8: ANÁLISE ESTRATÉGICA (SEM MUDANÇAS)
# ==============================================================================
def agent_analise_estrategica(client, dados, sas, contexto=""):
    prompt = f"""{RADAR_IDENTITY}
VOCÊ É O OFICIAL DE INTELIGÊNCIA DO PROJETO RADAR.
GERAR RELATÓRIO DE MISSÃO (BDA).

=== DADOS DO ALVO ===
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:15000]}

=== SCORE SAS ===
Score: {sas.get('score',0)} — Tier: {sas.get('tier','N/D')}

{PORTFOLIO_SENIOR}

=== ESTRUTURA DO RELATÓRIO (Markdown, separe com |||) ===

SEÇÃO 1 — RECONHECIMENTO DO ALVO (SITUATION REPORT):
- Visão Raio-X: Tamanho, produção, quem manda.
- STATUS: "ALVO PRIORITÁRIO" (>5k ha) ou "ALVO TÁTICO".

SEÇÃO 2 — ANÁLISE DE VULNERABILIDADES:
- Dores (Logística? Fiscal?).
- Problemas com atual ERP (TOTVS/SAP).

SEÇÃO 3 — ARSENAL RECOMENDADO:
- Soluções Senior + GAtec específicas.
- Argumento Matador.

SEÇÃO 4 — PLANO DE VOO:
- Quem abordar? Qual a isca? Red Flags.
"""
    cfg = types.GenerateContentConfig(temperature=0.4)
    return _call(client, prompt, cfg, Priority.CRITICAL) or "FALHA NA GERAÇÃO DA ANÁLISE."


# ==============================================================================
# AGENTE 9: AUDITOR DE QUALIDADE (SEM MUDANÇAS)
# ==============================================================================
def agent_auditor_qualidade(client, texto, dados):
    prompt = f"""{RADAR_IDENTITY}
MISSAO: DEBRIEFING E CONTROLE DE QUALIDADE.

Avalie (0-10): PRECISÃO, TÁTICA, FIT SENIOR.

Retorne JSON:
{{"scores":{{"precisao":{{"nota":0,"justificativa":""}},"acionabilidade":{{"nota":0,"justificativa":""}},"fit_senior":{{"nota":0,"justificativa":""}}}},"nota_final":0.0,"nivel":"EXCELENTE|BOM|ACEITAVEL|INSUFICIENTE","recomendacoes":[]}}"""
    
    cfg = types.GenerateContentConfig(temperature=0.2)
    return _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"nota_final":0,"nivel":"INSUFICIENTE","recomendacoes":["Erro"]}


# ==============================================================================
# UTILITÁRIO: BUSCA CNPJ (SEM MUDANÇAS)
# ==============================================================================
def buscar_cnpj_por_nome(client, nome):
    ck = {"b":nome}
    c = cache.get("bcnpj", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: LOCALIZAR CNPJ MATRIZ. ALVO: "{nome}".
Priorize Holdings. Retorne APENAS CNPJ ou "NAO_ENCONTRADO"."""
    
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.0)
    text = _call(client, prompt, cfg, Priority.HIGH)
    if text:
        m = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', text)
        if m:
            cnpj = m.group(0)
            cache.set("bcnpj", ck, cnpj, ttl=86400)
            return cnpj
    return None
