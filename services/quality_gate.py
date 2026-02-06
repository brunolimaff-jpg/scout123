"""
services/quality_gate.py — Auditor de Qualidade Determinístico
"""
import time
from scout_types import QualityReport, QualityCheck, QualityLevel, DossieCompleto


def executar_quality_gate(d: DossieCompleto) -> QualityReport:
    checks = []

    # 1. Cadastrais
    t = sum([d.dados_cnpj is not None, bool(d.dados_cnpj and d.dados_cnpj.razao_social),
             bool(d.dados_cnpj and d.dados_cnpj.cnae_principal)])
    checks.append(QualityCheck("Dados Cadastrais (CNPJ)", t >= 2, f"{t}/3", 1.0))

    # 2. Operacionais
    o = d.dados_operacionais
    t = sum([o.hectares_total > 0, len(o.culturas) > 0, len(o.regioes_atuacao) > 0, o.confianca >= 0.5])
    checks.append(QualityCheck("Dados Operacionais", t >= 2, f"{t}/4 | Conf: {o.confianca:.0%}", 1.5))

    # 3. Financeiros
    f = d.dados_financeiros
    t = sum([f.capital_social_estimado > 0, f.funcionarios_estimados > 0,
             len(f.movimentos_financeiros) > 0, f.governanca_corporativa or len(f.auditorias) > 0])
    checks.append(QualityCheck("Dados Financeiros", t >= 2, f"{t}/4 | {len(f.movimentos_financeiros)} movimentos", 1.5))

    # 4. Cadeia de valor
    cv = d.cadeia_valor
    t = sum([bool(cv.posicao_cadeia), len(cv.clientes_principais) > 0,
             bool(cv.integracao_vertical_nivel), cv.confianca >= 0.4])
    checks.append(QualityCheck("Cadeia de Valor", t >= 2, f"{t}/4 | Conf: {cv.confianca:.0%}", 1.0))

    # 5. Grupo econômico
    g = d.grupo_economico
    checks.append(QualityCheck("Grupo Econômico", g.total_empresas > 0,
                                f"{g.total_empresas} empresas | {len(g.controladores)} controladores", 0.8))

    # 6. Análise
    sec = d.secoes_analise
    nw = sum(len(s.conteudo.split()) for s in sec)
    checks.append(QualityCheck("Análise Estratégica", len(sec) >= 3 and nw >= 500,
                                f"{len(sec)} seções | {nw} palavras", 2.0))

    # 7. Score
    checks.append(QualityCheck("Score SAS 4.0", d.sas_result.score > 0,
                                f"{d.sas_result.score}/1000 ({d.sas_result.tier.value})", 1.0))

    tp = sum(c.peso for c in checks)
    sp = sum(c.peso * (1.0 if c.passou else 0.0) for c in checks) / tp * 100

    nivel = (QualityLevel.EXCELENTE if sp >= 85 else QualityLevel.BOM if sp >= 65
             else QualityLevel.ACEITAVEL if sp >= 45 else QualityLevel.INSUFICIENTE)

    recs = [f"⚠️ {c.criterio}: {c.nota}" for c in checks if not c.passou]

    return QualityReport(nivel=nivel, score_qualidade=sp, checks=checks,
                          recomendacoes=recs, timestamp=str(time.time()))