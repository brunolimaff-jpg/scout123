"""
services/market_estimator.py — Classe MarketEstimator para Cálculo SAS Score
CORRIGIDO: Importação correta + tratamento defensivo de erros
"""
import logging
from typing import Dict, Any
from scout_types import SASResult, Tier, SASBreakdown

logger = logging.getLogger(__name__)

# Funções de validação defensiva (fallback se data_validator não existir)
try:
    from services.data_validator import safe_float, safe_int, safe_list, safe_str
except ImportError:
    logger.warning("[MarketEstimator] data_validator não encontrado, usando fallbacks")
    
    def safe_float(val, default=0.0):
        try:
            if isinstance(val, (int, float)): 
                return float(val)
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


class MarketEstimator:
    """
    Classe para cálculo do Score SAS (Senior Agriculture Score).
    Motor defensivo que NUNCA falha.
    """
    
    def __init__(self):
        logger.info("[MarketEstimator] Inicializado")
    
    def calcular_sas(self, dados: Dict[str, Any]) -> SASResult:
        """
        Calcula Score SAS (0-1000 pontos) baseado em 4 pilares.
        
        Args:
            dados: Dicionário com dados consolidados do dossiê
            
        Returns:
            SASResult com score, tier, breakdown e justificativas
        """
        logger.info("[MarketEstimator] Iniciando cálculo SAS Score")
        
        breakdown = SASBreakdown()
        justificativas = []
        
        try:
            # ========================================================================
            # 1. MÚSCULO - PORTE (300 pontos)
            # ========================================================================
            hectares = safe_float(dados.get('hectares_total', 0))
            funcionarios = safe_int(dados.get('funcionarios_estimados', 0))
            fazendas = safe_int(dados.get('numero_fazendas', 0))
            
            # Hectares (0-150 pontos)
            if hectares >= 20000:
                breakdown.musculo += 150
                justificativas.append(f"✅ Mega-operação: {hectares:,.0f} ha → 150 pts")
            elif hectares >= 10000:
                breakdown.musculo += 120
                justificativas.append(f"✅ Grande operação: {hectares:,.0f} ha → 120 pts")
            elif hectares >= 5000:
                breakdown.musculo += 90
                justificativas.append(f"✅ Operação média: {hectares:,.0f} ha → 90 pts")
            elif hectares >= 2000:
                breakdown.musculo += 50
                justificativas.append(f"⚠️ Operação pequena: {hectares:,.0f} ha → 50 pts")
            elif hectares >= 500:
                breakdown.musculo += 20
                justificativas.append(f"⚠️ Operação micro: {hectares:,.0f} ha → 20 pts")
            else:
                justificativas.append(f"❌ Área insuficiente: {hectares:,.0f} ha → 0 pts")
            
            # Funcionários (0-80 pontos)
            if funcionarios >= 500:
                breakdown.musculo += 80
                justificativas.append(f"✅ Grande força de trabalho: {funcionarios:,} → 80 pts")
            elif funcionarios >= 200:
                breakdown.musculo += 60
                justificativas.append(f"✅ Força de trabalho média: {funcionarios:,} → 60 pts")
            elif funcionarios >= 100:
                breakdown.musculo += 40
                justificativas.append(f"⚠️ Força de trabalho pequena: {funcionarios:,} → 40 pts")
            elif funcionarios >= 50:
                breakdown.musculo += 20
            
            # Múltiplas fazendas (0-70 pontos)
            if fazendas >= 10:
                breakdown.musculo += 70
                justificativas.append(f"✅ Grupo multi-site: {fazendas} fazendas → 70 pts")
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
                justificativas.append(f"✅ Alta diversificação: {num_culturas} culturas → 80 pts")
            elif num_culturas >= 3:
                breakdown.complexidade += 50
            elif num_culturas >= 2:
                breakdown.complexidade += 25
            
            # Verticalização (0-100 pontos)
            vert_count = 0
            if hasattr(verticalizacao, 'count'):
                # Se é um objeto Verticalizacao
                vert_count = verticalizacao.count()
            elif isinstance(verticalizacao, dict):
                # Se é um dicionário
                vert_count = sum(1 for v in verticalizacao.values() if v)
            
            if vert_count >= 10:
                breakdown.complexidade += 100
                justificativas.append(f"✅ Alta verticalização: {vert_count} operações → 100 pts")
            elif vert_count >= 5:
                breakdown.complexidade += 70
                justificativas.append(f"✅ Verticalização média: {vert_count} operações → 70 pts")
            elif vert_count >= 3:
                breakdown.complexidade += 40
            elif vert_count >= 1:
                breakdown.complexidade += 20
            
            # Expansão geográfica (0-70 pontos)
            num_regioes = len(regioes)
            if num_regioes >= 5:
                breakdown.complexidade += 70
                justificativas.append(f"✅ Presença nacional: {num_regioes} regiões → 70 pts")
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
            if capital_social >= 100_000_000:
                breakdown.gente += 80
                justificativas.append(f"✅ Capital gigante: R$ {capital_social/1e6:.0f}M → 80 pts")
            elif capital_social >= 50_000_000:
                breakdown.gente += 60
            elif capital_social >= 10_000_000:
                breakdown.gente += 40
            elif capital_social >= 1_000_000:
                breakdown.gente += 20
            
            # Faturamento estimado (0-60 pontos)
            if faturamento >= 500_000_000:
                breakdown.gente += 60
                justificativas.append(f"✅ Faturamento alto: R$ {faturamento/1e6:.0f}M → 60 pts")
            elif faturamento >= 100_000_000:
                breakdown.gente += 40
            elif faturamento >= 50_000_000:
                breakdown.gente += 20
            
            # Sofisticação financeira (0-60 pontos)
            if len(fiagros) >= 2:
                breakdown.gente += 30
                justificativas.append(f"✅ Fiagros ativos: {len(fiagros)} → 30 pts")
            elif len(fiagros) >= 1:
                breakdown.gente += 15
            
            if len(cras) >= 3:
                breakdown.gente += 30
                justificativas.append(f"✅ CRAs emitidos: {len(cras)} → 30 pts")
            elif len(cras) >= 1:
                breakdown.gente += 15
            
            # Estrutura jurídica (0-30 pontos)
            if 'sociedade anônima' in natureza_juridica.lower() or 's.a.' in natureza_juridica.lower():
                breakdown.gente += 30
                justificativas.append("✅ S.A. → 30 pts (governança corporativa)")
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
            
            tech_stack = dados.get('tech_stack', {})
            tecnologias = safe_list(dados.get('tecnologias_identificadas', []))
            
            # Exportação (0-60 pontos)
            if exporta:
                breakdown.momento += 60
                justificativas.append("✅ Exportador ativo → 60 pts")
            
            # Certificações (0-50 pontos)
            num_cert = len(certificacoes)
            if num_cert >= 5:
                breakdown.momento += 50
                justificativas.append(f"✅ Altamente certificado: {num_cert} → 50 pts")
            elif num_cert >= 3:
                breakdown.momento += 35
            elif num_cert >= 1:
                breakdown.momento += 15
            
            # Grupo econômico (0-40 pontos)
            if total_empresas >= 10:
                breakdown.momento += 40
                justificativas.append(f"✅ Grande grupo: {total_empresas} empresas → 40 pts")
            elif total_empresas >= 5:
                breakdown.momento += 25
            elif total_empresas >= 2:
                breakdown.momento += 10
            
            # Maturidade tecnológica (0-50 pontos)
            if isinstance(tech_stack, dict):
                nivel_ti = safe_str(tech_stack.get('nivel_maturidade_ti', ''))
                if 'avançado' in nivel_ti.lower() or 'alto' in nivel_ti.lower():
                    breakdown.momento += 50
                    justificativas.append("✅ TI avançada → 50 pts")
                elif 'médio' in nivel_ti.lower() or 'intermediário' in nivel_ti.lower():
                    breakdown.momento += 25
            elif len(tecnologias) >= 5:
                breakdown.momento += 40
            elif len(tecnologias) >= 3:
                breakdown.momento += 20
            
            # ========================================================================
            # CÁLCULO FINAL
            # ========================================================================
            score_total = breakdown.total  # Usa a propriedade calculada
            
            # Classificação por tier
            if score_total >= 700:
                tier = Tier.DIAMANTE
                recomendacao = "🎯 ALVO PRIORITÁRIO - Potencial 500k+ | Ciclo 60-90 dias"
            elif score_total >= 500:
                tier = Tier.OURO
                recomendacao = "✅ ALVO QUALIFICADO - Potencial 200-500k | Ciclo 90-120 dias"
            elif score_total >= 300:
                tier = Tier.PRATA
                recomendacao = "⚠️ ALVO SECUNDÁRIO - Potencial <200k | Ciclo 120+ dias"
            else:
                tier = Tier.BRONZE
                recomendacao = "❌ ALVO DESCARTADO - Baixo potencial"
            
            # Gera justificativas finais
            justificativas.append("")
            justificativas.append(f"📊 BREAKDOWN FINAL:")
            justificativas.append(f"  💪 Músculo: {breakdown.musculo}/300 pts")
            justificativas.append(f"  ⚙️ Complexidade: {breakdown.complexidade}/250 pts")
            justificativas.append(f"  👥 Gente: {breakdown.gente}/250 pts")
            justificativas.append(f"  ⏱️ Momento: {breakdown.momento}/200 pts")
            justificativas.append(f"  ═══════════════════════")
            justificativas.append(f"  🏆 TOTAL: {score_total}/1000 pts")
            justificativas.append(f"  🎖️ TIER: {tier.value}")
            justificativas.append("")
            justificativas.append(f"💡 {recomendacao}")
            
            # Calcula confiança
            confidence_score = self._calcular_confianca(dados)
            
            logger.info(f"[MarketEstimator] Score calculado: {score_total}/1000 ({tier.value})")
            
            return SASResult(
                score=score_total,
                tier=tier,
                breakdown=breakdown,
                justificativas=justificativas,
                confidence_score=confidence_score,
                recomendacao_comercial=recomendacao
            )
            
        except Exception as e:
            logger.error(f"[MarketEstimator] Erro no cálculo: {e}", exc_info=True)
            # Retorna resultado seguro em caso de erro
            return SASResult(
                score=0,
                tier=Tier.BRONZE,
                breakdown=SASBreakdown(),
                justificativas=[f"❌ Erro no cálculo: {str(e)}"],
                confidence_score=0.0,
                recomendacao_comercial="Erro no processamento"
            )
    
    def _calcular_confianca(self, dados: Dict) -> float:
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
        confianca = campos_preenchidos / len(campos_importantes)
        
        logger.debug(f"[MarketEstimator] Confiança calculada: {confianca:.0%}")
        return confianca
