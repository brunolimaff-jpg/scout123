"""
services/market_estimator_v2.py — Cálculo SAS Score com Validação Defensiva
Versão 2.0: NUNCA falha em conversões de tipo
"""
from typing import Dict, Any
from scout_types import SASResult, Tier, SASBreakdown
from services.data_validator import safe_float, safe_int, safe_list, safe_str


def calcular_sas(dados: Dict[str, Any]) -> SASResult:
    """
    Calcula Score SAS (Senior Agriculture Score) de 0 a 1000 pontos.
    Sistema defensivo que NUNCA falha.
    """
    breakdown = SASBreakdown()
    
    # ========================================================================
    # 1. TAMANHO & COMPLEXIDADE (300 pontos)
    # ========================================================================
    hectares = safe_float(dados.get('hectares_total', 0))
    funcionarios = safe_int(dados.get('funcionarios_estimados', 0))
    fazendas = safe_int(dados.get('numero_fazendas', 0))
    
    # Hectares (0-150 pontos)
    if hectares >= 20000:
        breakdown.tamanho_complexidade += 150
    elif hectares >= 10000:
        breakdown.tamanho_complexidade += 120
    elif hectares >= 5000:
        breakdown.tamanho_complexidade += 90
    elif hectares >= 2000:
        breakdown.tamanho_complexidade += 50
    elif hectares >= 500:
        breakdown.tamanho_complexidade += 20
    
    # Funcionários (0-80 pontos)
    if funcionarios >= 500:
        breakdown.tamanho_complexidade += 80
    elif funcionarios >= 200:
        breakdown.tamanho_complexidade += 60
    elif funcionarios >= 100:
        breakdown.tamanho_complexidade += 40
    elif funcionarios >= 50:
        breakdown.tamanho_complexidade += 20
    
    # Múltiplas fazendas (0-70 pontos)
    if fazendas >= 10:
        breakdown.tamanho_complexidade += 70
    elif fazendas >= 5:
        breakdown.tamanho_complexidade += 50
    elif fazendas >= 3:
        breakdown.tamanho_complexidade += 30
    elif fazendas >= 2:
        breakdown.tamanho_complexidade += 15
    
    # ========================================================================
    # 2. SOFISTICAÇÃO OPERACIONAL (250 pontos)
    # ========================================================================
    culturas = safe_list(dados.get('culturas', []))
    verticalizacao = dados.get('verticalizacao', {})
    regioes = safe_list(dados.get('regioes_atuacao', []))
    
    # Diversificação de culturas (0-80 pontos)
    num_culturas = len(culturas)
    if num_culturas >= 5:
        breakdown.sofisticacao_operacional += 80
    elif num_culturas >= 3:
        breakdown.sofisticacao_operacional += 50
    elif num_culturas >= 2:
        breakdown.sofisticacao_operacional += 25
    
    # Verticalização (0-100 pontos)
    if isinstance(verticalizacao, dict):
        vert_flags = [
            verticalizacao.get('industria', False),
            verticalizacao.get('logistica', False),
            verticalizacao.get('comercializacao', False),
            verticalizacao.get('pecuaria', False),
            verticalizacao.get('florestal', False)
        ]
        vert_score = sum(20 for flag in vert_flags if flag)
        breakdown.sofisticacao_operacional += vert_score
    
    # Expansão geográfica (0-70 pontos)
    num_regioes = len(regioes)
    if num_regioes >= 5:
        breakdown.sofisticacao_operacional += 70
    elif num_regioes >= 3:
        breakdown.sofisticacao_operacional += 45
    elif num_regioes >= 2:
        breakdown.sofisticacao_operacional += 20
    
    # ========================================================================
    # 3. SAÚDE FINANCEIRA (200 pontos)
    # ========================================================================
    capital_social = safe_float(dados.get('capital_social_estimado', 0))
    faturamento = safe_float(dados.get('faturamento_estimado', 0))
    movimentos = safe_list(dados.get('movimentos_financeiros', []))
    fiagros = safe_list(dados.get('fiagros_relacionados', []))
    cras = safe_list(dados.get('cras_emitidos', []))
    
    # Capital social (0-80 pontos)
    if capital_social >= 100_000_000:  # 100M+
        breakdown.saude_financeira += 80
    elif capital_social >= 50_000_000:  # 50M+
        breakdown.saude_financeira += 60
    elif capital_social >= 10_000_000:  # 10M+
        breakdown.saude_financeira += 40
    elif capital_social >= 1_000_000:  # 1M+
        breakdown.saude_financeira += 20
    
    # Faturamento estimado (0-60 pontos)
    if faturamento >= 500_000_000:  # 500M+
        breakdown.saude_financeira += 60
    elif faturamento >= 100_000_000:  # 100M+
        breakdown.saude_financeira += 40
    elif faturamento >= 50_000_000:  # 50M+
        breakdown.saude_financeira += 20
    
    # Sofisticação financeira (0-60 pontos)
    if len(fiagros) >= 2:
        breakdown.saude_financeira += 30
    elif len(fiagros) >= 1:
        breakdown.saude_financeira += 15
    
    if len(cras) >= 3:
        breakdown.saude_financeira += 30
    elif len(cras) >= 1:
        breakdown.saude_financeira += 15
    
    # ========================================================================
    # 4. POSICIONAMENTO DE MERCADO (150 pontos)
    # ========================================================================
    exporta = dados.get('exporta', False) or dados.get('cadeia_valor', {}).get('exporta', False)
    certificacoes = safe_list(dados.get('certificacoes', []))
    total_empresas = safe_int(dados.get('grupo_economico', {}).get('total_empresas', 0))
    
    # Exportação (0-50 pontos)
    if exporta:
        breakdown.posicionamento_mercado += 50
    
    # Certificações (0-60 pontos)
    num_cert = len(certificacoes)
    if num_cert >= 5:
        breakdown.posicionamento_mercado += 60
    elif num_cert >= 3:
        breakdown.posicionamento_mercado += 40
    elif num_cert >= 1:
        breakdown.posicionamento_mercado += 20
    
    # Grupo econômico (0-40 pontos)
    if total_empresas >= 10:
        breakdown.posicionamento_mercado += 40
    elif total_empresas >= 5:
        breakdown.posicionamento_mercado += 25
    elif total_empresas >= 2:
        breakdown.posicionamento_mercado += 10
    
    # ========================================================================
    # 5. MATURIDADE ORGANIZACIONAL (100 pontos)
    # ========================================================================
    decisores = dados.get('decisores', {})
    tech_stack = dados.get('tech_stack', {})
    natureza_juridica = safe_str(dados.get('natureza_juridica', ''))
    qsa_count = safe_int(dados.get('qsa_count', 0))
    
    # Estrutura de decisão (0-40 pontos)
    if isinstance(decisores, dict):
        lista_decisores = safe_list(decisores.get('decisores', []))
        estrutura = safe_str(decisores.get('estrutura_decisao', ''))
        
        if len(lista_decisores) >= 5:
            breakdown.maturidade_organizacional += 25
        elif len(lista_decisores) >= 3:
            breakdown.maturidade_organizacional += 15
        
        if 'profissional' in estrutura.lower():
            breakdown.maturidade_organizacional += 15
    
    # Maturidade tecnológica (0-30 pontos)
    if isinstance(tech_stack, dict):
        nivel_ti = safe_str(tech_stack.get('nivel_maturidade_ti', ''))
        if 'avançado' in nivel_ti.lower() or 'alto' in nivel_ti.lower():
            breakdown.maturidade_organizacional += 30
        elif 'médio' in nivel_ti.lower() or 'intermediário' in nivel_ti.lower():
            breakdown.maturidade_organizacional += 15
    
    # Estrutura jurídica (0-30 pontos)
    if 'sociedade anônima' in natureza_juridica.lower() or 's.a.' in natureza_juridica.lower():
        breakdown.maturidade_organizacional += 30
    elif 'ltda' in natureza_juridica.lower():
        breakdown.maturidade_organizacional += 15
    
    # QSA complexo indica estrutura mais robusta
    if qsa_count >= 10:
        breakdown.maturidade_organizacional += 0  # Já contabilizado em estrutura
    
    # ========================================================================
    # CÁLCULO FINAL
    # ========================================================================
    score_total = (
        breakdown.tamanho_complexidade +
        breakdown.sofisticacao_operacional +
        breakdown.saude_financeira +
        breakdown.posicionamento_mercado +
        breakdown.maturidade_organizacional
    )
    
    # Classificação por tier
    if score_total >= 750:
        tier = Tier.HUNTER_KILLER  # Top tier - alvo prioritário
    elif score_total >= 500:
        tier = Tier.HIGH_VALUE  # Alto valor
    elif score_total >= 300:
        tier = Tier.MEDIUM  # Médio porte
    else:
        tier = Tier.LOW_PRIORITY  # Baixa prioridade
    
    return SASResult(
        score=score_total,
        tier=tier,
        breakdown=breakdown,
        justificativa=_gerar_justificativa(breakdown, tier, dados)
    )


def _gerar_justificativa(breakdown: SASBreakdown, tier: Tier, dados: Dict) -> str:
    """
    Gera justificativa detalhada do score.
    """
    linhas = []
    linhas.append(f"**Tier {tier.value}**")
    linhas.append("")
    
    # Destaques positivos
    if breakdown.tamanho_complexidade >= 150:
        ha = safe_float(dados.get('hectares_total', 0))
        linhas.append(f"\u2705 Operação de grande escala: {ha:,.0f} ha")
    
    if breakdown.sofisticacao_operacional >= 150:
        linhas.append("\u2705 Alta sofisticação operacional com diversificação")
    
    if breakdown.saude_financeira >= 120:
        linhas.append("\u2705 Sólida estrutura financeira")
    
    if breakdown.posicionamento_mercado >= 80:
        linhas.append("\u2705 Forte posicionamento de mercado")
    
    # Pontos de atenção
    if breakdown.maturidade_organizacional < 30:
        linhas.append("\u26a0\ufe0f Oportunidade: Baixa maturidade organizacional")
    
    if breakdown.saude_financeira < 50:
        linhas.append("\u26a0\ufe0f Risco: Estrutura financeira limitada")
    
    return "\n".join(linhas)
