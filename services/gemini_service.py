“””
services/gemini_service.py — Motor IA v3.1 (ALL Pro, 7 Agents)
TODOS os agentes rodam no gemini-2.5-pro para máxima precisão.
“””
import json, re, time
from typing import Optional, Any
from google import genai
from google.genai import types
from services.cache_service import cache
from services.request_queue import request_queue, Priority

MODEL = “gemini-2.5-pro”  # TUDO no Pro — precisão máxima

SEARCH_TOOL = types.Tool(google_search=types.GoogleSearch())

def _clean_json(text: str) -> Optional[dict]:
if not text:
return None
try:
m = re.search(r’{.*}’, text, re.DOTALL)
if m:
return json.loads(m.group(0))
except Exception:
pass
try:
return json.loads(text.replace(’`json', '').replace('`’, ‘’).strip())
except Exception:
return None

def _call(client, prompt: str, config: types.GenerateContentConfig, prio: Priority = Priority.NORMAL) -> Optional[str]:
def _do():
return client.models.generate_content(model=MODEL, contents=prompt, config=config).text
try:
return request_queue.execute(_do, priority=prio)
except Exception:
return None

# =============================================================================

# AGENTE 1: RECON OPERACIONAL

# =============================================================================

def agent_recon_operacional(client, empresa: str) -> dict:
ck = {“a”: “recon”, “e”: empresa}
c = cache.get(“recon”, ck)
if c:
return c

```
prompt = f"""ATUE COMO: Investigador Agrícola Sênior com 20 anos de campo.
```

ALVO: “{empresa}”

Busque em MÚLTIPLAS fontes (site oficial, LinkedIn, notícias, Econodata, relatórios setoriais).

DESCUBRA COM PRECISÃO:

1. Nome oficial do grupo econômico
1. Área TOTAL em hectares (se faixa, use valor médio)
1. TODAS as culturas: grãos, fibras, cana, café, citrus, HF, florestal, pecuária, etc
1. TODA infraestrutura vertical existente (veja a lista completa abaixo)
1. Regiões/estados de atuação
1. Número de fazendas/unidades
1. Pecuária: cabeças de gado, aves, suínos (se aplicável)
1. Área irrigada e área florestal (se aplicável)
1. Tecnologias: agricultura de precisão, drones, ERP, telemetria, etc.

LISTA COMPLETA DE VERTICALIZAÇÃO (marque true/false para CADA):
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

REGRAS: Seja FACTUAL. Não invente. Se não encontrar = 0/false. Confiança 0.0 a 1.0.

Retorne APENAS JSON:
{{
“nome_grupo”: “Nome”,
“hectares_total”: 0,
“culturas”: [],
“verticalizacao”: {{campo: bool para CADA campo da lista}},
“regioes_atuacao”: [],
“numero_fazendas”: 0,
“cabecas_gado”: 0,
“cabecas_aves”: 0,
“cabecas_suinos”: 0,
“area_florestal_ha”: 0,
“area_irrigada_ha”: 0,
“tecnologias_identificadas”: [],
“confianca”: 0.0
}}”””

```
cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL], temperature=0.1,
                                   thinking_config=types.ThinkingConfig(thinking_budget=4096))
r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"nome_grupo": empresa, "confianca": 0.0}
cache.set("recon", ck, r, ttl=7200)
return r
```

# =============================================================================

# AGENTE 2: SNIPER FINANCEIRO

# =============================================================================

def agent_sniper_financeiro(client, empresa: str, nome_grupo: str = “”) -> dict:
alvo = nome_grupo or empresa
ck = {“a”: “fin”, “e”: alvo}
c = cache.get(“fin”, ck)
if c:
return c

```
prompt = f"""ATUE COMO: Analista Sênior de Mercado de Capitais — Agro.
```

ALVO: “{alvo}” (pesquise também como “{empresa}”)

VASCULHE A WEB COM PROFUNDIDADE:

1. CRA (Certificados de Recebíveis do Agronegócio): valor, data, estruturador, rating, séries
1. FIAGRO: fundos relacionados, gestoras, tickers
1. GOVERNANÇA: auditoria Big 4, conselho, natureza jurídica S.A./Ltda
1. M&A: fusões, aquisições, parcerias estratégicas
1. DADOS FINANCEIROS: capital social, faturamento, funcionários (Econodata, Casa dos Dados, LinkedIn, RAIS)
1. PARCEIROS FINANCEIROS: bancos, gestoras, seguradoras
1. DÍVIDA: debêntures, empréstimos BNDES, Plano Safra

Retorne APENAS JSON:
{{
“capital_social_estimado”: 0,
“funcionarios_estimados”: 0,
“faturamento_estimado”: 0,
“movimentos_financeiros”: [“Fato 1: …”, “Fato 2: …”],
“fiagros_relacionados”: [],
“cras_emitidos”: [],
“parceiros_financeiros”: [],
“auditorias”: [],
“governanca_corporativa”: false,
“resumo_financeiro”: “texto”,
“confianca”: 0.0
}}”””

```
cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL], temperature=0.1,
                                   thinking_config=types.ThinkingConfig(thinking_budget=4096))
r = _clean_json(_call(client, prompt, cfg, Priority.HIGH)) or {"confianca": 0.0}
cache.set("fin", ck, r, ttl=7200)
return r
```

# =============================================================================

# AGENTE 3: CADEIA DE VALOR (NOVO)

# =============================================================================

def agent_cadeia_valor(client, empresa: str, dados_ops: dict) -> dict:
ck = {“a”: “cadeia”, “e”: empresa}
c = cache.get(“cadeia”, ck)
if c:
return c

```
culturas = dados_ops.get('culturas', [])
prompt = f"""ATUE COMO: Consultor de Supply Chain do Agronegócio.
```

ALVO: “{empresa}” — Culturas: {culturas}

MAPEIE A CADEIA DE VALOR COMPLETA:

1. POSIÇÃO NA CADEIA: É produtor primário? Integrador vertical? Processador? Trader?
1. CLIENTES PRINCIPAIS: Para quem vende? (Tradings, indústrias, varejo, exportação direta)
1. FORNECEDORES PRINCIPAIS: De quem compra insumos? (Bayer, Syngenta, Mosaic, etc)
1. PARCERIAS ESTRATÉGICAS: JVs, contratos de longo prazo, integrações
1. CANAIS DE VENDA: Cooperativa, trading, venda direta, marketplace
1. INTEGRAÇÃO VERTICAL: Qual o nível? (baixa/media/alta/total)
1. EXPORTAÇÃO: Exporta? Para quais mercados?
1. CERTIFICAÇÕES: GlobalGAP, Rainforest, FSC, ABR, orgânico, Bonsucro, ISCC, etc

Retorne APENAS JSON:
{{
“posicao_cadeia”: “produtor|integrador|processador|trader”,
“clientes_principais”: [],
“fornecedores_principais”: [],
“parcerias_estrategicas”: [],
“canais_venda”: [],
“integracao_vertical_nivel”: “baixa|media|alta|total”,
“exporta”: false,
“mercados_exportacao”: [],
“certificacoes”: [],
“confianca”: 0.0
}}”””

```
cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL], temperature=0.1,
                                   thinking_config=types.ThinkingConfig(thinking_budget=4096))
r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca": 0.0}
cache.set("cadeia", ck, r, ttl=7200)
return r
```

# =============================================================================

# AGENTE 4: GRUPO ECONÔMICO (NOVO)

# =============================================================================

def agent_grupo_economico(client, empresa: str, cnpj_matriz: str = “”) -> dict:
ck = {“a”: “grupo”, “e”: empresa}
c = cache.get(“grupo”, ck)
if c:
return c

```
prompt = f"""ATUE COMO: Analista de Inteligência Corporativa.
```

ALVO: “{empresa}” {f’(CNPJ Matriz: {cnpj_matriz})’ if cnpj_matriz else ‘’}

MAPEIE O GRUPO ECONÔMICO COMPLETO:

1. CNPJ MATRIZ (empresa controladora)
1. CNPJs de FILIAIS (mesma razão social, diferentes estados)
1. CNPJs de COLIGADAS/CONTROLADAS (empresas do mesmo grupo com razões sociais diferentes)
1. TOTAL de empresas no grupo
1. CONTROLADORES/SÓCIOS PRINCIPAIS (pessoas físicas ou holdings)

Busque em: Econodata, Casa dos Dados, Receita Federal, JUCESP/JUCEMG, site oficial.

Retorne APENAS JSON:
{{
“cnpj_matriz”: “XX.XXX.XXX/XXXX-XX”,
“cnpjs_filiais”: [“lista de CNPJs”],
“cnpjs_coligadas”: [“lista de CNPJs com nomes: CNPJ - Nome”],
“total_empresas”: 0,
“controladores”: [“Nome 1”, “Nome 2”],
“confianca”: 0.0
}}”””

```
cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL], temperature=0.1,
                                   thinking_config=types.ThinkingConfig(thinking_budget=2048))
r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca": 0.0}
cache.set("grupo", ck, r, ttl=7200)
return r
```

# =============================================================================

# AGENTE 5: INTEL DE MERCADO

# =============================================================================

def agent_intel_mercado(client, empresa: str, setor_info: str = “”) -> dict:
ck = {“a”: “intel”, “e”: empresa}
c = cache.get(“intel”, ck)
if c:
return c

```
prompt = f"""ATUE COMO: Analista de Inteligência Competitiva — Agro.
```

ALVO: “{empresa}”
{f’CONTEXTO: {setor_info}’ if setor_info else ‘’}

Busque NOTÍCIAS E SINAIS dos últimos 12 meses:

1. NOTÍCIAS: Expansão? Crise? Investimento? Novo projeto? M&A?
1. SINAIS DE COMPRA para ERP/tecnologia:
- Expansão de área, contratação de C-level, problemas operacionais
- Auditoria ou IPO (precisam de sistemas robustos)
- Troca de sistema (insatisfação com ERP atual)
1. RISCOS: Processos judiciais, ambientais, inadimplência, recall
1. CONCORRENTES: Quem mais atua no segmento/região
1. OPORTUNIDADES: Janelas de venda, dores explícitas, gaps de mercado
1. TENDÊNCIAS: O que está mudando no setor deles

Retorne APENAS JSON:
{{
“noticias_recentes”: [{{“titulo”: “”, “resumo”: “”, “data_aprox”: “”, “relevancia”: “alta|media|baixa”}}],
“sinais_compra”: [],
“riscos”: [],
“oportunidades”: [],
“concorrentes”: [],
“tendencias_setor”: [],
“dores_identificadas”: [],
“confianca”: 0.0
}}”””

```
cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL], temperature=0.2,
                                   thinking_config=types.ThinkingConfig(thinking_budget=4096))
r = _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {"confianca": 0.0}
cache.set("intel", ck, r, ttl=3600)
return r
```

# =============================================================================

# AGENTE 6: ANÁLISE ESTRATÉGICA (Deep Thinking 12k)

# =============================================================================

def agent_analise_estrategica(client, dados: dict, sas: dict, contexto: str = “”,
exemplo_dossie: str = “”) -> str:
prompt = f””“VOCÊ É: Sara, Analista Sênior de Inteligência de Vendas (Agro) da Senior Sistemas.
Você prepara briefings estratégicos para Executivos de Contas.

=== DADOS COMPLETOS DO ALVO ===
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:12000]}

=== SCORE SAS 4.0 ===
Score: {sas.get(‘score’, 0)}/1000 — {sas.get(‘tier’, ‘N/D’)}
Breakdown: {json.dumps(sas.get(‘breakdown’, {}), ensure_ascii=False)}

{contexto}

{f’=== EXEMPLO DE DOSSIÊ BEM FEITO ==={chr(10)}{exemplo_dossie}’ if exemplo_dossie else ‘’}

=== ESTRUTURA DO BRIEFING (separe seções com |||) ===

SEÇÃO 1 — PERFIL & MERCADO:

- Tamanho REAL da operação (hectares, cabeças, funcionários, faturamento)
- Se tem CRA/Fiagro/Auditoria: é CORPORAÇÃO, não fazendeiro
- Posição na cadeia de valor e nível de integração vertical
- Grupo econômico: quantas empresas, quem controla
- Contexto regional e competitivo

SEÇÃO 2 — COMPLEXIDADE OPERACIONAL & DORES:

- Complexidade por vertical: múltiplas culturas? Agroindústria? Pecuária integrada?
- Dores ESPECÍFICAS (nunca genéricas) conectadas com os dados reais
- Gaps de gestão prováveis baseados no porte e na verticalização
- Compliance e regulação relevante para o setor deles
- Cadeia de fornecimento: gargalos e oportunidades

SEÇÃO 3 — FIT SENIOR (O PITCH):

- Módulos Senior que resolvem CADA dor identificada
- Argumento matador para ESTA conta
- Se usa concorrente: argumento de troca com dados
- ROI estimado: onde Senior gera economia/eficiência
- Casos de referência do mesmo setor/porte

SEÇÃO 4 — PLANO DE ATAQUE TÁTICO:

- Decisor provável: cargo, perfil, como chegar nele
- Timing ideal: safra/entressafra, pós-CRA, pós-expansão
- Gatilho de entrada: evento, dor aguda, expansão, troca de sistema
- Estratégia: primeiro contato → demo → proposta → fechamento
- Red flags: o que pode dar errado, objeções prováveis
- Quick wins: o que entregar primeiro para gerar valor rápido

=== REGRAS ===

1. DIRETO e PRÁTICO — briefing militar, sem enrolação
1. USE DADOS FINANCEIROS: CRA, Fiagro, auditoria = ouro
1. REALPOLITIK: 20k+ ha com auditoria = corporação
1. Mínimo 400 palavras por seção, máximo 700
1. Separe com ||| (exatamente 3 pipes entre seções)
1. Cite dados numéricos e fontes quando possível
   “””
   
   cfg = types.GenerateContentConfig(
   temperature=0.35,
   thinking_config=types.ThinkingConfig(thinking_budget=12288),
   max_output_tokens=16000,
   )
   return _call(client, prompt, cfg, Priority.CRITICAL) or “Erro na análise.”

# =============================================================================

# AGENTE 7: AUDITOR DE QUALIDADE

# =============================================================================

def agent_auditor_qualidade(client, texto: str, dados: dict) -> dict:
prompt = f””“ATUE COMO: Editor-Chefe revisando um dossiê de inteligência de vendas.

=== DOSSIÊ ===
{texto[:10000]}

=== DADOS BASE ===
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:5000]}

Avalie (0 a 10) e justifique:

1. PRECISÃO: dados do texto batem com o JSON?
1. PROFUNDIDADE: vai além do óbvio? Cita finanças?
1. ACIONABILIDADE: executivo sabe o que fazer?
1. PERSONALIZAÇÃO: específico para ESTA empresa?
1. COMPLETUDE: 4 seções completas?
1. DADOS_FINANCEIROS: CRA/Fiagro/auditoria mencionados se existem?

Retorne JSON:
{{
“scores”: {{
“precisao”: {{“nota”: 0, “justificativa”: “”}},
“profundidade”: {{“nota”: 0, “justificativa”: “”}},
“acionabilidade”: {{“nota”: 0, “justificativa”: “”}},
“personalizacao”: {{“nota”: 0, “justificativa”: “”}},
“completude”: {{“nota”: 0, “justificativa”: “”}},
“dados_financeiros”: {{“nota”: 0, “justificativa”: “”}}
}},
“nota_final”: 0.0,
“nivel”: “EXCELENTE|BOM|ACEITAVEL|INSUFICIENTE”,
“recomendacoes”: []
}}”””

```
cfg = types.GenerateContentConfig(temperature=0.2,
                                   thinking_config=types.ThinkingConfig(thinking_budget=4096))
return _clean_json(_call(client, prompt, cfg, Priority.NORMAL)) or {
    "nota_final": 0, "nivel": "INSUFICIENTE", "recomendacoes": ["Erro na auditoria"]}
```

# =============================================================================

# BUSCA MÁGICA CNPJ

# =============================================================================

def buscar_cnpj_por_nome(client, nome: str) -> Optional[str]:
ck = {“b”: nome}
c = cache.get(“bcnpj”, ck)
if c:
return c
prompt = f””“Encontre o CNPJ principal da empresa/grupo “{nome}” do agronegócio brasileiro.
Busque em Econodata, Casa dos Dados, Sócios Brasil, site oficial.
Retorne APENAS o CNPJ no formato XX.XXX.XXX/XXXX-XX ou “NAO_ENCONTRADO”.”””
cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL], temperature=0.0)
text = _call(client, prompt, cfg, Priority.HIGH)
if text and “NAO_ENCONTRADO” not in text:
m = re.search(r’\d{2}.?\d{3}.?\d{3}/?\d{4}-?\d{2}’, text)
if m:
cnpj = m.group(0)
cache.set(“bcnpj”, ck, cnpj, ttl=86400)
return cnpj
return None