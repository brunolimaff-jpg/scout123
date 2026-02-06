"""
services/dossier_orchestrator.py — Pipeline 10 Passos v3.2
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import json, time
from typing import Optional, Callable


def _sj(lst, n=None):
    """Safe join: converts any list items to str before joining."""
    if not lst: return ''
    items = lst[:n] if n else lst
    return ', '.join(str(x) if not isinstance(x, dict) else x.get('nome', x.get('titulo', x.get('sistema', str(x)))) for x in items)
from google import genai
from scout_types import (
    DossieCompleto, DadosOperacionais, DadosFinanceiros, CadeiaValor,
    GrupoEconomico, IntelMercado, SecaoAnalise, Verticalizacao, PipelineStepResult,
)
from services.gemini_service import (
    agent_recon_operacional, agent_sniper_financeiro, agent_cadeia_valor,
    agent_grupo_economico, agent_intel_mercado, agent_profiler_decisores,
    agent_tech_stack, agent_analise_estrategica,
    agent_auditor_qualidade, buscar_cnpj_por_nome,
)
from services.cnpj_service import consultar_cnpj, limpar_cnpj, validar_cnpj
from services.market_estimator import calcular_sas
from services.quality_gate import executar_quality_gate
from utils.market_intelligence import enriquecer_prompt_com_contexto


def _parse_vert(raw):
    v = Verticalizacao()
    vr = raw.get('verticalizacao', {})
    if isinstance(vr, dict):
        for campo in v.all_fields():
            if vr.get(campo): setattr(v, campo, True)
    return v

def _parse_ops(raw):
    return DadosOperacionais(
        nome_grupo=raw.get('nome_grupo',''), hectares_total=int(raw.get('hectares_total',0) or 0),
        culturas=_to_strlist(raw.get('culturas',[])),
        verticalizacao=_parse_vert(raw),
        regioes_atuacao=_to_strlist(raw.get('regioes_atuacao',[])),
        numero_fazendas=int(raw.get('numero_fazendas',0) or 0),
        tecnologias_identificadas=_to_strlist(raw.get('tecnologias_identificadas',[])),
        cabecas_gado=int(raw.get('cabecas_gado',0) or 0),
        cabecas_aves=int(raw.get('cabecas_aves',0) or 0),
        cabecas_suinos=int(raw.get('cabecas_suinos',0) or 0),
        area_florestal_ha=int(raw.get('area_florestal_ha',0) or 0),
        area_irrigada_ha=int(raw.get('area_irrigada_ha',0) or 0),
        confianca=float(raw.get('confianca',0) or 0))

def _to_strlist(v):
    """Force any list to list[str], handling dicts gracefully."""
    if not v: return []
    return [str(x) if not isinstance(x, dict) else x.get('nome', x.get('titulo', x.get('descricao', json.dumps(x, ensure_ascii=False)))) for x in v]

def _parse_fin(raw):
    return DadosFinanceiros(
        capital_social_estimado=float(raw.get('capital_social_estimado',0) or 0),
        funcionarios_estimados=int(raw.get('funcionarios_estimados',0) or 0),
        faturamento_estimado=float(raw.get('faturamento_estimado',0) or 0),
        movimentos_financeiros=_to_strlist(raw.get('movimentos_financeiros',[])),
        fiagros_relacionados=_to_strlist(raw.get('fiagros_relacionados',[])),
        cras_emitidos=_to_strlist(raw.get('cras_emitidos',[])),
        parceiros_financeiros=_to_strlist(raw.get('parceiros_financeiros',[])),
        auditorias=_to_strlist(raw.get('auditorias',[])),
        governanca_corporativa=bool(raw.get('governanca_corporativa',False)),
        resumo_financeiro=raw.get('resumo_financeiro',''),
        confianca=float(raw.get('confianca',0) or 0))

def _parse_cadeia(raw):
    return CadeiaValor(
        posicao_cadeia=raw.get('posicao_cadeia',''),
        clientes_principais=_to_strlist(raw.get('clientes_principais',[])),
        fornecedores_principais=_to_strlist(raw.get('fornecedores_principais',[])),
        parcerias_estrategicas=_to_strlist(raw.get('parcerias_estrategicas',[])),
        canais_venda=_to_strlist(raw.get('canais_venda',[])),
        integracao_vertical_nivel=raw.get('integracao_vertical_nivel',''),
        exporta=bool(raw.get('exporta',False)),
        mercados_exportacao=_to_strlist(raw.get('mercados_exportacao',[])),
        certificacoes=_to_strlist(raw.get('certificacoes',[])),
        confianca=float(raw.get('confianca',0) or 0))

def _parse_grupo(raw):
    # controladores pode vir como list[str] ou list[dict]
    ctrls_raw = raw.get('controladores', []) or []
    ctrls = []
    for c in ctrls_raw:
        if isinstance(c, dict):
            ctrls.append(c.get('nome', c.get('razao_social', str(c))))
        else:
            ctrls.append(str(c))
    # filiais e coligadas podem vir como list[dict] ou list[str]
    filiais = raw.get('filiais', []) or raw.get('cnpjs_filiais', []) or []
    coligadas = raw.get('coligadas', []) or raw.get('cnpjs_coligadas', []) or []
    return GrupoEconomico(
        cnpj_matriz=raw.get('cnpj_matriz', ''),
        cnpjs_filiais=filiais,
        cnpjs_coligadas=coligadas,
        total_empresas=int(raw.get('total_empresas', 0) or 0),
        controladores=ctrls,
        holding_controladora=raw.get('holding_controladora', ''),
        confianca=float(raw.get('confianca', 0) or 0))

def _parse_intel(raw):
    return IntelMercado(
        noticias_recentes=raw.get('noticias_recentes',[]) or [],
        concorrentes=_to_strlist(raw.get('concorrentes',[])),
        tendencias_setor=_to_strlist(raw.get('tendencias_setor',[])),
        dores_identificadas=_to_strlist(raw.get('dores_identificadas',[])),
        oportunidades=_to_strlist(raw.get('oportunidades',[])),
        sinais_compra=_to_strlist(raw.get('sinais_compra',[])),
        riscos=_to_strlist(raw.get('riscos',[])),
        confianca=float(raw.get('confianca',0) or 0))

def _parse_secoes(texto):
    TIT = [("🏢","Quem e Esta Empresa"),("🚜","Complexidade & Dores"),("💡","Fit Senior/GAtec"),("⚔️","Plano de Ataque")]
    secoes = []
    for i, p in enumerate(texto.split('|||')):
        p = p.strip()
        if not p: continue
        ic, t = TIT[i] if i < len(TIT) else ("📄", f"Secao {i+1}")
        secoes.append(SecaoAnalise(titulo=t, conteudo=p, icone=ic))
    return secoes if len(secoes) >= 2 else [SecaoAnalise(titulo="Analise Completa", conteudo=texto, icone="🧠")]


def gerar_dossie_completo(empresa_alvo, api_key, cnpj="", log_cb=None, progress_cb=None, step_cb=None):
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

    # P1: CNPJ
    _prog(0.03, "📋 Passo 1/10: CNPJ...")
    t0 = time.time()
    s1 = PipelineStepResult(1, "Consulta CNPJ", "📋", "running")
    if cnpj and validar_cnpj(limpar_cnpj(cnpj)):
        dc = consultar_cnpj(cnpj)
        if dc:
            d.dados_cnpj = dc; d.cnpj = cnpj
            s1.status = "success"; s1.resumo = f"{dc.razao_social} | {dc.municipio}/{dc.uf}"
            s1.detalhes = [f"CNAE: {dc.cnae_principal}", f"Capital: R${dc.capital_social:,.0f}", f"QSA: {len(dc.qsa)} socios"]
        else: s1.status = "warning"; s1.resumo = "Nao encontrado"
    else:
        cf = buscar_cnpj_por_nome(client, empresa_alvo)
        if cf:
            dc = consultar_cnpj(cf)
            if dc:
                d.dados_cnpj = dc; d.cnpj = cf
                s1.status = "success"; s1.resumo = f"IA encontrou: {cf} — {dc.razao_social}"
            else: s1.status = "warning"; s1.resumo = f"CNPJ {cf} sem dados"
        else: s1.status = "warning"; s1.resumo = "Nao localizado"
    s1.tempo_segundos = time.time() - t0; _step(s1)

    # P2: RECON
    _prog(0.10, "🛰️ Passo 2/10: Recon Operacional...")
    t0 = time.time()
    s2 = PipelineStepResult(2, "Recon Operacional", "🛰️", "running")
    raw_ops = agent_recon_operacional(client, empresa_alvo)
    d.dados_operacionais = _parse_ops(raw_ops)
    ng = d.dados_operacionais.nome_grupo or empresa_alvo
    verts = d.dados_operacionais.verticalizacao.listar_ativos()
    s2.status = "success"; s2.confianca = d.dados_operacionais.confianca
    s2.resumo = f"{ng} | {d.dados_operacionais.hectares_total:,} ha | {_sj(d.dados_operacionais.culturas, 4)}"
    s2.detalhes = [f"Fazendas: {d.dados_operacionais.numero_fazendas}", f"Regioes: {_sj(d.dados_operacionais.regioes_atuacao)}"]
    if verts: s2.detalhes.append(f"Vert: {_sj(verts, 6)}")
    if d.dados_operacionais.cabecas_gado: s2.detalhes.append(f"Gado: {d.dados_operacionais.cabecas_gado:,}")
    s2.tempo_segundos = time.time() - t0; _step(s2)

    # P3: FINANCEIRO
    _prog(0.20, "💰 Passo 3/10: Sniper Financeiro...")
    t0 = time.time()
    s3 = PipelineStepResult(3, "Sniper Financeiro", "💰", "running")
    raw_fin = agent_sniper_financeiro(client, empresa_alvo, ng)
    d.dados_financeiros = _parse_fin(raw_fin)
    fi = d.dados_financeiros
    s3.status = "success"; s3.confianca = fi.confianca
    s3.resumo = f"R${fi.capital_social_estimado/1e6:.1f}M | {fi.funcionarios_estimados:,} funcs | {len(fi.movimentos_financeiros)} mov"
    s3.detalhes = [f"Fiagros: {_sj(fi.fiagros_relacionados, 2) or 'Nenhum'}",
                   f"CRAs: {_sj(fi.cras_emitidos, 2) or 'Nenhum'}"]
    for mv in fi.movimentos_financeiros[:2]: s3.detalhes.append(f"→ {mv[:80]}")
    s3.tempo_segundos = time.time() - t0; _step(s3)

    # P4: CADEIA DE VALOR
    _prog(0.28, "🔗 Passo 4/10: Cadeia de Valor...")
    t0 = time.time()
    s4 = PipelineStepResult(4, "Cadeia de Valor", "🔗", "running")
    raw_cad = agent_cadeia_valor(client, empresa_alvo, raw_ops)
    d.cadeia_valor = _parse_cadeia(raw_cad)
    cv = d.cadeia_valor
    s4.status = "success"; s4.confianca = cv.confianca
    s4.resumo = f"{cv.posicao_cadeia} | {cv.integracao_vertical_nivel} | Export: {'Sim' if cv.exporta else 'Nao'}"
    s4.detalhes = [f"Clientes: {_sj(cv.clientes_principais, 3) or 'N/I'}",
                   f"Certif: {_sj(cv.certificacoes) or 'Nenhuma'}"]
    s4.tempo_segundos = time.time() - t0; _step(s4)

    # P5: GRUPO ECONOMICO
    _prog(0.36, "🏛️ Passo 5/10: Grupo Economico...")
    t0 = time.time()
    s5 = PipelineStepResult(5, "Grupo Economico", "🏛️", "running")
    raw_grp = agent_grupo_economico(client, empresa_alvo, d.cnpj)
    d.grupo_economico = _parse_grupo(raw_grp)
    g = d.grupo_economico
    s5.status = "success"; s5.confianca = g.confianca
    nfil = len(g.cnpjs_filiais); ncol = len(g.cnpjs_coligadas)
    s5.resumo = f"{g.total_empresas} empresas | {nfil} filiais | {ncol} coligadas"
    s5.detalhes = [f"Controladores: {_sj(g.controladores, 3) or 'N/I'}"]
    if g.holding_controladora: s5.detalhes.append(f"Holding: {g.holding_controladora}")
    s5.tempo_segundos = time.time() - t0; _step(s5)

    # P6: INTEL MERCADO
    _prog(0.44, "📡 Passo 6/10: Intel de Mercado...")
    t0 = time.time()
    s6 = PipelineStepResult(6, "Intel de Mercado", "📡", "running")
    cnae = d.dados_cnpj.cnae_principal if d.dados_cnpj else ""
    uf = d.dados_cnpj.uf if d.dados_cnpj else (d.dados_operacionais.regioes_atuacao[0] if d.dados_operacionais.regioes_atuacao else "")
    ctx = enriquecer_prompt_com_contexto(cnae, uf)
    raw_int = agent_intel_mercado(client, empresa_alvo, ctx)
    d.intel_mercado = _parse_intel(raw_int)
    il = d.intel_mercado
    s6.status = "success"; s6.confianca = il.confianca
    s6.resumo = f"{len(il.noticias_recentes)} noticias | {len(il.sinais_compra)} sinais | {len(il.riscos)} riscos"
    for sc in il.sinais_compra[:2]: s6.detalhes.append(f"🟢 {sc[:60]}")
    s6.tempo_segundos = time.time() - t0; _step(s6)

    # P7: PROFILER DECISORES
    _prog(0.52, "👔 Passo 7/10: Profiler de Decisores...")
    t0 = time.time()
    s7 = PipelineStepResult(7, "Profiler Decisores", "👔", "running")
    raw_dec = agent_profiler_decisores(client, empresa_alvo, ng)
    d.decisores = raw_dec
    decs = raw_dec.get('decisores', [])
    s7.status = "success"; s7.confianca = raw_dec.get('confianca', 0)
    s7.resumo = f"{len(decs)} decisores | Estrutura: {raw_dec.get('estrutura_decisao','N/I')}"
    for dec in decs[:3]: s7.detalhes.append(f"👤 {dec.get('nome','')} — {dec.get('cargo','')}")
    s7.tempo_segundos = time.time() - t0; _step(s7)

    # P8: TECH STACK
    _prog(0.60, "💻 Passo 8/10: Tech Stack Hunter...")
    t0 = time.time()
    s8 = PipelineStepResult(8, "Tech Stack", "💻", "running")
    raw_tech = agent_tech_stack(client, empresa_alvo, ng)
    d.tech_stack = raw_tech
    erp_info = raw_tech.get('erp_principal', {})
    s8.status = "success"; s8.confianca = raw_tech.get('confianca', 0)
    s8.resumo = f"ERP: {erp_info.get('sistema','N/I')} | TI: {raw_tech.get('nivel_maturidade_ti','N/I')}"
    for ot in raw_tech.get('outros_sistemas', [])[:3]:
        s8.detalhes.append(f"→ {ot.get('tipo','')}: {ot.get('sistema','')}")
    for vg in raw_tech.get('vagas_ti_abertas', [])[:2]:
        s8.detalhes.append(f"📋 Vaga: {vg.get('titulo','')} ({_sj(vg.get('sistemas_mencionados',[]), 2)})")
    s8.tempo_segundos = time.time() - t0; _step(s8)

    # P8.5: SCORE SAS
    _prog(0.68, "📊 Calculando Score...")
    dados_m = d.merge_dados()
    dados_m['decisores'] = raw_dec
    dados_m['tech_stack'] = raw_tech
    dados_m['grupo_economico'] = {'total_empresas': g.total_empresas}
    dados_m['cadeia_valor'] = {'exporta': cv.exporta, 'certificacoes': cv.certificacoes}
    dados_m['natureza_juridica'] = d.dados_cnpj.natureza_juridica if d.dados_cnpj else ''
    dados_m['qsa_count'] = len(d.dados_cnpj.qsa) if d.dados_cnpj else 0
    d.sas_result = calcular_sas(dados_m)
    _log(f"Score: {d.sas_result.score}/1000 — {d.sas_result.tier.value}")

    # P9: ANALISE ESTRATEGICA
    _prog(0.72, "🧠 Passo 9/10: Analise Estrategica (Deep Thinking)...")
    t0 = time.time()
    s9 = PipelineStepResult(9, "Analise Estrategica", "🧠", "running")
    dados_a = dados_m.copy()
    dados_a['intel'] = {'noticias': il.noticias_recentes, 'sinais': il.sinais_compra,
                        'dores': il.dores_identificadas, 'oportunidades': il.oportunidades}
    sas_d = {'score': d.sas_result.score, 'tier': d.sas_result.tier.value, 'breakdown': d.sas_result.breakdown.to_dict()}
    texto = agent_analise_estrategica(client, dados_a, sas_d, ctx)
    d.analise_bruta = texto
    d.secoes_analise = _parse_secoes(texto)
    d.modelo_usado = "Senior Scout 360 Intelligence Platform"
    nw = sum(len(s.conteudo.split()) for s in d.secoes_analise)
    s9.status = "success"; s9.resumo = f"{len(d.secoes_analise)} secoes | {nw} palavras"
    s9.tempo_segundos = time.time() - t0; _step(s9)

    # P10: QUALITY GATE
    _prog(0.90, "✅ Passo 10/10: Quality Gate...")
    t0 = time.time()
    s10 = PipelineStepResult(10, "Quality Gate", "✅", "running")
    d.quality_report = executar_quality_gate(d)
    try:
        ai = agent_auditor_qualidade(client, texto, dados_a)
        d.quality_report.audit_ia = ai
        d.quality_report.recomendacoes.extend(ai.get('recomendacoes', []))
    except Exception: pass
    s10.status = "success"
    s10.resumo = f"{d.quality_report.nivel.value} ({d.quality_report.score_qualidade:.0f}%)"
    s10.tempo_segundos = time.time() - t0; _step(s10)

    d.tempo_total_segundos = time.time() - start
    d.timestamp_geracao = time.strftime("%Y-%m-%d %H:%M:%S")
    _prog(1.0, "🎯 Dossie completo!")
    return d
