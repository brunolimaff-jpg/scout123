"""
services/gemini_service.py — RADAR Intelligence Engine (Protocol FOX-3)
Motor IA com 9 Agentes Especializados em Deep Discovery
Identidade: RADAR AWACS (substitui Raptor/Sara)
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
RADAR_IDENTITY = """VOCE E O SISTEMA RADAR (PROTOCOLO FOX-3) — Inteligencia de Mercado Tatica para Agronegocio.
SUA MISSAO: VARREDURA COMPLETA E PROFUNDA.
ALVO: Grandes Grupos, Holdings e Produtores Rurais.

DIRETRIZES DE COMBATE:
1. NÃO FILTRE NADA AGORA. Mapeie tudo, independente do tamanho. Deixe o operador decidir.
2. BUSQUE A "BIG PICTURE": Não olhe apenas o CNPJ alvo. Procure a Holding, o Grupo Econômico, a Matriz.
3. RASTREIE O DINHEIRO: Procure balanços consolidados, CRAs, Fiagros e RI (Relação com Investidores).
4. TOM DE VOZ: Militar, Controladoria de Voo, Direto, Executivo.
   - Use termos como: "Visual confirmado", "Alvo travado", "Estrutura identificada".
   - Sem saudações. Apenas dados.
"""

# Alias para retrocompatibilidade
RAPTOR_IDENTITY = RADAR_IDENTITY 

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
# AGENTE 1: RECON OPERACIONAL
# ==============================================================================
def agent_recon_operacional(client, empresa):
    ck = {"a":"recon_v4","e":empresa}
    c = cache.get("recon", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO OPERACIONAL PROFUNDO (DEEP SCAN).
ALVO: "{empresa}"

INSTRUCOES ESPECIAIS (CAÇA A HOLDING):
- Não se limite ao site comercial. Procure por "Relatório de Sustentabilidade", "Demonstrações Financeiras", "Apresentação Institucional PDF".
- Se a empresa for uma filial, descubra quem é o GRUPO MÃE.

EXTRAIA COM PRECISÃO DE SNIPER:
1. Nome OFICIAL do Grupo Econômico (Holding).
2. Área TOTAL em Hectares (Some todas as unidades/fazendas).
3. Culturas (Mix de Produção): Soja, Milho, Algodão, Cana, Pecuária (nº cabeças).
4. Infraestrutura Vertical (ASSETS): Silos, Algodoeira, Usina, Frota Própria.
5. Tecnologia Atual: SAP, TOTVS, JDLink, Climate FieldView, Solinftec?

Retorne JSON:
{{"nome_grupo":"","hectares_total":0,"culturas":[],"verticalizacao":{{}},"regioes_atuacao":[],"numero_fazendas":0,"cabecas_gado":0,"tecnologias_identificadas":[],"perfil_farming":"ENTERPRISE|SMB","confianca":0.0}}"""

    # REMOVIDO thinking_config para evitar erro 400
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"nome_grupo":empresa,"confianca":0.0}
    cache.set("recon", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 2: SNIPER FINANCEIRO
# ==============================================================================
def agent_sniper_financeiro(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"fin_v4","e":alvo}
    c = cache.get("fin", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RASTREAMENTO FINANCEIRO E GOVERNANÇA.
ALVO: "{alvo}" (Investigue também variações e CNPJ raiz).

EXECUTE O PROTOCOLO "FOLLOW THE MONEY":
1. Busque por "Relação com Investidores (RI)", "Central de Resultados", "Balanço Patrimonial".
2. Busque por emissões de CRA (Certificado de Recebíveis do Agronegócio) na CVM ou B3.
3. Identifique Auditorias Externas (KPMG, Deloitte, PwC, EY).
4. M&A e Expansão: Notícias de fusões, compras de terras ou novas unidades.

Retorne JSON:
{{"capital_social_estimado":0,"faturamento_estimado":0,"origem_faturamento":"balanco_publico|estimativa_mercado|modelo_ia","movimentos_financeiros":[],"cras_emitidos":[],"auditorias":[],"governanca_corporativa":false,"resumo_financeiro":"","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("fin", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 3: GRUPO ECONÔMICO
# ==============================================================================
def agent_grupo_economico(client, empresa, cnpj_matriz=""):
    ck = {"a":"grupo_v4","e":empresa}
    c = cache.get("grupo", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: MAPEAR A TEIA CORPORATIVA (HOLDING & FILIAIS).
ALVO: "{empresa}" {f'(CNPJ Raiz: {cnpj_matriz})' if cnpj_matriz else ''}

PROCEDIMENTO DE VARREDURA:
1. Identifique a HOLDING CONTROLADORA (A "Mãe").
2. Liste as FILIAIS OPERACIONAIS.
3. Busque COLIGADAS: Transportadoras, Tradings, Imobiliárias.
4. CROSS-CHECK DE SÓCIOS: Se PF, busque outras empresas deles.

Retorne JSON:
{{"cnpj_matriz":"","holding_controladora":"","filiais":[{{"cnpj":"","cidade":"","uf":"","atividade":""}}],"coligadas":[{{"razao_social":"","atividade":""}}],"total_empresas":0,"controladores":[],"confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("grupo", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 4: CADEIA DE VALOR
# ==============================================================================
def agent_cadeia_valor(client, empresa, dados_ops):
    ck = {"a":"cadeia_v4","e":empresa}
    c = cache.get("cadeia", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: POSICIONAMENTO NA CADEIA DE VALOR.
ALVO: "{empresa}"

DETERMINE:
1. Grau de Verticalização (Baixo/Médio/Alto).
2. Exportação (Habilitação, Mercados).
3. Certificações (RTRS, Bonsucro, RenovaBio).

Retorne JSON:
{{"posicao_cadeia":"","integracao_vertical_nivel":"BAIXA|MEDIA|ALTA","exporta":false,"mercados_exportacao":[],"certificacoes":[],"confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("cadeia", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 5: INTEL MERCADO
# ==============================================================================
def agent_intel_mercado(client, empresa, setor_info=""):
    ck = {"a":"intel_v4","e":empresa}
    c = cache.get("intel", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: SIGINT (SINAIS DE INTELIGÊNCIA) - ÚLTIMOS 12 MESES.
ALVO: "{empresa}"

RASTREIE SINAIS TÁTICOS:
1. SINAL DE DOR (Prejuízo, Clima, Multas).
2. SINAL DE COMPRA (Investimento, Obras, Aquisições).
3. SINAL DE GESTÃO (Troca de Diretoria).

Retorne JSON:
{{"noticias_recentes":[{{"titulo":"","resumo":"","data_aprox":"","relevancia":"alta"}}],"sinais_compra":[],"riscos":[],"oportunidades":[],"dores_identificadas":[],"confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.2)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("intel", ck, r, ttl=3600)
    return r


# ==============================================================================
# AGENTE 6: PROFILER DECISORES
# ==============================================================================
def agent_profiler_decisores(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"decisores_v4","e":alvo}
    c = cache.get("decisores", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: HUMINT - QUEM SÃO OS ALVOS.
ALVO: "{alvo}"

IDENTIFIQUE:
1. O CHEFE (Dono/CEO).
2. O GUARDIÃO DO COFRE (CFO/Controller).
3. O TECNÓLOGO (CIO/TI).
4. O OPERADOR (Diretor Agrícola/Industrial).

Retorne JSON:
{{"decisores":[{{"nome":"","cargo":"","linkedin":"","relevancia_erp":"ALTA|MEDIA|BAIXA","perfil_comportamental":""}}],"estrutura_decisao":"FAMILIAR|PROFISSIONAL|MISTA","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"decisores":[],"confianca":0.0}
    cache.set("decisores", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 7: TECH STACK
# ==============================================================================
def agent_tech_stack(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"tech_v4","e":alvo}
    c = cache.get("tech", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO DE SISTEMAS (TECH INTEL).
ALVO: "{alvo}"

DESCUBRA O QUE ELES USAM HOJE:
1. Vagas de emprego (pedem Protheus? SAP?).
2. Notícias de implantação.
3. Reclamações.

Retorne JSON:
{{"erp_principal":{{"sistema":"","versao":"","fonte_evidencia":""}},"outros_sistemas":[],"vagas_ti_abertas":[{{"titulo":"","sistemas_mencionados":[]}}],"nivel_maturidade_ti":"BAIXO|MEDIO|ALTO","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("tech", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 8: ANÁLISE ESTRATÉGICA
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
    # Removido thinking config aqui também
    cfg = types.GenerateContentConfig(temperature=0.4)
    return _call(client, prompt, cfg, Priority.CRITICAL) or "FALHA NA GERAÇÃO DA ANÁLISE."


# ==============================================================================
# AGENTE 9: AUDITOR DE QUALIDADE
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
# UTILITÁRIO: BUSCA CNPJ
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
