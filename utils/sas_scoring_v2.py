"""
utils/sas_scoring_v2.py — Motor de Cálculo SAS 4.0 v0.2
Calibrado para Ticket 500k / Ciclo 90 dias

Mudanças principais vs v0.1:
- Pecuária REMOVIDA das verticals core
- Algodão separado como vertical própria (140 pts)
- Pesos rebalanceados: Músculo 350, Complexidade 250, Gente 220, Momento 180
- Tiers mais seletivos: Diamante 820+, Ouro 650+, Prata 430+
- Confiança com penalidade não-linear
- Big Fish condicional (capital + hectares + confiança)
"""
from scout_types import (
    SASResult, SASBreakdown, Tier, DossieCompleto,
    VERTICALS_CORE, PESOS_PILARES_V2, TIERS_V2,
    CNAE_ALGODAO, KEYWORDS_ALGODAO
)


def detectar_vertical(dossie: DossieCompleto) -> str:
    """
    Detecta a vertical principal (core para Senior XT ticket 500k+).

    Ordem de prioridade:
    1. Algodão (complexidade industrial - UBA, rastreabilidade)
    2. Bioenergia (usinas, destilarias)
    3. Sementes (multiplicação, royalties)
    4. Grãos (padrão)

    Pecuária foi REMOVIDA - não é core para ticket 500k+
    """
    op = dossie.dados_operacionais
    cnpj_data = dossie.dados_cnpj

    # 1. Algodão (complexidade industrial - nova categoria)
    cnae = cnpj_data.cnae_principal if cnpj_data else ""
    culturas_str = " ".join(op.culturas).lower() if op.culturas else ""

    if any(cnae.startswith(c) for c in CNAE_ALGODAO):
        return 'Algodão'
    if any(kw in culturas_str for kw in KEYWORDS_ALGODAO):
        return 'Algodão'
    if op.verticalizacao.algodoeira:
        return 'Algodão'

    # 2. Bioenergia
    if op.verticalizacao.usina_acucar_etanol or op.verticalizacao.destilaria:
        return 'Bioenergia'
    if 'cana' in culturas_str or 'etanol' in culturas_str or 'acucar' in culturas_str:
        return 'Bioenergia'

    # 3. Sementes
    if cnae and cnae.startswith('0119'):
        return 'Sementes'
    if op.verticalizacao.sementeira or op.verticalizacao.ubs:
        return 'Sementes'
    if 'semente' in culturas_str:
        return 'Sementes'

    # 4. Grãos (padrão)
    return 'Grãos'


def calcular_sas_v2(dossie: DossieCompleto) -> SASResult:
    """
    Motor de scoring SAS 4.0 v0.2 - Calibrado por vertical.

    Mudanças vs v0.1:
    - Pecuária excluída (não é core para ticket 500k)
    - Algodão como vertical própria (140 pts)
    - Pesos ajustados: menos Músculo, mais Gente/Momento
    - Tiers mais seletivos (Diamante 820+)
    - Confiança não-linear

    Pilares:
    - Músculo: 350 pts (capacidade financeira e física)
    - Complexidade: 250 pts (vertical + operações)
    - Gente: 220 pts (governança + CLT)
    - Momento: 180 pts (TI + digital)
    + Bônus S.A.: 30 pts
    = Máx: 1000 pts
    """

    op = dossie.dados_operacionais
    fi = dossie.dados_financeiros
    cnpj_data = dossie.dados_cnpj
    cv = dossie.cadeia_valor
    gr = dossie.grupo_economico
    ts = dossie.tech_stack or {}

    breakdown = SASBreakdown()
    justificativas = []

    # ========================================================================
    # PILAR 1: MÚSCULO (350 pts máx - reduzido de 400)
    # ========================================================================

    # Capital Social (ajustado para ticket 500k)
    capital = fi.capital_social_estimado or (cnpj_data.capital_social if cnpj_data else 0)

    if capital >= 200_000_000:
        breakdown.musculo += 200
        justificativas.append(f"💰 Capital Social R${capital/1e6:.0f}M → 200 pts")
    elif capital >= 80_000_000:
        breakdown.musculo += 160
        justificativas.append(f"💰 Capital Social R${capital/1e6:.0f}M → 160 pts")
    elif capital >= 20_000_000:
        breakdown.musculo += 110
        justificativas.append(f"💰 Capital Social R${capital/1e6:.0f}M → 110 pts")
    elif capital >= 5_000_000:
        breakdown.musculo += 50
        justificativas.append(f"💰 Capital Social R${capital/1e6:.0f}M → 50 pts")
    else:
        justificativas.append(f"⚪ Capital Social R${capital/1e6:.1f}M → 0 pts")

    # Hectares (ajustado para distribuição MT/MS/BA)
    hectares = op.hectares_total

    if hectares >= 70_000:
        breakdown.musculo += 150
        justificativas.append(f"🌾 Hectares {hectares:,} ha → 150 pts")
    elif hectares >= 20_000:
        breakdown.musculo += 110
        justificativas.append(f"🌾 Hectares {hectares:,} ha → 110 pts")
    elif hectares >= 5_000:
        breakdown.musculo += 80
        justificativas.append(f"🌾 Hectares {hectares:,} ha → 80 pts")
    elif hectares >= 1_000:
        breakdown.musculo += 40
        justificativas.append(f"🌾 Hectares {hectares:,} ha → 40 pts")
    else:
        justificativas.append(f"⚪ Hectares {hectares:,} ha → 0 pts")

    # Cap máximo: 350 pts
    breakdown.musculo = min(breakdown.musculo, PESOS_PILARES_V2['musculo'])

    # ========================================================================
    # PILAR 2: COMPLEXIDADE (250 pts máx)
    # ========================================================================

    # Detectar vertical
    vertical = detectar_vertical(dossie)
    pts_vertical = VERTICALS_CORE.get(vertical, 80)
    breakdown.complexidade += pts_vertical
    justificativas.append(f"🎯 Vertical '{vertical}' → {pts_vertical} pts")

    # Verticalização (operações que agregam complexidade)
    vert = op.verticalizacao

    # Agroindústria (alto impacto)
    if vert.agroindustria or vert.usina_acucar_etanol or vert.algodoeira or vert.esmagadora_soja:
        breakdown.complexidade += 70
        justificativas.append("🏭 Agroindústria/Usina/Processamento → +70 pts")

    # Armazenagem (médio impacto)
    if vert.silos or vert.armazens_gerais:
        breakdown.complexidade += 40
        justificativas.append("🏗️ Silos/Armazéns → +40 pts")

    # Logística própria (médio impacto)
    if vert.frota_propria or vert.ferrovia_propria or vert.terminal_portuario:
        breakdown.complexidade += 30
        justificativas.append("🚛 Logística Própria (Frota/Ferrovia/Porto) → +30 pts")

    # Energia (médio impacto - RenovaBio, leilões)
    if vert.cogeracao_energia or vert.usina_solar or vert.biodigestor:
        breakdown.complexidade += 30
        justificativas.append("⚡ Energia (Cogeração/Solar/Biogás) → +30 pts")

    # Beneficiamento/Transformação
    if vert.fabrica_racao or vert.torrefacao_cafe or vert.fabrica_biodiesel:
        breakdown.complexidade += 25
        justificativas.append("🌾 Beneficiamento/Transformação → +25 pts")

    # Frigoríficos (proteína animal)
    if vert.frigorifico_bovino or vert.frigorifico_aves or vert.frigorifico_suinos:
        breakdown.complexidade += 50
        justificativas.append("🥩 Frigorífico → +50 pts")

    # Irrigação (gestão hídrica complexa)
    if vert.pivos_centrais or vert.irrigacao_gotejamento:
        pts_irrig = min(op.area_irrigada_ha // 1000 * 5, 20)
        if pts_irrig > 0:
            breakdown.complexidade += pts_irrig
            justificativas.append(f"💧 Irrigação ({op.area_irrigada_ha:,} ha) → +{pts_irrig} pts")

    # Bônus Sementeiro (fixo, não multiplicador como era antes)
    if vertical == 'Sementes':
        breakdown.complexidade += 25
        justificativas.append("🌱 Bônus Sementeiro (royalties/rastreabilidade) → +25 pts")

    # Cap máximo: 250 pts
    breakdown.complexidade = min(breakdown.complexidade, PESOS_PILARES_V2['complexidade'])

    # ========================================================================
    # PILAR 3: GENTE (220 pts máx - aumentado de 200)
    # ========================================================================

    # Funcionários (CLT = complexidade de RH)
    func = fi.funcionarios_estimados

    if func >= 500:
        breakdown.gente += 100
        justificativas.append(f"👥 Funcionários {func:,} → 100 pts")
    elif func >= 200:
        breakdown.gente += 75
        justificativas.append(f"👥 Funcionários {func:,} → 75 pts")
    elif func >= 100:
        breakdown.gente += 50
        justificativas.append(f"👥 Funcionários {func:,} → 50 pts")
    elif func >= 50:
        breakdown.gente += 25
        justificativas.append(f"👥 Funcionários {func:,} → 25 pts")
    else:
        justificativas.append(f"⚪ Funcionários {func} → 0 pts")

    # Governança (estrutura jurídica + CLT robusta)
    nat_jur = cnpj_data.natureza_juridica if cnpj_data else ""

    if 'S.A.' in nat_jur or 'S/A' in nat_jur or 'SOCIEDADE ANONIMA' in nat_jur.upper():
        breakdown.gente += 40
        justificativas.append("🏛️ Natureza S.A. → +40 pts (governança corporativa)")
    elif 'LTDA' in nat_jur.upper() and capital >= 20_000_000:
        # Reconhecer Holdings Familiares profissionalizadas
        breakdown.gente += 30
        justificativas.append("🏛️ Ltda Grande (Cap>20M) → +30 pts (governança familiar)")
    elif 'COOPERATIVA' in nat_jur.upper() and capital >= 50_000_000:
        # Grandes cooperativas (Coamo, Lar, etc)
        breakdown.gente += 35
        justificativas.append("🏛️ Cooperativa Grande → +35 pts")

    # Nome empresarial limpo (não é "MEI", "Familia", etc)
    razao = cnpj_data.razao_social if cnpj_data else ""
    if razao and not any(x in razao.lower() for x in ['familia', 'me ', 'mei', 'produtor rural']):
        breakdown.gente += 20
        justificativas.append("✅ Nome empresarial limpo → +20 pts")
    elif razao and any(x in razao.lower() for x in ['mei', 'me ']):
        breakdown.gente -= 10
        justificativas.append("⚠️ Nome MEI/ME → -10 pts")

    # Governança corporativa (auditorias, compliance)
    if fi.governanca_corporativa or fi.auditorias:
        breakdown.gente += 30
        justificativas.append("📋 Governança/Auditoria ativa → +30 pts")

    # QSA (Quadro Societário Administrativo)
    if cnpj_data and len(cnpj_data.qsa) >= 3:
        breakdown.gente += 10
        justificativas.append(f"👔 QSA estruturado ({len(cnpj_data.qsa)} membros) → +10 pts")

    # Cap máximo: 220 pts
    breakdown.gente = min(breakdown.gente, PESOS_PILARES_V2['gente'])

    # ========================================================================
    # PILAR 4: MOMENTO (180 pts máx - aumentado de 150)
    # ========================================================================

    # Natureza Jurídica (governança estratégica)
    if 'S.A.' in nat_jur or 'S/A' in nat_jur:
        breakdown.momento += 50
        justificativas.append("💎 S.A. (momento estratégico) → +50 pts")
    elif 'LTDA' in nat_jur.upper():
        breakdown.momento += 20
        justificativas.append("⚪ Ltda → +20 pts")
    elif 'COOPERATIVA' in nat_jur.upper():
        breakdown.momento += 15
        justificativas.append("⚪ Cooperativa → +15 pts")

    # Presença Digital & TI (sinais de maturidade tecnológica)
    if ts:
        # Domínio próprio / Site institucional
        if ts.get('dominio_proprio') or ts.get('site_institucional'):
            breakdown.momento += 25
            justificativas.append("🌐 Site/Domínio próprio → +25 pts")

        # Vagas TI abertas (SINAL FORTÍSSIMO de momento de compra)
        vagas = ts.get('vagas_ti_abertas', [])
        if len(vagas) >= 4:
            breakdown.momento += 40
            justificativas.append(f"🔥 Vagas TI ({len(vagas)}) → +40 pts [SINAL FORTE]")
        elif len(vagas) >= 1:
            breakdown.momento += 20
            justificativas.append(f"📋 Vagas TI ({len(vagas)}) → +20 pts")

        # ERP já implantado (indica maturidade, mas pode ser troca)
        erp = ts.get('erp_principal', {})
        if erp.get('sistema') and erp['sistema'] not in ['Não identificado', 'N/I']:
            breakdown.momento += 15
            justificativas.append(f"💻 ERP existente ({erp['sistema']}) → +15 pts")

    # Tecnologias no campo (conectividade, agricultura de precisão)
    if op.tecnologias_identificadas and len(op.tecnologias_identificadas) >= 2:
        breakdown.momento += 20
        justificativas.append(f"📡 Tecnologias identificadas ({len(op.tecnologias_identificadas)}) → +20 pts")

    # Conectividade (telemetria, sensores)
    if vert.telemetria_frota or vert.estacoes_meteorologicas or vert.drones_proprios:
        breakdown.momento += 15
        justificativas.append("📡 Conectividade no campo (telemetria/drones) → +15 pts")

    # Certificações (indica compliance e maturidade de processos)
    if cv.certificacoes and len(cv.certificacoes) >= 2:
        breakdown.momento += 20
        justificativas.append(f"✅ Certificações ({len(cv.certificacoes)}) → +20 pts")

    # Movimentos financeiros recentes (expansão, CRAs, Fiagros)
    if fi.movimentos_financeiros and len(fi.movimentos_financeiros) >= 1:
        breakdown.momento += 15
        justificativas.append(f"💰 Movimentos financeiros recentes ({len(fi.movimentos_financeiros)}) → +15 pts")

    # Cap máximo: 180 pts
    breakdown.momento = min(breakdown.momento, PESOS_PILARES_V2['momento'])

    # ========================================================================
    # BÔNUS S.A. GLOBAL (30 pts - reduzido de 50)
    # ========================================================================
    bonus = 0
    if 'S.A.' in nat_jur or 'S/A' in nat_jur:
        bonus = 30
        justificativas.append("💎 Bônus S.A. global → +30 pts")

    # ========================================================================
    # SCORE BRUTO
    # ========================================================================
    score_bruto = breakdown.total + bonus

    # ========================================================================
    # PENALIDADE DE CONFIANÇA (não-linear)
    # ========================================================================
    conf_media = (
        op.confianca + fi.confianca + cv.confianca
    ) / 3.0

    multiplicador_conf = 1.0

    if conf_media < 0.3:
        multiplicador_conf = 0.5
        justificativas.append(f"⚠️ Confiança BAIXA ({conf_media:.0%}) → score × 0.5")
    elif conf_media < 0.5:
        multiplicador_conf = 0.7
        justificativas.append(f"⚠️ Confiança média-baixa ({conf_media:.0%}) → score × 0.7")
    elif conf_media < 0.7:
        multiplicador_conf = 0.9
        justificativas.append(f"⚪ Confiança média ({conf_media:.0%}) → score × 0.9")
    else:
        justificativas.append(f"✅ Confiança ALTA ({conf_media:.0%}) → sem penalidade")

    score_bruto = int(score_bruto * multiplicador_conf)

    # ========================================================================
    # SCORE FINAL (cap 1000)
    # ========================================================================
    score_final = max(0, min(score_bruto, 1000))

    # ========================================================================
    # TIER (v0.2 - mais seletivo)
    # ========================================================================
    if score_final >= TIERS_V2['DIAMANTE']:
        tier = Tier.DIAMANTE
    elif score_final >= TIERS_V2['OURO']:
        tier = Tier.OURO
    elif score_final >= TIERS_V2['PRATA']:
        tier = Tier.PRATA
    else:
        tier = Tier.BRONZE

    # ========================================================================
    # OVERRIDE BIG FISH (condicional - só com dados robustos)
    # ========================================================================
    if capital >= 50_000_000 and hectares >= 10_000 and conf_media >= 0.6:
        if tier == Tier.PRATA:
            tier = Tier.OURO
            justificativas.append("🐋 Big Fish override: PRATA → OURO (Cap>50M + Ha>10k + Conf>60%)")
        elif tier == Tier.BRONZE:
            tier = Tier.PRATA
            justificativas.append("🐋 Big Fish override: BRONZE → PRATA (Cap>50M + Ha>10k + Conf>60%)")

    # ========================================================================
    # RESULTADO FINAL
    # ========================================================================
    justificativas.append(f"✅ Score Final: {score_final}/1000 — {tier.value}")
    justificativas.append(f"📊 Breakdown: Músculo {breakdown.musculo} | Complexidade {breakdown.complexidade} | Gente {breakdown.gente} | Momento {breakdown.momento}")

    return SASResult(
        score=score_final,
        tier=tier,
        breakdown=breakdown,
        dados_inferidos=(conf_media < 0.5),
        justificativas=justificativas
    )
