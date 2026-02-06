"""
services/market_estimator.py — SAS 5.0 Engine (Verticais, Confidence, Recomendacao)
Baseado no motor Realpolitik com verticais GRAOS/BIOENERGIA/SEMENTES/PECUARIA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import math
from typing import Optional
from scout_types import SASResult, SASBreakdown, Tier, Verticalizacao

# ==========================================
# SCORING CONFIG POR VERTICAL
# ==========================================
SCORING_CONFIG = {
    "GRAOS": {
        "musculo": {
            "hectares": [(70000,200),(20000,150),(5000,100),(1000,50)],
            "capital": [(200000000,150),(80000000,110),(20000000,50)],
        },
        "complexidade": {
            "signals": {"tem_algodao":80,"tem_irrigacao":40,"tem_silos":40,"tem_agroindustria":30},
            "base": 30,
        },
        "confidence": {"hectares":30,"capital_social":20,"vertical":20,"cnpj":15,"basic":15},
    },
    "BIOENERGIA": {
        "musculo": {
            "moagem": [(4000000,200),(2000000,150),(1000000,100)],
            "capital": [(200000000,150),(50000000,100)],
        },
        "complexidade": {
            "signals": {"tem_agroindustria":70,"certificacao_renovabio":50,"tem_silos":30},
            "base": 50,
        },
        "confidence": {"moagem":35,"capital_social":20,"basic":45},
    },
    "SEMENTES": {
        "musculo": {
            "capital_primary": [(80000000,200),(20000000,150),(5000000,80)],
        },
        "complexidade": {
            "signals": {"tem_hub_royalties":90,"tem_laboratorio":50,"renasem_ativo":40,"tem_silos":30},
            "base": 40,
        },
        "confidence": {"renasem":30,"capital_social":30,"hub":20,"basic":20},
    },
    "PECUARIA": {
        "musculo": {
            "cabecas": [(20000,200),(10000,150),(5000,100)],
            "capital": [(50000000,150),(10000000,80)],
        },
        "complexidade": {
            "signals": {"tem_boitel":100,"tem_fabrica_racao":60,"tem_confinamento":40},
            "base": 10,
        },
        "confidence": {"cabecas":35,"boitel":25,"capital_social":20,"basic":20},
    },
}

CAPS = {"musculo": 400, "complexidade": 250, "gente": 200, "momento": 150}

# ==========================================
# HELPERS
# ==========================================
def _lookup(value, thresholds):
    for threshold, points in thresholds:
        if value >= threshold:
            return points
    return 0

def _detect_vertical(dados):
    """Detecta vertical com base nos dados disponveis."""
    vert = dados.get('verticalizacao')
    culturas = " ".join(dados.get('culturas', [])).lower()
    has_graos = any(x in culturas for x in ['soja', 'milho', 'algod', 'sorgo', 'trigo', 'feijao'])
    has_cana = 'cana' in culturas
    # Pure bioenergia: cana without grains
    if has_cana and not has_graos:
        return "BIOENERGIA"
    # Pecuaria
    if dados.get('cabecas_gado', 0) > 1000:
        return "PECUARIA"
    if vert and (getattr(vert, 'frigorifico_bovino', False) or getattr(vert, 'frigorifico_aves', False)):
        if not has_graos: return "PECUARIA"
    # Sementes
    if vert and (getattr(vert, 'sementeira', False) or getattr(vert, 'laboratorio_genetica', False)):
        if not has_graos: return "SEMENTES"
    # Default: GRAOS (covers mixed agro+industrial like Alvorada)
    return "GRAOS"

def _compute_musculo(dados, v_config):
    pts = 0
    just = []
    # Hectares
    ha = dados.get('hectares_total', 0)
    if ha > 0 and "hectares" in v_config.get("musculo", {}):
        p = _lookup(ha, v_config["musculo"]["hectares"])
        pts = max(pts, p)
        just.append(f"{ha:,}ha={p}pts")
    # Capital
    cap = dados.get('capital_social_estimado', 0) or dados.get('capital_social', 0)
    if cap > 0:
        for key in ["capital", "capital_primary"]:
            if key in v_config.get("musculo", {}):
                p = _lookup(cap, v_config["musculo"][key])
                if key == "capital_primary":
                    pts = max(pts, p)
                else:
                    pts = max(pts, p)
                just.append(f"R${cap/1e6:.0f}M={p}pts")
                break
    # Cabecas gado
    cab = dados.get('cabecas_gado', 0)
    if cab > 0 and "cabecas" in v_config.get("musculo", {}):
        p = _lookup(cab, v_config["musculo"]["cabecas"])
        pts = max(pts, p)
        just.append(f"{cab:,}cab={p}pts")
    # Moagem
    moag = dados.get('moagem_ton', 0)
    if moag > 0 and "moagem" in v_config.get("musculo", {}):
        p = _lookup(moag, v_config["musculo"]["moagem"])
        pts = max(pts, p)
        just.append(f"{moag:,}ton={p}pts")
    return min(pts, CAPS["musculo"]), "; ".join(just) or "Sem dados"

def _compute_complexidade(dados, v_config):
    c = v_config.get("complexidade", {})
    score = c.get("base", 0)
    labels = []
    vert = dados.get('verticalizacao')
    # Signals from config
    for signal, weight in c.get("signals", {}).items():
        val = False
        if vert and hasattr(vert, signal):
            val = getattr(vert, signal, False)
        elif dados.get(signal):
            val = True
        # Derive from culturas
        if signal == "tem_algodao" and not val:
            val = "algod" in " ".join(dados.get('culturas', [])).lower()
        if signal == "tem_irrigacao" and not val and vert:
            val = getattr(vert, 'pivos_centrais', False) or getattr(vert, 'irrigacao_gotejamento', False)
        if val:
            score += weight
            labels.append(f"{signal}(+{weight})")
    # Extra vert bonus (beyond config signals)
    if vert:
        extra_map = {
            'silos':15,'armazens_gerais':15,'terminal_portuario':25,'frota_propria':15,
            'algodoeira':25,'sementeira':20,'secador':10,
            'usina_acucar_etanol':35,'destilaria':25,'esmagadora_soja':30,
            'fabrica_biodiesel':25,'fabrica_racao':20,'cogeracao_energia':25,
            'frigorifico_bovino':30,'frigorifico_aves':25,'laticinio':20,
            'fabrica_celulose':30,'creditos_carbono':15,
            'agricultura_precisao':10,'drones_proprios':8,'telemetria_frota':8,
        }
        for campo, val in extra_map.items():
            if getattr(vert, campo, False) and campo not in [s for s in c.get("signals", {})]:
                score += val
                labels.append(campo)
    return min(score, CAPS["complexidade"]), "; ".join(labels[:6]) or "Baixa complexidade"

def _compute_gente(dados):
    funcs = dados.get('funcionarios_estimados', 0)
    score = _lookup(funcs, [(2000,200),(1000,180),(500,150),(200,120),(100,90),(50,60),(20,30)])
    # Natureza juridica
    nat = str(dados.get('natureza_juridica', '')).lower()
    if 's.a.' in nat or 'anonima' in nat:
        score += 80
    elif 'ltda' in nat:
        score += 30
        cap = dados.get('capital_social_estimado', 0) or dados.get('capital_social', 0)
        if cap > 50_000_000:
            score += 40  # Governanca familiar
    label = f"{funcs:,} funcs" if funcs else "N/I"
    return min(score, CAPS["gente"]), label

def _compute_momento(dados):
    score = 0
    labels = []
    # Vagas TI
    vagas = 0
    ts = dados.get('tech_stack', {})
    if ts:
        vagas = len(ts.get('vagas_ti_abertas', []))
    score += _lookup(vagas, [(4,60),(1,30)])
    if vagas: labels.append(f"{vagas} vagas TI")
    # Dominio/conectividade
    techs = " ".join(str(x) for x in dados.get('tecnologias_identificadas', [])).lower()
    if any(x in techs for x in ['site', 'dominio', 'web']): score += 20; labels.append("Dominio")
    if any(x in techs for x in ['conectividade', 'fibra', 'starlink', 'internet']): score += 40; labels.append("Conectividade")
    # SA bonus
    nat = str(dados.get('natureza_juridica', '')).lower()
    if 's.a.' in nat or 'anonima' in nat: score += 30; labels.append("S.A.")
    # Financial governance signals
    govs = " ".join(str(d) for d in [datos.get('movimentos_financeiros',''), datos.get('fiagros',''),
                                      datos.get('cras',''), datos.get('parceiros_financeiros','')]).lower() \
        if (datos := dados) else ""
    if 'fiagro' in govs: score += 25; labels.append("Fiagro")
    if 'cra' in govs: score += 20; labels.append("CRA")
    if any(x in govs for x in ['auditoria','kpmg','ey','deloitte','pwc']): score += 15; labels.append("Auditoria")
    # Grupo economico
    grp = dados.get('grupo_economico', {})
    if isinstance(grp, dict) and grp.get('total_empresas', 0) >= 5: score += 15; labels.append(f"Grupo {grp['total_empresas']}emp")
    # Exportacao
    cadeia = dados.get('cadeia_valor', {})
    if isinstance(cadeia, dict) and cadeia.get('exporta'): score += 10; labels.append("Exporta")
    return min(score, CAPS["momento"]), "; ".join(labels) or "Sem sinais"

def _compute_confidence(dados, v_config):
    """Compute confidence score 0-100 based on available data."""
    total_w = 0
    found_w = 0
    checks = {
        "hectares": dados.get('hectares_total', 0) > 0,
        "capital_social": (dados.get('capital_social_estimado', 0) or dados.get('capital_social', 0)) > 0,
        "vertical": True,  # always have vertical
        "cnpj": bool(dados.get('cnpj') or dados.get('razao_social')),
        "basic": bool(dados.get('razao_social')),
        "moagem": dados.get('moagem_ton', 0) > 0,
        "cabecas": dados.get('cabecas_gado', 0) > 0,
        "renasem": bool(dados.get('renasem_ativo')),
        "hub": bool(dados.get('tem_hub_royalties')),
        "boitel": bool(dados.get('tem_boitel')),
    }
    for field, w in v_config.get("confidence", {}).items():
        total_w += w
        if checks.get(field, False):
            found_w += w
    return (found_w / total_w * 100) if total_w > 0 else 50

def _heuristic(d):
    inf = []
    ha = d.get('hectares_total', 0)
    if d.get('funcionarios_estimados', 0) == 0 and ha > 0:
        ct = " ".join(d.get('culturas', [])).lower()
        f = 120 if any(x in ct for x in ['cana','semente','hf','cafe']) else 200 if 'algod' in ct else 350
        est = max(math.ceil(ha / f), d.get('cabecas_gado', 0) // 500 or 0)
        if d.get('cabecas_aves', 0) > 0: est += d['cabecas_aves'] // 50000
        d['funcionarios_estimados'] = est
        inf.append(f"Funcs estimados: ~{est}")
    if d.get('capital_social_estimado', 0) == 0 and ha > 0:
        vha = 3500
        d['capital_social_estimado'] = ha * vha
        inf.append(f"Capital estimado: R${ha*vha/1e6:.1f}M")
    return d, inf


# ==========================================
# MAIN
# ==========================================
def calcular_sas(dados: dict) -> SASResult:
    dados, inf = _heuristic(dados)
    just = list(inf)

    # Detect vertical
    vertical = _detect_vertical(dados)
    v_config = SCORING_CONFIG.get(vertical, SCORING_CONFIG["GRAOS"])

    # Compute pillars
    musc, musc_l = _compute_musculo(dados, v_config)
    comp, comp_l = _compute_complexidade(dados, v_config)
    gent, gent_l = _compute_gente(dados)
    mome, mome_l = _compute_momento(dados)

    just.append(f"Vertical: {vertical}")
    just.append(f"Musculo: {musc_l} = {musc}/{CAPS['musculo']}")
    just.append(f"Complexidade: {comp_l} = {comp}/{CAPS['complexidade']}")
    just.append(f"Gente: {gent_l} = {gent}/{CAPS['gente']}")
    just.append(f"Momento: {mome_l} = {mome}/{CAPS['momento']}")

    raw = musc + comp + gent + mome

    # Confidence penalty
    conf = _compute_confidence(dados, v_config)
    penalty = 1.0
    if conf < 30: penalty = 0.5
    elif conf < 50: penalty = 0.75
    elif conf < 70: penalty = 0.90
    score = int(raw * penalty)
    if penalty < 1.0:
        just.append(f"Confidence: {conf:.0f}% -> penalty {penalty}")

    # Tier
    tier = Tier.DIAMANTE if score >= 751 else Tier.OURO if score >= 501 else Tier.PRATA if score >= 251 else Tier.BRONZE

    # Recomendacao comercial (Fit Matrix)
    mc = musc + comp
    gm = gent + mome
    if mc > 400 and gm > 250:
        reco = "BALEIA IDEAL (Field Sales)"
    elif comp > 150 and musc < 200:
        reco = "DOR LATENTE (Inside Sales)"
    elif musc > 250 and comp < 100:
        reco = "GIGANTE INERTE (Nutrir/Mkt)"
    elif gm > 250:
        reco = "TECH FIT (Governanca)"
    else:
        reco = "OPORTUNIDADE (Qualificacao)"

    return SASResult(
        score=score, tier=tier,
        breakdown=SASBreakdown(musculo=musc, complexidade=comp, gente=gent, momento=mome),
        dados_inferidos=len(inf) > 0, justificativas=just,
        confidence_score=conf, recomendacao_comercial=reco, vertical_detectada=vertical,
    )
