"""
services/dossie_generator.py

Gerador de dossiês completos em formato Markdown.
Bandeirante Digital - Sistema de Inteligência de Mercado.
"""

import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class DossieGenerator:
    """Gerador de dossiês Bandeirante Digital."""
    
    def gerar_dossie_completo(self, results: Dict) -> str:
        """
        Gera dossiê markdown completo a partir dos resultados da investigação.
        
        Args:
            results: Dicionário com resultados completos da investigação
            
        Returns:
            String com dossiê formatado em Markdown
        """
        sections = []
        
        # Gera cada seção do dossiê
        sections.append(self._gerar_header(results))
        sections.append(self._gerar_executive_summary(results))
        sections.append(self._gerar_matriz_priorizacao(results))
        sections.append(self._gerar_recomendacoes(results))
        sections.append(self._gerar_todas_fases(results))
        sections.append(self._gerar_footer(results))
        
        # Junta todas as seções com dupla quebra de linha
        return "\n\n".join(sections)
    
    def _gerar_header(self, results: Dict) -> str:
        """Gera cabeçalho do dossiê."""
        metadata = results.get("metadata", {})
        empresa = metadata.get("empresa", "N/D")
        cnpj = metadata.get("cnpj", "N/D")
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        return (
            "# 🎯 DOSSIÊ DE INTELIGÊNCIA COMERCIAL\n"
            "## BANDEIRANTE DIGITAL - MODO DEUS\n\n"
            f"**📋 EMPRESA:** {empresa}  \n"
            f"**🔢 CNPJ:** {cnpj}  \n"
            f"**📅 DATA:** {data_atual}  \n"
            "**⚡ VERSÃO:** 3.0\n\n"
            "---"
        )
    
    def _gerar_executive_summary(self, results: Dict) -> str:
        """Gera resumo executivo."""
        matriz = results.get("matriz_priorizacao", {})
        score = matriz.get("score_final", 0)
        status = matriz.get("status", "N/D")
        classificacao = matriz.get("classificacao", "N/D")
        
        rec = results.get("recomendacoes", {})
        acao = rec.get("acao_recomendada", "N/D")
        
        return (
            "## 📊 EXECUTIVE SUMMARY\n\n"
            f"**🎯 SCORE FINAL:** {score}/100  \n"
            f"**📌 STATUS:** {status}  \n"
            f"**🏆 CLASSIFICAÇÃO:** {classificacao}  \n"
            f"**⚡ AÇÃO RECOMENDADA:** {acao}\n\n"
            "---"
        )
    
    def _gerar_matriz_priorizacao(self, results: Dict) -> str:
        """Gera seção da matriz de priorização."""
        matriz = results.get("matriz_priorizacao", {})
        
        area = matriz.get("area_total_ha", 0)
        score = matriz.get("score_final", 0)
        status = matriz.get("status", "N/D")
        
        return (
            "## 🎯 MATRIZ DE PRIORIZAÇÃO\n\n"
            "### Indicadores Chave\n\n"
            f"- **Área Total:** {area:,.0f} hectares\n"
            f"- **Score Final:** {score}/100\n"
            f"- **Status:** {status}\n\n"
            "---"
        )
    
    def _gerar_recomendacoes(self, results: Dict) -> str:
        """Gera seção de recomendações."""
        rec = results.get("recomendacoes", {})
        
        acao = rec.get("acao_recomendada", "N/D")
        score = rec.get("score", 0)
        status = rec.get("status", "N/D")
        
        content = (
            "## 🚀 RECOMENDAÇÕES DE AÇÃO\n\n"
            f"**STATUS:** {status}  \n"
            f"**AÇÃO:** {acao}  \n"
            f"**SCORE:** {score}/100\n\n"
            "### Próximos Passos\n\n"
        )
        
        # Adiciona cada passo
        for passo in rec.get("proximos_passos", []):
            content += f"{passo}\n"
        
        # Adiciona estratégia de abordagem
        decisor = rec.get('decisor_principal', 'CEO')
        gatilho = rec.get('gatilho_usar', 'N/D')
        canal = rec.get('canal_preferido', 'LinkedIn')
        momento = rec.get('melhor_momento_contato', 'N/D')
        
        content += (
            "\n### Estratégia de Abordagem\n\n"
            f"- **Decisor Principal:** {decisor}\n"
            f"- **Gatilho a Usar:** {gatilho}\n"
            f"- **Canal Preferido:** {canal}\n"
            f"- **Melhor Momento:** {momento}\n\n"
            "---"
        )
        
        return content
    
    def _gerar_todas_fases(self, results: Dict) -> str:
        """Gera resumo de todas as fases da investigação."""
        content = "## 📋 DETALHAMENTO DAS FASES\n\n"
        
        fases = results.get("fases", {})
        
        # FASE -1: REPUTATION
        reputation = fases.get("fase_-1_reputation", {})
        flag_risco = reputation.get("flag_risco", "N/D")
        
        content += (
            "### 🔍 FASE -1: SHADOW REPUTATION\n\n"
            f"**Flag de Risco:** {flag_risco}\n\n"
            "---\n\n"
        )
        
        # FASE 1: INCENTIVOS FISCAIS
        incentivos = fases.get("fase_1_incentivos", {})
        estaduais = incentivos.get("incentivos_estaduais", {})
        multas = incentivos.get("sancoes_multas", {})
        
        content += (
            "### 💰 FASE 1: INCENTIVOS FISCAIS\n\n"
            f"- **Total de Incentivos:** {estaduais.get('total_incentivos', 0)}\n"
            f"- **Benefício Anual Estimado:** {estaduais.get('valor_beneficio_anual_estimado', 'N/D')}\n"
            f"- **Multas Fiscais:** {multas.get('total_multas_quantidade', 0)}\n"
            f"- **Valor Total Multas:** {multas.get('total_multas_valor', 'R$ 0')}\n\n"
            "---\n\n"
        )
        
        # FASE 2: TERRITORIAL
        territorial = fases.get("fase_2_territorial", {})
        fundiario = territorial.get("dados_fundiarios", {})
        licencas = territorial.get("licencas_ambientais", {})
        
        estados_str = ', '.join(fundiario.get('estados_presenca', ['N/D']))
        car_regular = 'Sim' if fundiario.get('car_status', {}).get('cadastrado') else 'Não'
        
        content += (
            "### 🗺️ FASE 2: INTELIGÊNCIA TERRITORIAL\n\n"
            "**Dados Fundiários:**\n"
            f"- **Área Total:** {fundiario.get('area_total_ha', 0):,.0f} hectares\n"
            f"- **Total de Imóveis:** {fundiario.get('total_imoveis', 0)}\n"
            f"- **Estados:** {estados_str}\n"
            f"- **CAR Regular:** {car_regular}\n\n"
            "**Licenças Ambientais:**\n"
            f"- **Licenças Ativas:** {licencas.get('total_licencas', 0)}\n"
            f"- **Licenças Recentes (6m):** {licencas.get('licencas_recentes_6m', 0)}\n\n"
            "---\n\n"
        )
        
        # FASE 3: LOGÍSTICA
        logistica = fases.get("fase_3_logistica", {})
        armazenagem = logistica.get("armazenagem", {})
        frota = logistica.get("frota_logistica", {})
        
        rntrc_ativo = 'Ativo' if frota.get('rntrc', {}).get('ativo') else 'Inativo'
        
        content += (
            "### 🚛 FASE 3: LOGÍSTICA & SUPPLY CHAIN\n\n"
            "**Armazenagem:**\n"
            f"- **Capacidade Total:** {armazenagem.get('capacidade_total_toneladas', 0):,.0f} toneladas\n"
            f"- **Unidades:** {armazenagem.get('total_unidades', 0)}\n"
            f"- **Necessidade WMS:** {armazenagem.get('necessidade_wms', 'N/D')}\n\n"
            "**Frota:**\n"
            f"- **RNTRC:** {rntrc_ativo}\n"
            f"- **Veículos:** {frota.get('rntrc', {}).get('quantidade_veiculos', 0)}\n\n"
            "---\n\n"
        )
        
        # FASE 4: SOCIETÁRIO
        societario = fases.get("fase_4_societario", {})
        estrutura = societario.get("estrutura", {})
        grupo = estrutura.get("grupo_economico", {})
        
        content += (
            "### 🏢 FASE 4: ESTRUTURA SOCIETÁRIA\n\n"
            "**Grupo Econômico:**\n"
            f"- **Holding Controladora:** {grupo.get('holding_controladora', 'N/D')}\n"
            f"- **Total Empresas:** {grupo.get('total_empresas_grupo', 0)}\n"
            f"- **Capital Social Total:** {grupo.get('capital_social_total_grupo', 'R$ 0')}\n\n"
            f"**Risco Societário:** {societario.get('risco_societario', 'N/D')}\n\n"
            "---\n\n"
        )
        
        # FASE 5: EXECUTIVOS
        executivos = fases.get("fase_5_executivos", {})
        hierarquia = executivos.get("hierarquia", {})
        
        tem_ti = 'Sim' if hierarquia.get('tem_area_ti') else 'Não'
        
        content += (
            "### 👔 FASE 5: PROFILING DE EXECUTIVOS\n\n"
            "**Hierarquia:**\n"
            f"- **Tem Área TI:** {tem_ti}\n"
            f"- **Tipo de Decisão:** {hierarquia.get('tipo_decisao', 'N/D')}\n"
            f"- **Vagas TI Abertas:** {len(hierarquia.get('vagas_ti_abertas', []))}\n\n"
            "---\n\n"
        )
        
        # FASE 6: TRIGGERS
        triggers = fases.get("fase_6_triggers", {})
        contexto = triggers.get("contexto_sazonal", {})
        
        content += (
            "### ⏰ FASE 6: TRIGGER EVENTS\n\n"
            f"**Urgência Geral:** {triggers.get('urgencia_geral', 'N/D')}  \n"
            f"**Melhor Momento:** {triggers.get('melhor_momento_contato', 'N/D')}\n\n"
            "**Contexto Sazonal:**\n"
            f"- **Período:** {contexto.get('periodo', 'N/D')}\n"
            f"- **Abertura:** {contexto.get('abertura', 'N/D')}\n\n"
            f"**Triggers Identificados:** {triggers.get('total_triggers', 0)}\n\n"
        )
        
        # Lista cada trigger
        for i, trigger in enumerate(triggers.get("triggers", []), 1):
            content += (
                f"**Trigger {i}:** {trigger.get('tipo', 'N/D')}\n"
                f"- **Severidade:** {trigger.get('severidade', 'N/D')}\n"
                f"- **Descrição:** {trigger.get('descricao', 'N/D')}\n"
                f"- **Implicação:** {trigger.get('implicacao', 'N/D')}\n\n"
            )
        
        content += "---\n\n"
        
        # FASE 7: PSICOLOGIA
        psicologia = fases.get("fase_7_psicologia", {})
        storytelling = psicologia.get('storytelling_abertura', 'N/D')
        
        content += (
            "### 🧠 FASE 7: PSICOLOGIA & GATILHOS\n\n"
            f"**Gatilho Psicológico:** {psicologia.get('gatilho_psicologico', 'N/D')}  \n"
            f"**Canal Preferido:** {psicologia.get('canal_preferido', 'N/D')}  \n"
            f"**Tom Recomendado:** {psicologia.get('tom_recomendado', 'Consultivo')}\n\n"
            "**Storytelling de Abertura:**\n\n"
            "```\n"
            f"{storytelling}\n"
            "```\n\n"
            "---\n\n"
        )
        
        return content
    
    def _gerar_footer(self, results: Dict) -> str:
        """Gera rodapé do dossiê."""
        metadata = results.get("metadata", {})
        duracao = metadata.get("duracao_segundos", 0)
        timestamp_fim = metadata.get("timestamp_fim", "N/D")
        versao = metadata.get("versao", "3.0")
        modo = metadata.get('modo', 'completo')
        
        return (
            "## 📝 METADADOS DA INVESTIGAÇÃO\n\n"
            f"**Versão do Sistema:** {versao}  \n"
            f"**Duração da Investigação:** {duracao:.1f} segundos  \n"
            f"**Timestamp Final:** {timestamp_fim}  \n"
            f"**Modo de Execução:** {modo}\n\n"
            "---\n\n"
            "**🎯 Bandeirante Digital - MODO DEUS COMPLETO**  \n"
            "*Sistema de Inteligência de Mercado Ultra-Avançada para Agronegócio*\n\n"
            "**Desenvolvido por:** Bruno Lima  \n"
            "**Empresa:** Senior Sistemas  \n"
            "**Localidade:** Cuiabá, MT\n\n"
            "© 2026 - Todos os direitos reservados"
        )
