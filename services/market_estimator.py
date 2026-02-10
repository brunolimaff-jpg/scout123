"""
services/market_estimator.py — Cálculo SAS Score com Validação Defensiva
Versão Corrigida: Usa os atributos corretos do SASBreakdown
"""
from typing import Dict, Any
from scout_types import SASResult, Tier, SASBreakdown

try:
    from services.data_validator import safe_float, safe_int, safe_list, safe_str
except ImportError:
    # Fallback se data_validator não existir
    def safe_float(val, default=0.0):
        try:
            if isinstance(val, (int, float)): return float(val)
            if isinstance(val, str):
                import re
                val_clean = re.sub(r'[^0-9.]', '', val)
                return float(val_clean) if val_clean else default
            return default
        except:
            return default
    
    def safe_int(val, default=0):
        return int(safe_float(val, default))
    
    def safe_list(val):
        return val if isinstance(val, list) else []
    
    def safe_str(val, default=''):
        return str(val) if val else default


def calcular_sas(dados: Dict[str, Any]) -> SASResult:
    """
    Calcula Score SAS (Senior Agriculture Score) de 0 a 1000 pontos.
    Sistema defensivo que NUNCA falha.
    
    Breakdown:
    - musculo (300 pts): Tamanho/Hectares/Funcionários
    - complexidade (250 pts): Verticalização/Culturas/Regiões
    - gente (250 pts): Saúde Financeira + Estrutura
    - momento (200 pts): Posicionamento/Exporta/Tech
    """
    breakdown = SASBreakdown()
    
    # ========================================================================
    # 1. MÚSCULO - PORTE (300 pontos)
    # ========================================================================
    hectares = safe_float(dados.get('hectares_total', 0))
    funcionarios = safe_int(dados.get('funcionarios_estimados', 0))
    fazendas = safe_int(dados.get('numero_fazendas', 0))
    
    # Hectares (0-150 pontos)
    if hectares >= 20000:
        breakdown.musculo += 150
    elif hectares >= 10000:
        breakdown.musculo += 120
    elif hectares >= 5000:
        breakdown.musculo += 90
    elif hectares >= 2000:
        breakdown.musculo += 50
    elif hectares >= 500:
        breakdown.musculo += 20
    
    # Funcionários (0-80 pontos)
    if funcionarios >= 500:
        breakdown.musculo += 80
    elif funcionarios >= 200:
        breakdown.musculo += 60
    elif funcionarios >= 100:
        breakdown.musculo += 40
    elif funcionarios >= 50:
        breakdown.musculo += 20
    
    # Múltiplas fazendas (0-70 pontos)
    if fazendas >= 10:
        breakdown.musculo += 70
    elif fazendas >= 5:
        breakdown.musculo += 50
    elif fazendas >= 3:
        breakdown.musculo += 30
    elif fazendas >= 2:
        breakdown.musculo += 15
    
    # ========================================================================
    # 2. COMPLEXIDADE - SOFISTICAÇÃO OPERACIONAL (250 pontos)
    # ========================================================================
    culturas = safe_list(dados.get('culturas', []))
    verticalizacao = dados.get('verticalizacao', {})
    regioes = safe_list(dados.get('regioes_atuacao', []))
    
    # Diversificação de culturas (0-80 pontos)
    num_culturas = len(culturas)
    if num_culturas >= 5:
        breakdown.complexidade += 80
    elif num_culturas >= 3:
        breakdown.complexidade += 50
    elif num_culturas >= 2:
        breakdown.complexidade += 25
    
    # Verticalização (0-100 pontos)
    if hasattr(verticalizacao, 'count'):
        # Se é um objeto Verticalizacao
        vert_count = verticalizacao.count()
        if vert_count >= 10:
            breakdown.complexidade += 100
        elif vert_count >= 5:
            breakdown.complexidade += 70
        elif vert_count >= 3:
            breakdown.complexidade += 40
        elif vert_count >= 1:
            breakdown.complexidade += 20
    elif isinstance(verticalizacao, dict):
        # Se é um dicionário
        vert_flags = sum(1 for v in verticalizacao.values() if v)
        if vert_flags >= 10:
            breakdown.complexidade += 100
        elif vert_flags >= 5:
            breakdown.complexidade += 70
        elif vert_flags >= 3:
            breakdown.complexidade += 40
        elif vert_flags >= 1:
            breakdown.complexidade += 20
    
    # Expansão geográfica (0-70 pontos)
    num_regioes = len(regioes)
    if num_regioes >= 5:
        breakdown.complexidade += 70
    elif num_regioes >= 3:
        breakdown.complexidade += 45
    elif num_regioes >= 2:
        breakdown.complexidade += 20
    
    # ========================================================================
    # 3. GENTE - SAÚDE FINANCEIRA + ESTRUTURA (250 pontos)
    # ========================================================================
    capital_social = safe_float(dados.get('capital_social_estimado', 0))
    faturamento = safe_float(dados.get('faturamento_estimado', 0))
    fiagros = safe_list(dados.get('fiagros_relacionados', []))
    cras = safe_list(dados.get('cras_emitidos', []))
    qsa_count = safe_int(dados.get('qsa_count', 0))
    natureza_juridica = safe_str(dados.get('natureza_juridica', ''))
    
    # Capital social (0-80 pontos)
    if capital_social >= 100_000_000:  # 100M+
        breakdown.gente += 80
    elif capital_social >= 50_000_000:  # 50M+
        breakdown.gente += 60
    elif capital_social >= 10_000_000:  # 10M+
        breakdown.gente += 40
    elif capital_social >= 1_000_000:  # 1M+
        breakdown.gente += 20
    
    # Faturamento estimado (0-60 pontos)
    if faturamento >= 500_000_000:  # 500M+
        breakdown.gente += 60
    elif faturamento >= 100_000_000:  # 100M+
        breakdown.gente += 40
    elif faturamento >= 50_000_000:  # 50M+
        breakdown.gente += 20
    
    # Sofisticação financeira (0-60 pontos)
    if len(fiagros) >= 2:
        breakdown.gente += 30
    elif len(fiagros) >= 1:
        breakdown.gente += 15
    
    if len(cras) >= 3:
        breakdown.gente += 30
    elif len(cras) >= 1:
        breakdown.gente += 15
    
    # Estrutura jurídica (0-30 pontos)
    if 'sociedade anônima' in natureza_juridica.lower() or 's.a.' in natureza_juridica.lower():
        breakdown.gente += 30
    elif 'ltda' in natureza_juridica.lower():
        breakdown.gente += 15
    
    # Estrutura de gestão (0-20 pontos)
    if qsa_count >= 10:
        breakdown.gente += 20
    elif qsa_count >= 5:
        breakdown.gente += 10
    
    # ========================================================================
    # 4. MOMENTO - POSICIONAMENTO & TECNOLOGIA (200 pontos)
    # ========================================================================
    cadeia_valor = dados.get('cadeia_valor', {})
    if isinstance(cadeia_valor, dict):
        exporta = cadeia_valor.get('exporta', False)
        certificacoes = safe_list(cadeia_valor.get('certificacoes', []))
    else:
        exporta = dados.get('exporta', False)
        certificacoes = safe_list(dados.get('certificacoes', []))
    
    grupo_economico = dados.get('grupo_economico', {})
    total_empresas = safe_int(grupo_economico.get('total_empresas', 0)) if isinstance(grupo_economico, dict) else 0
    
    decisores = dados.get('decisores', {})
    tech_stack = dados.get('tech_stack', {})
    tecnologias = safe_list(dados.get('tecnologias_identificadas', []))
    
    # Exportação (0-60 pontos)
    if exporta:
        breakdown.momento += 60
    
    # Certificações (0-50 pontos)
    num_cert = len(certificacoes)
    if num_cert >= 5:
        breakdown.momento += 50
    elif num_cert >= 3:
        breakdown.momento += 35
    elif num_cert >= 1:
        breakdown.momento += 15
    
    # Grupo econômico (0-40 pontos)
    if total_empresas >= 10:
        breakdown.momento += 40
    elif total_empresas >= 5:
        breakdown.momento += 25
    elif total_empresas >= 2:
        breakdown.momento += 10
    
    # Maturidade tecnológica (0-50 pontos)
    if isinstance(tech_stack, dict):
        nivel_ti = safe_str(tech_stack.get('nivel_maturidade_ti', ''))
        if 'avançado' in nivel_ti.lower() or 'alto' in nivel_ti.lower():
            breakdown.momento += 50
        elif 'médio' in nivel_ti.lower() or 'intermediário' in nivel_ti.lower():
            breakdown.momento += 25
    elif len(tecnologias) >= 5:
        breakdown.momento += 40
    elif len(tecnologias) >= 3:
        breakdown.momento += 20
    
    # ========================================================================
    # CÁLCULO FINAL
    # ========================================================================
    score_total = breakdown.total  # Usa a propriedade do dataclass
    
    # Classificação por tier
    if score_total >= 700:
        tier = Tier.DIAMANTE  # Top tier - alvo prioritário
    elif score_total >= 500:
        tier = Tier.OURO  # Alto valor
    elif score_total >= 300:
        tier = Tier.PRATA  # Médio porte
    else:
        tier = Tier.BRONZE  # Baixa prioridade
    
    # Gera justificativas
    justificativas = _gerar_justificativas(breakdown, tier, dados)
    
    return SASResult(
        score=score_total,
        tier=tier,
        breakdown=breakdown,
        justificativas=justificativas,
        confidence_score=_calcular_confianca(dados)
    )


def _gerar_justificativas(breakdown: SASBreakdown, tier: Tier, dados: Dict) -> list:
    """
    Gera lista de justificativas do score.
    """
    justificativas = []
    
    # Breakdown detalhado
    justificativas.append(f"💪 Músculo (Porte): {breakdown.musculo}/300 pts")
    justificativas.append(f"⚙️ Complexidade: {breakdown.complexidade}/250 pts")
    justificativas.append(f"👥 Gente (Gestão/Finanças): {breakdown.gente}/250 pts")
    justificativas.append(f"⏱️ Momento (Tech/Mercado): {breakdown.momento}/200 pts")
    justificativas.append("")
    
    # Destaques positivos
    ha = safe_float(dados.get('hectares_total', 0))
    if breakdown.musculo >= 180:
        justificativas.append(f"✅ Operação de grande escala: {ha:,.0f} ha")
    
    if breakdown.complexidade >= 150:
        justificativas.append("✅ Alta sofisticação operacional com diversificação")
    
    if breakdown.gente >= 150:
        justificativas.append("✅ Sólida estrutura financeira e de gestão")
    
    if breakdown.momento >= 120:
        justificativas.append("✅ Forte posicionamento de mercado e tecnologia")
    
    # Pontos de atenção
    if breakdown.momento < 50:
        justificativas.append("⚠️ Oportunidade: Baixa adoção tecnológica")
    
    if breakdown.gente < 50:
        justificativas.append("⚠️ Risco: Estrutura financeira limitada")
    
    if breakdown.musculo < 50:
        justificativas.append("⚠️ Operação de pequeno porte")
    
    return justificativas


def _calcular_confianca(dados: Dict) -> float:
    """
    Calcula nível de confiança baseado na disponibilidade de dados.
    """
    campos_importantes = [
        'hectares_total',
        'culturas',
        'capital_social_estimado',
        'funcionarios_estimados',
        'numero_fazendas'
    ]
    
    campos_preenchidos = sum(1 for campo in campos_importantes if dados.get(campo))
    return campos_preenchidos / len(campos_importantes)
