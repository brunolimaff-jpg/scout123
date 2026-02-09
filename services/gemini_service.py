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

# Configuração do Modelo (Use flash para velocidade ou pro para raciocínio complexo)
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
    # Tenta extrair bloco JSON markdown
    try:
        m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if m: return json.loads(m.group(1))
    except: pass
    
    # Tenta encontrar o primeiro { e o último }
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m: return json.loads(m.group(0))
    except: pass
    
    # Tenta limpeza bruta
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
# AGENTE 1: RECON OPERACIONAL (MAPEAMENTO DE TERRENO)
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
   - Se encontrar dados antigos, faça uma projeção conservadora e avise.
3. Culturas (Mix de Produção): Soja, Milho, Algodão, Cana, Pecuária (nº cabeças).
4. Infraestrutura Vertical (ASSETS):
   - Possui Armazéns/Silos próprios? (Indício de dor em Logística).
   - Possui Algodoeira? Usina? Frigorífico? Fábrica de Ração?
   - Possui Frota Própria? (Indício de dor em Manutenção).
5. Tecnologia Atual:
   - Menciona uso de SAP, TOTVS, JDLink, Climate FieldView, Solinftec?
   - Tem conectividade no campo?

ALERTA DE TAMANHO:
- NÃO DESCARTE NADA. Apenas registre a área.
- Se < 5.000 ha, marque "perfil_farming" = "SMB" (Small/Medium).
- Se > 5.000 ha, marque "perfil_farming" = "ENTERPRISE".

Retorne JSON:
{{"nome_grupo":"","hectares_total":0,"culturas":[],"verticalizacao":{{}},"regioes_atuacao":[],"numero_fazendas":0,"cabecas_gado":0,"tecnologias_identificadas":[],"perfil_farming":"ENTERPRISE|SMB","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(
        tools=[SEARCH], 
        temperature=0.1, 
        thinking_config=types.ThinkingConfig(thinking_budget=2048) # Thinking rápido
    )
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"nome_grupo":empresa,"confianca":0.0}
    cache.set("recon", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 2: SNIPER FINANCEIRO (RASTREIO DE DINHEIRO)
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
   - CRAs revelam o tamanho real da dívida e da operação.
3. Identifique Auditorias Externas (KPMG, Deloitte, PwC, EY).
   - Se tem Big 4, tem governança para comprar ERP Tier 1.
4. M&A e Expansão: Notícias de fusões, compras de terras ou novas unidades.

ESTIMATIVAS (Se não houver balanço público):
- Use Capital Social (Receita Federal) como piso.
- Estime Faturamento base: ~R$ 5.000 a R$ 10.000 por hectare (grãos) ou compare com pares.

Retorne JSON:
{{"capital_social_estimado":0,"faturamento_estimado":0,"origem_faturamento":"balanco_publico|estimativa_mercado|modelo_ia","movimentos_financeiros":[],"cras_emitidos":[],"auditorias":[],"governanca_corporativa":false,"resumo_financeiro":"","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("fin", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 3: GRUPO ECONÔMICO (A TEIA CORPORATIVA)
# ==============================================================================
def agent_grupo_economico(client, empresa, cnpj_matriz=""):
    ck = {"a":"grupo_v4","e":empresa}
    c = cache.get("grupo", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: MAPEAR A TEIA CORPORATIVA (HOLDING & FILIAIS).
ALVO: "{empresa}" {f'(CNPJ Raiz: {cnpj_matriz})' if cnpj_matriz else ''}

PROCEDIMENTO DE VARREDURA:
1. Identifique a HOLDING CONTROLADORA (A "Mãe"). Muitas vezes é uma S.A. ou Ltda com nome dos sócios.
2. Liste as FILIAIS OPERACIONAIS (CNPJs produtivos).
3. Busque COLIGADAS: Transportadoras do grupo, Tradings do grupo, Imobiliárias rurais.
4. CROSS-CHECK DE SÓCIOS:
   - Se os sócios são Pessoas Físicas (PF), busque "Sócio X + Agro" ou "Sócio X + Fazenda".
   - Muitas vezes o produtor tem vários CNPJs separados que formam um império invisível. Descubra isso.

Retorne JSON:
{{"cnpj_matriz":"","holding_controladora":"","filiais":[{{"cnpj":"","cidade":"","uf":"","atividade":""}}],"coligadas":[{{"razao_social":"","atividade":""}}],"total_empresas":0,"controladores":[],"confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("grupo", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 4: CADEIA DE VALOR (ONDE ELES ESTÃO)
# ==============================================================================
def agent_cadeia_valor(client, empresa, dados_ops):
    ck = {"a":"cadeia_v4","e":empresa}
    c = cache.get("cadeia", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: POSICIONAMENTO NA CADEIA DE VALOR.
ALVO: "{empresa}"

DETERMINE:
1. Grau de Verticalização: Eles só plantam (Baixo)? Eles armazenam (Médio)? Eles industrializam/vendem varejo (Alto)?
   - Verticalização Alta = Alta aderência para Senior (Indústria + Varejo).
2. Exportação: Eles têm "Habilitação Exportadora"? Vendem direto para China/Europa?
   - Se sim, precisam de Compliance Fiscal robusto (Ponto para Senior).
3. Certificações: RTRS, Bonsucro, RenovaBio?
   - Exige rastreabilidade (Ponto para GAtec).

Retorne JSON:
{{"posicao_cadeia":"","integracao_vertical_nivel":"BAIXA|MEDIA|ALTA","exporta":false,"mercados_exportacao":[],"certificacoes":[],"confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("cadeia", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 5: INTEL MERCADO (SINAIS DE FUMAÇA)
# ==============================================================================
def agent_intel_mercado(client, empresa, setor_info=""):
    ck = {"a":"intel_v4","e":empresa}
    c = cache.get("intel", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: SIGINT (SINAIS DE INTELIGÊNCIA) - ÚLTIMOS 12 MESES.
ALVO: "{empresa}"

RASTREIE SINAIS TÁTICOS PARA VENDAS:
1. SINAL DE DOR: Notícias de prejuízo, problemas climáticos, multas ambientais?
2. SINAL DE COMPRA: Anúncio de investimento, construção de nova fábrica, aquisição de terras?
   - "Empresa X investirá R$ 100mi em nova unidade" = OPORTUNIDADE ERP.
3. SINAL DE GESTÃO: Troca de CEO/CFO? Profissionalização da gestão familiar?
   - Novo CFO geralmente quer trocar o ERP antigo.

Retorne JSON:
{{"noticias_recentes":[{{"titulo":"","resumo":"","data_aprox":"","relevancia":"alta"}}],"sinais_compra":[],"riscos":[],"oportunidades":[],"dores_identificadas":[],"confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.2)
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("intel", ck, r, ttl=3600)
    return r


# ==============================================================================
# AGENTE 6: PROFILER DECISORES (QUEM MANDA)
# ==============================================================================
def agent_profiler_decisores(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"decisores_v4","e":alvo}
    c = cache.get("decisores", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: HUMINT (HUMAN INTELLIGENCE) - QUEM SÃO OS ALVOS.
ALVO: "{alvo}"

IDENTIFIQUE O "CIRCLE OF INFLUENCE":
1. O CHEFE (Dono/CEO): Geralmente a família fundadora.
2. O GUARDIÃO DO COFRE (CFO/Controller): O alvo principal para vender ERP Senior.
3. O TECNÓLOGO (CIO/TI): O influenciador técnico.
4. O OPERADOR (Diretor Agrícola/Industrial): O usuário da GAtec.

Busque LinkedIn e notícias. Se for gestão familiar, identifique a "Segunda Geração" (filhos assumindo), pois eles são mais abertos a tecnologia.

Retorne JSON:
{{"decisores":[{{"nome":"","cargo":"","linkedin":"","relevancia_erp":"ALTA|MEDIA|BAIXA","perfil_comportamental":""}}],"estrutura_decisao":"FAMILIAR|PROFISSIONAL|MISTA","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"decisores":[],"confianca":0.0}
    cache.set("decisores", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 7: TECH STACK (O INIMIGO ATUAL)
# ==============================================================================
def agent_tech_stack(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"tech_v4","e":alvo}
    c = cache.get("tech", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO DE SISTEMAS (TECH INTEL).
ALVO: "{alvo}"

DESCUBRA O QUE ELES USAM HOJE (PARA SUBSTITUIRMOS):
1. Procure vagas de emprego da empresa. Elas dizem "Desejável conhecimento em Protheus", "SAP", "Excel avançado".
2. Se pedem "Excel Avançado" para Coordenador Financeiro, é SINAL DE DOR (falta de ERP).
3. Busque reclamações de sistemas ou notícias de implantação.

MAPA DE ALVOS (CONCORRENTES):
- TOTVS (Protheus/Datasul): Muito comum. Atacar com "Integração Nativa Agro" e "Cloud de verdade".
- SAP (B1/S4): Caro e rígido. Atacar com "Custo Total (TCO)" e "Tropicalização Brasil".
- SIAGRI: Bom no agro, fraco no backoffice. Atacar com "ERP Corporativo Robusto".

Retorne JSON:
{{"erp_principal":{{"sistema":"","versao":"","fonte_evidencia":""}},"outros_sistemas":[],"vagas_ti_abertas":[{{"titulo":"","sistemas_mencionados":[]}}],"nivel_maturidade_ti":"BAIXO|MEDIO|ALTO","confianca":0.0}}"""

    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("tech", ck, r, ttl=7200)
    return r


# ==============================================================================
# AGENTE 8: ANÁLISE ESTRATÉGICA (O PLANO DE VOO)
# ==============================================================================
def agent_analise_estrategica(client, dados, sas, contexto=""):
    prompt = f"""{RADAR_IDENTITY}

VOCÊ É O OFICIAL DE INTELIGÊNCIA DO PROJETO RADAR.
GERAR RELATÓRIO DE MISSÃO (BDA - Battle Damage Assessment).

=== DADOS DO ALVO ===
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:15000]}

=== SCORE SAS ===
Score Tático: {sas.get('score',0)}/1000 — Classificação: {sas.get('tier','N/D')}

{PORTFOLIO_SENIOR}

=== ESTRUTURA DO RELATÓRIO RADAR (Separe seções com |||) ===

SEÇÃO 1 — RECONHECIMENTO DO ALVO (SITUATION REPORT):
- Visão Raio-X: Quem são, tamanho real (ha), o que produzem.
- Estrutura de Poder: Quem manda? Família ou Executivos? Holding ou Isolado?
- STATUS: Se > 5.000 ha, declare "ALVO PRIORITÁRIO (HIGH TICKET)". Se menor, "ALVO TÁTICO".

SEÇÃO 2 — ANÁLISE DE VULNERABILIDADES (PAIN POINTS):
- Onde eles estão sangrando? (Logística? Fiscal? Planilhas?)
- Se usam TOTVS/SAP: Quais as dores comuns desses sistemas que a Senior resolve?
- Se tem auditoria/CRA: A dor é Compliance e Governança (Senior brilha aqui).

SEÇÃO 3 — ARSENAL RECOMENDADO (SENIOR + GATEC):
- Monte o "Loadout" ideal. Ex: "Vender SimpleFarm para o campo + ERP Senior para a Holding + HCM para a folha da safra".
- Argumento Matador: Uma frase para o Hunter falar no telefone que vai travar a atenção do CEO.

SEÇÃO 4 — PLANO DE VOO (ACTION PLAN):
- Quem abordar primeiro? (O CFO ou o Agrônomo?)
- Qual a "Isca"? (RenovaBio? Compliance Fiscal? Custo de Frota?)
- Red Flags: O que pode derrubar a venda?

REGRAS:
- SEJA TÁTICO E DIRETO. Linguagem de Briefing Militar.
- Use Markdown.
- Separe as seções com "|||".
"""
    # Thinking budget alto para cruzar todas as infos
    cfg = types.GenerateContentConfig(temperature=0.4, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    return _call(client, prompt, cfg, Priority.CRITICAL) or "FALHA NA GERAÇÃO DA ANÁLISE."


# ==============================================================================
# UTILITÁRIO: BUSCA CNPJ
# ==============================================================================
def buscar_cnpj_por_nome(client, nome):
    ck = {"b":nome}
    c = cache.get("bcnpj", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: LOCALIZAR CNPJ MATRIZ.
ALVO: "{nome}" (Agronegócio Brasil).
Priorize CNPJs de Holdings, Matrizes ou S.A.
Retorne APENAS o CNPJ (formato XX.XXX.XXX/XXXX-XX) ou "NAO_ENCONTRADO"."""
    
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.0)
    text = _call(client, prompt, cfg, Priority.HIGH)
    if text:
        m = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', text)
        if m:
            cnpj = m.group(0)
            cache.set("bcnpj", ck, cnpj, ttl=86400)
            return cnpj
    return None
