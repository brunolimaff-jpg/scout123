"""
services/market_estimator.py — SAS 4.0 Full (12+ faixas, todas verticais)
"""
import math
from typing import Optional
from scout_types import SASResult, SASBreakdown, Tier, Verticalizacao


def _lk_capital(v: float) -> tuple[int, str]:
    if v >= 500_000_000: return 200, f"R${v/1e6:.0f}M → Mega Corporação"
    if v >= 200_000_000: return 190, f"R${v/1e6:.0f}M → Corporação"
    if v >= 100_000_000: return 175, f"R${v/1e6:.0f}M → Grande Empresa"
    if v >= 50_000_000:  return 150, f"R${v/1e6:.0f}M → Empresa Consolidada"
    if v >= 20_000_000:  return 120, f"R${v/1e6:.0f}M → Médio-Grande"
    if v >= 10_000_000:  return 100, f"R${v/1e6:.0f}M → Média Empresa"
    if v >= 5_000_000:   return 70,  f"R${v/1e6:.1f}M → PME Robusta"
    if v >= 2_000_000:   return 50,  f"R${v/1e6:.1f}M → PME"
    if v >= 1_000_000:   return 40,  f"R${v/1e6:.1f}M → Pequena"
    if v >= 500_000:     return 25,  f"R${v/1e3:.0f}k → Micro-Pequena"
    if v > 0:            return 10,  f"R${v/1e3:.0f}k → Micro"
    return 0, "Sem dados de capital"

def _lk_hectares(v: int) -> tuple[int, str]:
    if v >= 200_000: return 200, f"{v:,}ha → Mega-operação"
    if v >= 100_000: return 195, f"{v:,}ha → Gigante"
    if v >= 50_000:  return 180, f"{v:,}ha → Muito Grande"
    if v >= 20_000:  return 150, f"{v:,}ha → Grande"
    if v >= 10_000:  return 130, f"{v:,}ha → Consolidado"
    if v >= 5_000:   return 100, f"{v:,}ha → Médio-Grande"
    if v >= 3_000:   return 80,  f"{v:,}ha → Médio"
    if v >= 1_000:   return 50,  f"{v:,}ha → Pequeno-Médio"
    if v >= 500:     return 30,  f"{v:,}ha → Pequeno"
    if v > 0:        return 10,  f"{v:,}ha → Micro"
    return 0, "Sem dados de área"

def _lk_cultura(culturas: list[str]) -> tuple[int, str]:
    if not culturas:
        return 50, "Culturas não identificadas"
    txt = " ".join(culturas).lower()
    scores = {
        "cana": 150, "usina": 150, "semente": 140, "sementes": 140,
        "algod": 130, "café": 125, "cafe": 125, "citrus": 120, "laranja": 120,
        "alho": 120, "batata": 115, "hf": 110, "hortifruti": 110,
        "pecuária": 105, "pecuaria": 105, "gado": 105, "boi": 105, "leite": 100,
        "aves": 110, "frango": 110, "suínos": 110, "suinos": 110,
        "camarão": 110, "peixe": 105, "tilapia": 105,
        "eucalipto": 100, "pinus": 100, "celulose": 120, "florestal": 100,
        "soja": 80, "milho": 80, "trigo": 75, "arroz": 75,
        "feijão": 60, "feijao": 60, "fumo": 90, "tabaco": 90,
        "cacau": 100, "dendê": 95, "dende": 95, "palma": 95,
    }
    best, label = 50, "Culturas genéricas"
    for kw, sc in scores.items():
        if kw in txt and sc > best:
            best, label = sc, f"Cultura: {kw}"
    n = len(set(culturas))
    if n >= 5:
        best = min(best + 40, 150)
        label += f" +{n} culturas (altamente diversificado)"
    elif n >= 3:
        best = min(best + 20, 150)
        label += f" +{n} culturas"
    return best, label

def _lk_vert(vert) -> tuple[int, str]:
    if vert is None:
        return 0, "Sem dados"
    pts_map = {
        'agroindustria': 35, 'usina_acucar_etanol': 40, 'destilaria': 30,
        'esmagadora_soja': 35, 'refinaria_oleo': 30, 'fabrica_biodiesel': 25,
        'torrefacao_cafe': 25, 'beneficiamento_arroz': 20, 'fabrica_sucos': 25,
        'vinicultura': 20, 'frigorifico_bovino': 35, 'frigorifico_aves': 35,
        'frigorifico_suinos': 30, 'frigorifico_peixes': 25, 'laticinio': 30,
        'fabrica_racao': 25, 'incubatorio': 20,
        'silos': 20, 'armazens_gerais': 15, 'terminal_portuario': 30,
        'ferrovia_propria': 25, 'frota_propria': 10,
        'algodoeira': 25, 'sementeira': 25, 'ubs': 20, 'secador': 10,
        'fabrica_fertilizantes': 30, 'fabrica_defensivos': 25,
        'laboratorio_genetica': 20, 'central_inseminacao': 15, 'viveiro_mudas': 10,
        'cogeracao_energia': 30, 'usina_solar': 15, 'biodigestor': 20,
        'planta_biogas': 20, 'creditos_carbono': 15,
        'florestal_eucalipto': 15, 'florestal_pinus': 10,
        'fabrica_celulose': 35, 'serraria': 15,
        'pivos_centrais': 15, 'irrigacao_gotejamento': 10, 'barragem_propria': 15,
        'agricultura_precisao': 15, 'drones_proprios': 10,
        'estacoes_meteorologicas': 5, 'telemetria_frota': 10, 'erp_implantado': 10,
    }
    pts, labels = 0, []
    for campo, val in pts_map.items():
        if getattr(vert, campo, False):
            pts += val
            labels.append(campo)
    pts = min(pts, 100)
    return pts, ", ".join(labels[:5]) + (f" +{len(labels)-5} mais" if len(labels) > 5 else "") if labels else "Não verticalizado"

def _lk_funcs(v: int) -> tuple[int, str]:
    if v >= 2000: return 200, f"{v:,} funcs → Mega empregador"
    if v >= 1000: return 180, f"{v:,} funcs → Corporação"
    if v >= 500:  return 150, f"{v:,} funcs → Grande"
    if v >= 200:  return 120, f"{v:,} funcs → Médio-Grande"
    if v >= 100:  return 90,  f"{v:,} funcs → Médio"
    if v >= 50:   return 60,  f"{v:,} funcs → Pequeno-Médio"
    if v >= 20:   return 30,  f"{v:,} funcs → Pequeno"
    if v > 0:     return 15,  f"{v} funcs → Micro"
    return 0, "Sem dados"

def _lk_gov(d: dict) -> tuple[int, str]:
    pts, labels = 0, []
    all_fin = " ".join(str(d.get(k, '')) for k in
                       ['movimentos_financeiros', 'fiagros', 'cras', 'parceiros_financeiros']).lower()
    if 'fiagro' in all_fin: pts += 35; labels.append("Fiagro")
    if 'cra' in all_fin: pts += 30; labels.append("CRA")
    if 'auditoria' in all_fin or d.get('governanca'): pts += 25; labels.append("Governança")
    if any(x in all_fin for x in ['xp', 'suno', 'valora', 'itaú', 'btg', 'bndes']): pts += 20; labels.append("Parceiro financeiro")
    techs = str(d.get('tecnologias', '')).lower()
    if any(x in techs for x in ['erp', 'senior', 'sap', 'totvs']): pts += 15; labels.append("ERP")
    if any(x in techs for x in ['precisão', 'drone', 'telemetria', 'iot']): pts += 10; labels.append("Ag-tech")
    nat = str(d.get('natureza_juridica', '')).lower()
    if 's.a.' in nat or 'anônima' in nat or 'anonima' in nat: pts += 20; labels.append("S.A.")
    qsa = d.get('qsa_count', 0)
    if qsa >= 5: pts += 10; labels.append(f"QSA:{qsa}")
    grp = d.get('grupo_economico', {})
    if grp.get('total_empresas', 0) >= 3: pts += 15; labels.append(f"Grupo:{grp['total_empresas']} empresas")
    cadeia = d.get('cadeia_valor', {})
    if cadeia.get('exporta'): pts += 10; labels.append("Exportador")
    if len(cadeia.get('certificacoes', [])) >= 2: pts += 10; labels.append("Certificado")
    return min(pts, 150), "; ".join(labels) if labels else "Sem sinais"


def _heuristic(d: dict) -> tuple[dict, list[str]]:
    inf = []
    ha = d.get('hectares_total', 0)
    if d.get('funcionarios_estimados', 0) == 0 and ha > 0:
        ct = " ".join(d.get('culturas', [])).lower()
        f = 120 if any(x in ct for x in ['cana', 'batata', 'alho', 'semente', 'hf', 'café', 'cafe']) else \
            200 if any(x in ct for x in ['algod', 'laranja', 'citrus', 'café']) else 350
        est = max(math.ceil(ha / f), d.get('cabecas_gado', 0) // 500 or 0)
        if d.get('cabecas_aves', 0) > 0:
            est += d['cabecas_aves'] // 50000
        d['funcionarios_estimados'] = est
        inf.append(f"Funcs estimados: ~{est}")
    if d.get('capital_social_estimado', 0) == 0 and ha > 0:
        r = str(d.get('regioes_atuacao', '')).lower()
        vha = 5000 if any(x in r for x in ['sp', 'pr', 'rs']) else 3500 if any(x in r for x in ['mt', 'ba', 'go']) else 2500
        d['capital_social_estimado'] = ha * vha
        inf.append(f"Capital estimado: R${ha*vha/1e6:.1f}M")
    if d.get('faturamento_estimado', 0) == 0 and ha > 0:
        d['faturamento_estimado'] = ha * 5000
        inf.append(f"Faturamento estimado: R${ha*5000/1e6:.1f}M")
    return d, inf


def calcular_sas(dados: dict) -> SASResult:
    dados, inf = _heuristic(dados)
    just = list(inf)

    cap_p, cap_l = _lk_capital(dados.get('capital_social_estimado', 0) or dados.get('capital_social', 0))
    hec_p, hec_l = _lk_hectares(dados.get('hectares_total', 0))
    musculo = min(cap_p + hec_p, 400)
    just.append(f"Músculo: {cap_l} ({cap_p}) + {hec_l} ({hec_p}) = {musculo}/400")

    cul_p, cul_l = _lk_cultura(dados.get('culturas', []))
    ver_p, ver_l = _lk_vert(dados.get('verticalizacao'))
    complexidade = min(cul_p + ver_p, 250)
    just.append(f"Complexidade: {cul_l} ({cul_p}) + Vert ({ver_p}) = {complexidade}/250")

    fun_p, fun_l = _lk_funcs(dados.get('funcionarios_estimados', 0))
    gente = min(fun_p, 200)
    just.append(f"Gente: {fun_l} = {gente}/200")

    gov_p, gov_l = _lk_gov(dados)
    momento = min(gov_p, 150)
    just.append(f"Momento: {gov_l} = {momento}/150")

    total = musculo + complexidade + gente + momento
    tier = Tier.DIAMANTE if total >= 751 else Tier.OURO if total >= 501 else Tier.PRATA if total >= 251 else Tier.BRONZE

    return SASResult(score=total, tier=tier,
                     breakdown=SASBreakdown(musculo=musculo, complexidade=complexidade, gente=gente, momento=momento),
                     dados_inferidos=len(inf) > 0, justificativas=just)
