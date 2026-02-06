"""
services/gemini_service.py — Motor IA v3.2 (ALL Pro, 9 Agents)
Inclui: Profiler Decisores, Tech Stack Hunter, Portfolio Senior/Gatec
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import json, re, time
from typing import Optional, Any
from google import genai
from google.genai import types
from services.cache_service import cache
from services.request_queue import request_queue, Priority

MODEL = "gemini-2.5-pro"
SEARCH = types.Tool(google_search=types.GoogleSearch())

# === PORTFOLIO SENIOR/GATEC (injetado nos prompts sem custo de API) ===
PORTFOLIO_SENIOR = """
=== PORTFOLIO SENIOR SISTEMAS + GATEC (by Senior) ===
A Senior Sistemas oferece suite completa para agro via parceria com GAtec:

GATEC PRODUTOS (Especializados Agro):
- SimpleFarm: Gestao Agricola completa (planejamento safra, custos por talhao, controle de insumos, 
  gestao automotiva/frota, manutencao industrial, originacao, logistica, processo industrial/beneficiamento, custos gerenciais)
- SimpleViewer: BI Agricola com dashboards operacionais e gerenciais
- Operis: Gestao de Armazens e Patios (recebimento, classificacao, expedicao)
- CommerceSF: Comercializacao de commodities (compra, venda, contratos, hedge, barter, CPR)
- CommerceLog: Logistica de transporte (frete, romaneio, balanca, rastreamento)
- Mapfy: Mapas dinamicos, agricultura de precisao, monitoramento satelital

SENIOR ERP (Backoffice Corporativo):
- ERP Gestao Empresarial: Financeiro, Contabil, Fiscal, Compras, Estoque
- Compliance Fiscal: SPED, REINF, eSocial, Funrural, ICMS diferido
- CRM Senior X: Gestao de relacionamento e vendas
- ERP Banking: Conciliacao bancaria, cobranca, pagamentos

SENIOR LOGISTICA:
- WMS: Gestao de Armazenagem (CD, silos, cameras frias)
- TMS: Gestao de Transportes (embarcador e transportador)
- YMS: Gestao de Patio (filas, docas, agendamento)
- Torre de Controle: Visibilidade end-to-end

SENIOR HCM (Gestao de Pessoas):
- Folha de Pagamento: eSocial nativo, calculo de Funrural
- Ponto Eletronico: Turnos de campo, sazonalidade, NR-31
- RH/DP: Admissao digital, SST, juridico
- Talent Management: LMS, desempenho, remuneracao, clima

SENIOR SEGURANCA:
- Controle de Acesso: Portarias de fazenda, biometria
- Gestao de Terceiros: Compliance de prestadores
- Security Hub: Monitoramento centralizado

SENIOR FLOW:
- BPM: Automacao de processos (aprovacoes, workflows)
- GED: Gestao eletronica de documentos
- SIGN: Assinatura digital de contratos

DIFERENCIAIS vs CONCORRENTES:
- UNICA plataforma que integra campo (SimpleFarm) + backoffice (ERP Senior) + pessoas (HCM) nativamente
- Cloud-first com deploy em 3-6 meses (vs 12-24 meses SAP)
- Custo 50-70% menor que SAP com funcionalidade equivalente
- eSocial e compliance fiscal brasileiro nativo (TOTVS adapta, Senior eh nativo)
- Gestao multi-empresa/multi-fazenda nativa (Siagri nao escala)
- Suporte em portugues com especialistas agro (SAP/Oracle = ingles)
"""


def _clean_json(text):
    if not text: return None
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m: return json.loads(m.group(0))
    except Exception: pass
    try: return json.loads(text.replace('```json','').replace('```','').strip())
    except Exception: return None

def _call(client, prompt, config, prio=Priority.NORMAL):
    def _do():
        return client.models.generate_content(model=MODEL, contents=prompt, config=config).text
    try: return request_queue.execute(_do, priority=prio)
    except Exception: return None


# =========================================================================
# AGENTE 1: RECON OPERACIONAL
# =========================================================================
def agent_recon_operacional(client, empresa):
    ck = {"a":"recon","e":empresa}
    c = cache.get("recon", ck)
    if c: return c
    prompt = f"""ATUE COMO: Investigador Agricola Senior com 20 anos de campo.
ALVO: "{empresa}"

Busque em MULTIPLAS fontes (site oficial, LinkedIn, noticias, Econodata, relatorios).

DESCUBRA COM PRECISAO:
1. Nome oficial do grupo economico
2. Area TOTAL em hectares (se faixa, use valor medio)
3. TODAS as culturas: graos, fibras, cana, cafe, citrus, HF, florestal, pecuaria, etc
4. TODA infraestrutura vertical (silos, armazens, algodoeira, usina, frigorifico, fabrica_racao, etc)
5. Regioes/estados de atuacao
6. Numero de fazendas/unidades
7. Pecuaria: cabecas de gado, aves, suinos (se aplicavel)
8. Area irrigada e area florestal (se aplicavel)
9. Tecnologias: agricultura de precisao, drones, ERP, telemetria

LISTA DE VERTICALIZACAO (marque true/false para CADA):
silos, armazens_gerais, terminal_portuario, ferrovia_propria, frota_propria,
algodoeira, sementeira, ubs, secador,
agroindustria, usina_acucar_etanol, destilaria, esmagadora_soja, refinaria_oleo,
fabrica_biodiesel, torrefacao_cafe, beneficiamento_arroz, fabrica_sucos, vinicultura,
frigorifico_bovino, frigorifico_aves, frigorifico_suinos, frigorifico_peixes,
laticinio, fabrica_racao, incubatorio,
fabrica_fertilizantes, fabrica_defensivos, laboratorio_genetica, central_inseminacao, viveiro_mudas,
cogeracao_energia, usina_solar, biodigestor, planta_biogas, creditos_carbono,
florestal_eucalipto, florestal_pinus, fabrica_celulose, serraria,
pivos_centrais, irrigacao_gotejamento, barragem_propria,
agricultura_precisao, drones_proprios, estacoes_meteorologicas, telemetria_frota, erp_implantado

REGRAS: Seja FACTUAL. Nao invente. Se nao encontrar = 0/false. Confianca 0.0 a 1.0.

Retorne APENAS JSON:
{{"nome_grupo":"","hectares_total":0,"culturas":[],"verticalizacao":{{}},"regioes_atuacao":[],"numero_fazendas":0,"cabecas_gado":0,"cabecas_aves":0,"cabecas_suinos":0,"area_florestal_ha":0,"area_irrigada_ha":0,"tecnologias_identificadas":[],"confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"nome_grupo":empresa,"confianca":0.0}
    cache.set("recon", ck, r, ttl=7200)
    return r


# =========================================================================
# AGENTE 2: SNIPER FINANCEIRO
# =========================================================================
def agent_sniper_financeiro(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"fin","e":alvo}
    c = cache.get("fin", ck)
    if c: return c
    prompt = f"""ATUE COMO: Analista Senior de Mercado de Capitais — Agro.
ALVO: "{alvo}" (pesquise tambem como "{empresa}")

VASCULHE A WEB COM PROFUNDIDADE:
1. CRA: valor, data, estruturador, rating, series
2. FIAGRO: fundos, gestoras, tickers
3. GOVERNANCA: auditoria Big 4, conselho, S.A./Ltda
4. M&A: fusoes, aquisicoes, parcerias
5. FINANCEIROS: capital social, faturamento, funcionarios (Econodata, Casa dos Dados, LinkedIn, RAIS)
6. PARCEIROS: bancos, gestoras, seguradoras
7. DIVIDA: debentures, BNDES, Plano Safra

Retorne APENAS JSON:
{{"capital_social_estimado":0,"funcionarios_estimados":0,"faturamento_estimado":0,"movimentos_financeiros":[],"fiagros_relacionados":[],"cras_emitidos":[],"parceiros_financeiros":[],"auditorias":[],"governanca_corporativa":false,"resumo_financeiro":"","confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("fin", ck, r, ttl=7200)
    return r


# =========================================================================
# AGENTE 3: CADEIA DE VALOR
# =========================================================================
def agent_cadeia_valor(client, empresa, dados_ops):
    ck = {"a":"cadeia","e":empresa}
    c = cache.get("cadeia", ck)
    if c: return c
    culturas = dados_ops.get('culturas',[])
    prompt = f"""ATUE COMO: Consultor de Supply Chain do Agro.
ALVO: "{empresa}" — Culturas: {culturas}

MAPEIE:
1. Posicao na cadeia: produtor/integrador/processador/trader
2. Clientes principais (tradings, industrias, varejo, export)
3. Fornecedores principais (Bayer, Syngenta, Mosaic, etc)
4. Parcerias estrategicas
5. Canais de venda
6. Nivel de integracao vertical (baixa/media/alta/total)
7. Exportacao: mercados
8. Certificacoes: GlobalGAP, Rainforest, FSC, ABR, organico, Bonsucro, ISCC

Retorne JSON:
{{"posicao_cadeia":"","clientes_principais":[],"fornecedores_principais":[],"parcerias_estrategicas":[],"canais_venda":[],"integracao_vertical_nivel":"","exporta":false,"mercados_exportacao":[],"certificacoes":[],"confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("cadeia", ck, r, ttl=7200)
    return r


# =========================================================================
# AGENTE 4: GRUPO ECONOMICO EXPANDIDO (com filiais e cidades)
# =========================================================================
def agent_grupo_economico(client, empresa, cnpj_matriz=""):
    ck = {"a":"grupo","e":empresa}
    c = cache.get("grupo", ck)
    if c: return c
    prompt = f"""ATUE COMO: Analista de Inteligencia Corporativa.
ALVO: "{empresa}" {f'(CNPJ: {cnpj_matriz})' if cnpj_matriz else ''}

MAPEIE O GRUPO ECONOMICO COMPLETO com DETALHES:

1. CNPJ MATRIZ
2. TODAS as FILIAIS — para cada uma informe: CNPJ, cidade/UF, atividade principal
3. TODAS as COLIGADAS/CONTROLADAS — CNPJ, razao social, cidade/UF, atividade
4. Total de empresas no grupo
5. Controladores/socios principais (PF ou holdings)
6. Se ha holding: qual a holding controladora

IMPORTANTE: Busque em Econodata, Casa dos Dados, JUCESP, site oficial, Receita Federal.
Quero ver a MAGNITUDE real do grupo — todas as ramificacoes.

Retorne JSON:
{{"cnpj_matriz":"","holding_controladora":"","filiais":[{{"cnpj":"","cidade":"","uf":"","atividade":""}}],"coligadas":[{{"cnpj":"","razao_social":"","cidade":"","uf":"","atividade":""}}],"total_empresas":0,"controladores":[],"confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("grupo", ck, r, ttl=7200)
    return r


# =========================================================================
# AGENTE 5: INTEL DE MERCADO
# =========================================================================
def agent_intel_mercado(client, empresa, setor_info=""):
    ck = {"a":"intel","e":empresa}
    c = cache.get("intel", ck)
    if c: return c
    prompt = f"""ATUE COMO: Analista de Inteligencia Competitiva — Agro.
ALVO: "{empresa}"
{f'CONTEXTO: {setor_info}' if setor_info else ''}

Busque NOTICIAS E SINAIS dos ultimos 12 meses:
1. Noticias: Expansao, crise, investimento, M&A
2. Sinais de compra ERP/tech: expansao, C-level, problemas, auditoria/IPO
3. Riscos: processos, ambientais, inadimplencia
4. Concorrentes do segmento/regiao
5. Oportunidades e tendencias

Retorne JSON:
{{"noticias_recentes":[{{"titulo":"","resumo":"","data_aprox":"","relevancia":"alta"}}],"sinais_compra":[],"riscos":[],"oportunidades":[],"concorrentes":[],"tendencias_setor":[],"dores_identificadas":[],"confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.2, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca":0.0}
    cache.set("intel", ck, r, ttl=3600)
    return r


# =========================================================================
# AGENTE 6: PROFILER DE DECISORES (NOVO — Deep Search)
# =========================================================================
def agent_profiler_decisores(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"decisores","e":alvo}
    c = cache.get("decisores", ck)
    if c: return c
    prompt = f"""ATUE COMO: Headhunter Executivo especializado em Agronegocio.
ALVO: "{alvo}" (tambem busque "{empresa}")

Sua missao e mapear TODOS os decisores-chave desta empresa.
Busque em: LinkedIn, site oficial, noticias, JUCESP, Econodata, Google.

PARA CADA PESSOA encontre:
- Nome completo
- Cargo/funcao atual
- Tempo no cargo (se disponivel)
- Formacao academica
- Experiencia anterior relevante
- LinkedIn URL (se encontrar)
- Relevancia para venda de ERP/tecnologia (alta/media/baixa)

MAPEIE ESPECIFICAMENTE:
1. CEO / Presidente / Diretor Geral
2. CFO / Diretor Financeiro / Controller
3. CTO / CIO / Diretor de TI / Gerente de TI
4. COO / Diretor de Operacoes / Diretor Agricola
5. Dir. RH / Dir. Pessoas
6. Dir. Comercial / Dir. Vendas
7. Membros do Conselho de Administracao
8. Socios relevantes (se empresa familiar)

Retorne JSON:
{{"decisores":[{{"nome":"","cargo":"","tempo_cargo":"","formacao":"","experiencia_anterior":"","linkedin":"","relevancia_erp":"alta","email_corporativo":""}}],"estrutura_decisao":"familiar|profissionalizada|mista","nivel_maturidade_gestao":"baixo|medio|alto","confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1, thinking_config=types.ThinkingConfig(thinking_budget=6144))
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"decisores":[],"confianca":0.0}
    cache.set("decisores", ck, r, ttl=7200)
    return r


# =========================================================================
# AGENTE 7: TECH STACK HUNTER (NOVO — Descobre sistemas usados)
# =========================================================================
def agent_tech_stack(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"tech","e":alvo}
    c = cache.get("tech", ck)
    if c: return c
    prompt = f"""ATUE COMO: Consultor de TI especializado em agronegocio brasileiro.
ALVO: "{alvo}" (tambem "{empresa}")

Investigue QUAL SISTEMA/ERP esta empresa utiliza atualmente.

BUSQUE PISTAS EM:
1. LinkedIn: vagas de emprego mencionando sistemas (ex: "Analista TOTVS", "Consultor SAP")
2. LinkedIn: perfis de funcionarios (ex: "Experiencia com Protheus na Empresa X")
3. Site da empresa: pagina de carreiras/vagas
4. Google: "empresa X" + "ERP" ou "TOTVS" ou "SAP" ou "Siagri" ou "Senior"
5. Noticias: anuncios de implantacao de sistema
6. Reclame Aqui / Glassdoor: mencionam sistema em avaliacoes
7. Integradores: consultorias que atenderam esta empresa

SISTEMAS PARA VERIFICAR:
- ERP: TOTVS (Protheus/RM/Datasul), SAP (S4HANA/B1), Senior, Siagri, Datacoper, Oracle, Sage
- Agro: Aegro, Solinftec, Agrosmart, Climate FieldView, Agrotools, SimpleFarm, Agrotopus
- RH: TOTVS RH, Senior HCM, ADP, Gupy, Kenoby
- Contabilidade: Dominio, Questor, Fortes
- BI: Power BI, Tableau, Qlik

Retorne JSON:
{{"erp_principal":{{"sistema":"","versao":"","fonte_evidencia":"","confianca":0.0}},"outros_sistemas":[{{"tipo":"","sistema":"","fonte_evidencia":""}}],"vagas_ti_abertas":[{{"titulo":"","plataforma":"","sistemas_mencionados":[]}}],"nivel_maturidade_ti":"baixo|medio|alto","investimento_ti_percebido":"baixo|medio|alto","dores_tech_identificadas":[],"confianca":0.0}}"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca":0.0}
    cache.set("tech", ck, r, ttl=7200)
    return r


# =========================================================================
# AGENTE 8: ANALISE ESTRATEGICA (Deep Thinking 12k + Portfolio Senior)
# =========================================================================
def agent_analise_estrategica(client, dados, sas, contexto=""):
    prompt = f"""VOCE E: Sara, Analista Senior de Inteligencia de Vendas da Senior Sistemas / GAtec.
Voce prepara briefings para Executivos de Contas antes de reunioes.

=== DADOS DO ALVO ===
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:14000]}

=== SCORE SAS 4.0 ===
Score: {sas.get('score',0)}/1000 — {sas.get('tier','N/D')}
Breakdown: {json.dumps(sas.get('breakdown',{}), ensure_ascii=False)}

{contexto}

{PORTFOLIO_SENIOR}

=== ESTRUTURA DO BRIEFING (separe secoes com |||) ===

SECAO 1 — QUEM E ESTA EMPRESA (PERFIL COMPLETO):
- Comece com um RESUMO EXECUTIVO: quem e, o que faz, tamanho, relevancia
- Dados factuais: hectares, cabecas, funcionarios, faturamento, capital
- Grupo economico: quantas empresas, quem controla, holding
- Posicao na cadeia de valor e nivel de integracao
- Se tem CRA/Fiagro/Auditoria: detalhe e explique o que isso significa
- Contexto regional e competitivo

SECAO 2 — COMPLEXIDADE OPERACIONAL & DORES:
- Complexidade: multiplas culturas? Agroindustria? Pecuaria integrada?
- Dores ESPECIFICAS conectadas com dados reais (nunca genericas)
- Gaps de gestao provaveis baseados no porte
- Tech stack atual: qual sistema usam? Quais as dores com ele?
- Compliance e regulacao relevante

SECAO 3 — FIT SENIOR / GATEC (O PITCH COM PROFUNDIDADE):
- Para CADA dor, indique o modulo ESPECIFICO Senior/GAtec que resolve:
  * SimpleFarm para gestao agricola e custos por talhao
  * CommerceSF para comercializacao de commodities
  * Operis para gestao de armazens
  * CommerceLog para logistica
  * Mapfy para agricultura de precisao
  * Senior ERP para backoffice/fiscal/financeiro
  * Senior HCM para folha/ponto/eSocial
  * Senior WMS/TMS/YMS para logistica
- Se usa concorrente (TOTVS/SAP/Siagri): argumento ESPECIFICO de troca
- ROI estimado com numeros
- Casos de referencia do mesmo setor/porte

SECAO 4 — PLANO DE ATAQUE TATICO:
- DECISORES: nomes reais, cargos, perfil, como chegar neles
- TIMING: safra/entressafra, pos-CRA, pos-expansao
- GATILHO: qual evento ou dor aguda usar como porta de entrada
- ESTRATEGIA: primeiro contato -> demo -> proposta -> fechamento (passo a passo)
- FIRST CALL SCRIPT: o que falar nos primeiros 2 minutos
- OBJECOES provaveis e como rebater cada uma
- RED FLAGS: o que pode dar errado
- QUICK WINS: o que entregar primeiro para gerar valor rapido

=== REGRAS ===
1. DIRETO e PRATICO — briefing militar
2. USE NOMES REAIS dos decisores se disponivel
3. CITE MODULOS ESPECIFICOS Senior/GAtec (nao generico)
4. Minimo 500 palavras por secao
5. Separe com ||| (3 pipes)
"""
    cfg = types.GenerateContentConfig(temperature=0.35, thinking_config=types.ThinkingConfig(thinking_budget=12288), max_output_tokens=16000)
    return _call(client, prompt, cfg, Priority.CRITICAL) or "Erro na analise."


# =========================================================================
# AGENTE 9: AUDITOR DE QUALIDADE
# =========================================================================
def agent_auditor_qualidade(client, texto, dados):
    prompt = f"""ATUE COMO: Editor-Chefe revisando dossie de inteligencia.

=== DOSSIE ===
{texto[:10000]}

=== DADOS ===
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:5000]}

Avalie (0-10):
1. PRECISAO: dados batem com JSON?
2. PROFUNDIDADE: cita financas, decisores, tech stack?
3. ACIONABILIDADE: executivo sabe o que fazer?
4. PERSONALIZACAO: especifico para ESTA empresa?
5. COMPLETUDE: 4 secoes completas?
6. FIT_SENIOR: menciona modulos especificos Senior/GAtec?
7. DECISORES: nomes e cargos reais mencionados?

Retorne JSON:
{{"scores":{{"precisao":{{"nota":0,"justificativa":""}},"profundidade":{{"nota":0,"justificativa":""}},"acionabilidade":{{"nota":0,"justificativa":""}},"personalizacao":{{"nota":0,"justificativa":""}},"completude":{{"nota":0,"justificativa":""}},"fit_senior":{{"nota":0,"justificativa":""}},"decisores":{{"nota":0,"justificativa":""}}}},"nota_final":0.0,"nivel":"EXCELENTE|BOM|ACEITAVEL|INSUFICIENTE","recomendacoes":[]}}"""
    cfg = types.GenerateContentConfig(temperature=0.2, thinking_config=types.ThinkingConfig(thinking_budget=4096))
    return _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"nota_final":0,"nivel":"INSUFICIENTE","recomendacoes":["Erro"]}


# =========================================================================
# BUSCA MAGICA CNPJ
# =========================================================================
def buscar_cnpj_por_nome(client, nome):
    ck = {"b":nome}
    c = cache.get("bcnpj", ck)
    if c: return c
    prompt = f"""Encontre o CNPJ principal da empresa/grupo "{nome}" do agronegocio brasileiro.
Busque em Econodata, Casa dos Dados, Socios Brasil, site oficial.
Retorne APENAS o CNPJ no formato XX.XXX.XXX/XXXX-XX ou "NAO_ENCONTRADO"."""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.0)
    text = _call(client, prompt, cfg, Priority.HIGH)
    if text and "NAO_ENCONTRADO" not in text:
        m = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', text)
        if m:
            cnpj = m.group(0)
            cache.set("bcnpj", ck, cnpj, ttl=86400)
            return cnpj
    return None
