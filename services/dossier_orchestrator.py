“””
services/dossier_orchestrator.py — Pipeline 8 Passos com Feedback Visual
“””
import json, time
from typing import Optional, Callable
from google import genai
from scout_types import (
DossieCompleto, DadosOperacionais, DadosFinanceiros, CadeiaValor,
GrupoEconomico, IntelMercado, SecaoAnalise, Verticalizacao, PipelineStepResult,
)
from services.gemini_service import (
agent_recon_operacional, agent_sniper_financeiro, agent_cadeia_valor,
agent_grupo_economico, agent_intel_mercado, agent_analise_estrategica,
agent_auditor_qualidade, buscar_cnpj_por_nome,
)
from services.cnpj_service import consultar_cnpj, limpar_cnpj, validar_cnpj
from services.market_estimator import calcular_sas
from services.quality_gate import executar_quality_gate
from utils.market_intelligence import enriquecer_prompt_com_contexto

def _parse_vert(raw):
v = Verticalizacao()
vr = raw.get(‘verticalizacao’, {})
if isinstance(vr, dict):
for campo in v.all_fields():
if vr.get(campo):
setattr(v, campo, True)
return v

def _parse_ops(raw):
return DadosOperacionais(
nome_grupo=raw.get(‘nome_grupo’, ‘’), hectares_total=int(raw.get(‘hectares_total’, 0) or 0),
culturas=raw.get(‘culturas’, []) or [], verticalizacao=_parse_vert(raw),
regioes_atuacao=raw.get(‘regioes_atuacao’, []) or [],
numero_fazendas=int(raw.get(‘numero_fazendas’, 0) or 0),
tecnologias_identificadas=raw.get(‘tecnologias_identificadas’, []) or [],
cabecas_gado=int(raw.get(‘cabecas_gado’, 0) or 0),
cabecas_aves=int(raw.get(‘cabecas_aves’, 0) or 0),
cabecas_suinos=int(raw.get(‘cabecas_suinos’, 0) or 0),
area_florestal_ha=int(raw.get(‘area_florestal_ha’, 0) or 0),
area_irrigada_ha=int(raw.get(‘area_irrigada_ha’, 0) or 0),
confianca=float(raw.get(‘confianca’, 0) or 0))

def _parse_fin(raw):
return DadosFinanceiros(
capital_social_estimado=float(raw.get(‘capital_social_estimado’, 0) or 0),
funcionarios_estimados=int(raw.get(‘funcionarios_estimados’, 0) or 0),
faturamento_estimado=float(raw.get(‘faturamento_estimado’, 0) or 0),
movimentos_financeiros=raw.get(‘movimentos_financeiros’, []) or [],
fiagros_relacionados=raw.get(‘fiagros_relacionados’, []) or [],
cras_emitidos=raw.get(‘cras_emitidos’, []) or [],
parceiros_financeiros=raw.get(‘parceiros_financeiros’, []) or [],
auditorias=raw.get(‘auditorias’, []) or [],
governanca_corporativa=bool(raw.get(‘governanca_corporativa’, False)),
resumo_financeiro=raw.get(‘resumo_financeiro’, ‘’),
confianca=float(raw.get(‘confianca’, 0) or 0))

def _parse_cadeia(raw):
return CadeiaValor(
posicao_cadeia=raw.get(‘posicao_cadeia’, ‘’),
clientes_principais=raw.get(‘clientes_principais’, []) or [],
fornecedores_principais=raw.get(‘fornecedores_principais’, []) or [],
parcerias_estrategicas=raw.get(‘parcerias_estrategicas’, []) or [],
canais_venda=raw.get(‘canais_venda’, []) or [],
integracao_vertical_nivel=raw.get(‘integracao_vertical_nivel’, ‘’),
exporta=bool(raw.get(‘exporta’, False)),
mercados_exportacao=raw.get(‘mercados_exportacao’, []) or [],
certificacoes=raw.get(‘certificacoes’, []) or [],
confianca=float(raw.get(‘confianca’, 0) or 0))

def _parse_grupo(raw):
return GrupoEconomico(
cnpj_matriz=raw.get(‘cnpj_matriz’, ‘’),
cnpjs_filiais=raw.get(‘cnpjs_filiais’, []) or [],
cnpjs_coligadas=raw.get(‘cnpjs_coligadas’, []) or [],
total_empresas=int(raw.get(‘total_empresas’, 0) or 0),
controladores=raw.get(‘controladores’, []) or [],
confianca=float(raw.get(‘confianca’, 0) or 0))

def _parse_intel(raw):
return IntelMercado(
noticias_recentes=raw.get(‘noticias_recentes’, []) or [],
concorrentes=raw.get(‘concorrentes’, []) or [],
tendencias_setor=raw.get(‘tendencias_setor’, []) or [],
dores_identificadas=raw.get(‘dores_identificadas’, []) or [],
oportunidades=raw.get(‘oportunidades’, []) or [],
sinais_compra=raw.get(‘sinais_compra’, []) or [],
riscos=raw.get(‘riscos’, []) or [],
confianca=float(raw.get(‘confianca’, 0) or 0))

def _parse_secoes(texto):
TIT = [(“🏢”,“Perfil & Mercado”),(“🚜”,“Complexidade & Dores”),(“💡”,“Fit Senior”),(“⚔️”,“Plano de Ataque”)]
secoes = []
for i, p in enumerate(texto.split(’|||’)):
p = p.strip()
if not p: continue
ic, t = TIT[i] if i < len(TIT) else (“📄”, f”Seção {i+1}”)
secoes.append(SecaoAnalise(titulo=t, conteudo=p, icone=ic))
return secoes if len(secoes) >= 2 else [SecaoAnalise(titulo=“Análise Completa”, conteudo=texto, icone=“🧠”)]

def gerar_dossie_completo(empresa_alvo, api_key, cnpj=””, log_cb=None, progress_cb=None, step_cb=None):
start = time.time()
client = genai.Client(api_key=api_key)
d = DossieCompleto(empresa_alvo=empresa_alvo, cnpj=cnpj)
def _log(m):
d.pipeline_log.append(m)
if log_cb: log_cb(m)
def _prog(p, m):
if progress_cb: progress_cb(min(p, 1.0), m)
def _step(s):
d.pipeline_steps.append(s)
if step_cb: step_cb(s)

```
# P1: CNPJ
_prog(0.03, "📋 Passo 1/8: CNPJ...")
t0 = time.time()
s1 = PipelineStepResult(1, "Consulta CNPJ", "📋", "running")
if cnpj and validar_cnpj(limpar_cnpj(cnpj)):
    dc = consultar_cnpj(cnpj)
    if dc:
        d.dados_cnpj = dc; d.cnpj = cnpj
        s1.status = "success"; s1.resumo = f"{dc.razao_social} | {dc.municipio}/{dc.uf}"
        s1.detalhes = [f"CNAE: {dc.cnae_principal}", f"Capital: R${dc.capital_social:,.0f}", f"QSA: {len(dc.qsa)} sócios"]
    else:
        s1.status = "warning"; s1.resumo = "Não encontrado"
else:
    cf = buscar_cnpj_por_nome(client, empresa_alvo)
    if cf:
        dc = consultar_cnpj(cf)
        if dc:
            d.dados_cnpj = dc; d.cnpj = cf
            s1.status = "success"; s1.resumo = f"IA encontrou: {cf} — {dc.razao_social}"
        else:
            s1.status = "warning"; s1.resumo = f"CNPJ {cf} sem dados"
    else:
        s1.status = "warning"; s1.resumo = "Não localizado"
s1.tempo_segundos = time.time() - t0
_step(s1)

# P2: RECON
_prog(0.12, "🛰️ Passo 2/8: Recon Operacional...")
t0 = time.time()
s2 = PipelineStepResult(2, "Recon Operacional", "🛰️", "running")
raw_ops = agent_recon_operacional(client, empresa_alvo)
d.dados_operacionais = _parse_ops(raw_ops)
ng = d.dados_operacionais.nome_grupo or empresa_alvo
verts = d.dados_operacionais.verticalizacao.listar_ativos()
s2.status = "success"; s2.confianca = d.dados_operacionais.confianca
s2.resumo = f"{ng} | {d.dados_operacionais.hectares_total:,} ha | {', '.join(d.dados_operacionais.culturas[:4])}"
s2.detalhes = [f"Fazendas: {d.dados_operacionais.numero_fazendas}", f"Regiões: {', '.join(d.dados_operacionais.regioes_atuacao)}"]
if verts: s2.detalhes.append(f"Verticalizações: {', '.join(verts[:6])}")
if d.dados_operacionais.cabecas_gado: s2.detalhes.append(f"Gado: {d.dados_operacionais.cabecas_gado:,}")
if d.dados_operacionais.cabecas_aves: s2.detalhes.append(f"Aves: {d.dados_operacionais.cabecas_aves:,}")
s2.tempo_segundos = time.time() - t0
_step(s2)

# P3: FINANCEIRO
_prog(0.25, "💰 Passo 3/8: Sniper Financeiro...")
t0 = time.time()
s3 = PipelineStepResult(3, "Sniper Financeiro", "💰", "running")
raw_fin = agent_sniper_financeiro(client, empresa_alvo, ng)
d.dados_financeiros = _parse_fin(raw_fin)
fi = d.dados_financeiros
s3.status = "success"; s3.confianca = fi.confianca
s3.resumo = f"Capital: R${fi.capital_social_estimado/1e6:.1f}M | {fi.funcionarios_estimados:,} funcs | {len(fi.movimentos_financeiros)} movimentos"
s3.detalhes = [f"Fiagros: {', '.join(fi.fiagros_relacionados[:3]) or 'Nenhum'}",
               f"CRAs: {', '.join(fi.cras_emitidos[:2]) or 'Nenhum'}",
               f"Governança: {'Sim' if fi.governanca_corporativa else 'Não'}"]
for mv in fi.movimentos_financeiros[:3]: s3.detalhes.append(f"→ {mv}")
s3.tempo_segundos = time.time() - t0
_step(s3)

# P4: CADEIA DE VALOR
_prog(0.38, "🔗 Passo 4/8: Cadeia de Valor...")
t0 = time.time()
s4 = PipelineStepResult(4, "Cadeia de Valor", "🔗", "running")
raw_cad = agent_cadeia_valor(client, empresa_alvo, raw_ops)
d.cadeia_valor = _parse_cadeia(raw_cad)
cv = d.cadeia_valor
s4.status = "success"; s4.confianca = cv.confianca
s4.resumo = f"{cv.posicao_cadeia} | Integração: {cv.integracao_vertical_nivel} | Export: {'Sim' if cv.exporta else 'Não'}"
s4.detalhes = [f"Clientes: {', '.join(cv.clientes_principais[:4]) or 'N/I'}",
               f"Certificações: {', '.join(cv.certificacoes) or 'Nenhuma'}"]
s4.tempo_segundos = time.time() - t0
_step(s4)

# P5: GRUPO ECONÔMICO
_prog(0.48, "🏛️ Passo 5/8: Grupo Econômico...")
t0 = time.time()
s5 = PipelineStepResult(5, "Grupo Econômico", "🏛️", "running")
raw_grp = agent_grupo_economico(client, empresa_alvo, d.cnpj)
d.grupo_economico = _parse_grupo(raw_grp)
g = d.grupo_economico
s5.status = "success"; s5.confianca = g.confianca
s5.resumo = f"{g.total_empresas} empresas | {len(g.controladores)} controladores"
s5.detalhes = [f"Controladores: {', '.join(g.controladores[:3]) or 'N/I'}"]
for c in g.cnpjs_coligadas[:3]: s5.detalhes.append(f"→ {c}")
s5.tempo_segundos = time.time() - t0
_step(s5)

# P6: INTEL MERCADO
_prog(0.58, "📡 Passo 6/8: Intel de Mercado...")
t0 = time.time()
s6 = PipelineStepResult(6, "Intel de Mercado", "📡", "running")
cnae = d.dados_cnpj.cnae_principal if d.dados_cnpj else ""
uf = d.dados_cnpj.uf if d.dados_cnpj else (d.dados_operacionais.regioes_atuacao[0] if d.dados_operacionais.regioes_atuacao else "")
ctx = enriquecer_prompt_com_contexto(cnae, uf)
raw_int = agent_intel_mercado(client, empresa_alvo, ctx)
d.intel_mercado = _parse_intel(raw_int)
il = d.intel_mercado
s6.status = "success"; s6.confianca = il.confianca
s6.resumo = f"{len(il.noticias_recentes)} notícias | {len(il.sinais_compra)} sinais | {len(il.riscos)} riscos"
for sc in il.sinais_compra[:3]: s6.detalhes.append(f"🟢 {sc}")
for rs in il.riscos[:2]: s6.detalhes.append(f"🔴 {rs}")
s6.tempo_segundos = time.time() - t0
_step(s6)

# P6.5: SCORE SAS
_prog(0.68, "📊 Calculando Score SAS 4.0...")
dados_m = d.merge_dados()
d.sas_result = calcular_sas(dados_m)
_log(f"Score: {d.sas_result.score}/1000 — {d.sas_result.tier.value}")

# P7: ANÁLISE ESTRATÉGICA (Pro Deep Thinking 12k)
_prog(0.72, "🧠 Passo 7/8: Análise Estratégica (Pro Deep Thinking)...")
t0 = time.time()
s7 = PipelineStepResult(7, "Análise Estratégica", "🧠", "running")
dados_analise = dados_m.copy()
dados_analise['intel'] = {'noticias': il.noticias_recentes, 'sinais': il.sinais_compra,
                           'dores': il.dores_identificadas, 'oportunidades': il.oportunidades,
                           'riscos': il.riscos, 'concorrentes': il.concorrentes}
sas_d = {'score': d.sas_result.score, 'tier': d.sas_result.tier.value, 'breakdown': d.sas_result.breakdown.to_dict()}
texto = agent_analise_estrategica(client, dados_analise, sas_d, ctx)
d.analise_bruta = texto
d.secoes_analise = _parse_secoes(texto)
d.modelo_usado = "gemini-2.5-pro (todos os agentes)"
nw = sum(len(s.conteudo.split()) for s in d.secoes_analise)
s7.status = "success"; s7.resumo = f"{len(d.secoes_analise)} seções | {nw} palavras"
s7.tempo_segundos = time.time() - t0
_step(s7)

# P8: QUALITY GATE
_prog(0.90, "✅ Passo 8/8: Quality Gate...")
t0 = time.time()
s8 = PipelineStepResult(8, "Quality Gate", "✅", "running")
d.quality_report = executar_quality_gate(d)
try:
    ai = agent_auditor_qualidade(client, texto, dados_analise)
    d.quality_report.audit_ia = ai
    d.quality_report.recomendacoes.extend(ai.get('recomendacoes', []))
    s8.detalhes.append(f"Nota IA: {ai.get('nota_final', 0)}/10")
except Exception as e:
    s8.detalhes.append(f"Auditoria IA falhou: {e}")
s8.status = "success"
s8.resumo = f"{d.quality_report.nivel.value} ({d.quality_report.score_qualidade:.0f}%)"
s8.tempo_segundos = time.time() - t0
_step(s8)

d.tempo_total_segundos = time.time() - start
d.timestamp_geracao = time.strftime("%Y-%m-%d %H:%M:%S")
_prog(1.0, "🎯 Dossiê completo!")
return d
```