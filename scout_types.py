"""
scout_types.py — Contrato de Dados v3.1 (Full Agro Verticals)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Tier(str, Enum):
    DIAMANTE = "DIAMANTE 💎"
    OURO = "OURO 🥇"
    PRATA = "PRATA 🥈"
    BRONZE = "BRONZE 🥉"

class QualityLevel(str, Enum):
    EXCELENTE = "EXCELENTE"
    BOM = "BOM"
    ACEITAVEL = "ACEITÁVEL"
    INSUFICIENTE = "INSUFICIENTE"


# =============================================================================
# VERTICALIZAÇÃO — TODAS AS CADEIAS DO AGRO (40+ campos)
# =============================================================================

@dataclass
class Verticalizacao:
    # Armazenagem & Logística
    silos: bool = False
    armazens_gerais: bool = False
    terminal_portuario: bool = False
    ferrovia_propria: bool = False
    frota_propria: bool = False
    # Beneficiamento Grãos/Fibras
    algodoeira: bool = False
    sementeira: bool = False
    ubs: bool = False                    # Unidade Beneficiamento Sementes
    secador: bool = False
    # Agroindústria Vegetal
    agroindustria: bool = False
    usina_acucar_etanol: bool = False
    destilaria: bool = False
    esmagadora_soja: bool = False
    refinaria_oleo: bool = False
    fabrica_biodiesel: bool = False
    torrefacao_cafe: bool = False
    beneficiamento_arroz: bool = False
    fabrica_sucos: bool = False
    vinicultura: bool = False
    # Proteína Animal
    frigorifico_bovino: bool = False
    frigorifico_aves: bool = False
    frigorifico_suinos: bool = False
    frigorifico_peixes: bool = False
    laticinio: bool = False
    fabrica_racao: bool = False
    incubatorio: bool = False
    # Insumos & Genética
    fabrica_fertilizantes: bool = False
    fabrica_defensivos: bool = False
    laboratorio_genetica: bool = False
    central_inseminacao: bool = False
    viveiro_mudas: bool = False
    # Energia & Sustentabilidade
    cogeracao_energia: bool = False
    usina_solar: bool = False
    biodigestor: bool = False
    planta_biogas: bool = False
    creditos_carbono: bool = False
    # Florestal & Celulose
    florestal_eucalipto: bool = False
    florestal_pinus: bool = False
    fabrica_celulose: bool = False
    serraria: bool = False
    # Irrigação
    pivos_centrais: bool = False
    irrigacao_gotejamento: bool = False
    barragem_propria: bool = False
    # Tecnologia
    agricultura_precisao: bool = False
    drones_proprios: bool = False
    estacoes_meteorologicas: bool = False
    telemetria_frota: bool = False
    erp_implantado: bool = False

    _LABELS: dict = field(default_factory=lambda: {}, repr=False, init=False)

    def __post_init__(self):
        self._LABELS = {
            'silos': '🏗️ Silos', 'armazens_gerais': '🏗️ Armazéns',
            'terminal_portuario': '🚢 Terminal Portuário', 'ferrovia_propria': '🚂 Ferrovia',
            'frota_propria': '🚛 Frota', 'algodoeira': '☁️ Algodoeira',
            'sementeira': '🌱 Sementeira', 'ubs': '🌱 UBS',
            'secador': '🔥 Secador', 'agroindustria': '🏭 Agroindústria',
            'usina_acucar_etanol': '⚡ Usina Açúcar/Etanol', 'destilaria': '🧪 Destilaria',
            'esmagadora_soja': '🫘 Esmagadora Soja', 'refinaria_oleo': '🛢️ Refinaria Óleo',
            'fabrica_biodiesel': '⛽ Biodiesel', 'torrefacao_cafe': '☕ Torrefação Café',
            'beneficiamento_arroz': '🍚 Benef. Arroz', 'fabrica_sucos': '🍊 Fábrica Sucos',
            'vinicultura': '🍷 Vinicultura', 'frigorifico_bovino': '🥩 Frigorífico Bovino',
            'frigorifico_aves': '🍗 Frigorífico Aves', 'frigorifico_suinos': '🐷 Frigorífico Suínos',
            'frigorifico_peixes': '🐟 Frigorífico Peixes', 'laticinio': '🥛 Laticínio',
            'fabrica_racao': '🌾 Fáb. Ração', 'incubatorio': '🥚 Incubatório',
            'fabrica_fertilizantes': '🧫 Fáb. Fertilizantes', 'fabrica_defensivos': '🧴 Fáb. Defensivos',
            'laboratorio_genetica': '🧬 Lab. Genética', 'central_inseminacao': '🧬 Central Inseminação',
            'viveiro_mudas': '🌿 Viveiro Mudas', 'cogeracao_energia': '⚡ Cogeração',
            'usina_solar': '☀️ Solar', 'biodigestor': '♻️ Biodigestor',
            'planta_biogas': '💨 Biogás', 'creditos_carbono': '🌍 Créditos Carbono',
            'florestal_eucalipto': '🌲 Eucalipto', 'florestal_pinus': '🌲 Pinus',
            'fabrica_celulose': '📄 Celulose', 'serraria': '🪵 Serraria',
            'pivos_centrais': '💧 Pivôs Centrais', 'irrigacao_gotejamento': '💧 Gotejamento',
            'barragem_propria': '🌊 Barragem', 'agricultura_precisao': '📡 Agric. Precisão',
            'drones_proprios': '🛸 Drones', 'estacoes_meteorologicas': '🌤️ Estações Meteo',
            'telemetria_frota': '📍 Telemetria', 'erp_implantado': '💻 ERP',
        }

    def listar_ativos(self) -> list[str]:
        ativos = []
        for campo, label in self._LABELS.items():
            if getattr(self, campo, False):
                ativos.append(label)
        return ativos

    def count(self) -> int:
        return len(self.listar_ativos())

    def all_fields(self) -> list[str]:
        return [k for k in self._LABELS.keys()]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DadosCNPJ:
    cnpj: str = ""
    razao_social: str = ""
    nome_fantasia: str = ""
    situacao_cadastral: str = ""
    data_abertura: str = ""
    natureza_juridica: str = ""
    capital_social: float = 0.0
    porte: str = ""
    cnae_principal: str = ""
    cnae_descricao: str = ""
    cnaes_secundarios: list[str] = field(default_factory=list)
    municipio: str = ""
    uf: str = ""
    cep: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    telefone: str = ""
    email: str = ""
    qsa: list[dict] = field(default_factory=list)
    fonte: str = "brasilapi"
    timestamp: str = ""


@dataclass
class DadosOperacionais:
    nome_grupo: str = ""
    hectares_total: int = 0
    culturas: list[str] = field(default_factory=list)
    verticalizacao: Verticalizacao = field(default_factory=Verticalizacao)
    regioes_atuacao: list[str] = field(default_factory=list)
    numero_fazendas: int = 0
    tecnologias_identificadas: list[str] = field(default_factory=list)
    cabecas_gado: int = 0
    cabecas_aves: int = 0
    cabecas_suinos: int = 0
    area_florestal_ha: int = 0
    area_irrigada_ha: int = 0
    confianca: float = 0.0


@dataclass
class DadosFinanceiros:
    capital_social_estimado: float = 0.0
    funcionarios_estimados: int = 0
    faturamento_estimado: float = 0.0
    movimentos_financeiros: list[str] = field(default_factory=list)
    fiagros_relacionados: list[str] = field(default_factory=list)
    cras_emitidos: list[str] = field(default_factory=list)
    parceiros_financeiros: list[str] = field(default_factory=list)
    auditorias: list[str] = field(default_factory=list)
    governanca_corporativa: bool = False
    resumo_financeiro: str = ""
    confianca: float = 0.0


@dataclass
class CadeiaValor:
    posicao_cadeia: str = ""         # "produtor", "integrador", "processador", "trader"
    clientes_principais: list[str] = field(default_factory=list)
    fornecedores_principais: list[str] = field(default_factory=list)
    parcerias_estrategicas: list[str] = field(default_factory=list)
    canais_venda: list[str] = field(default_factory=list)
    integracao_vertical_nivel: str = "" # "baixa", "media", "alta", "total"
    exporta: bool = False
    mercados_exportacao: list[str] = field(default_factory=list)
    certificacoes: list[str] = field(default_factory=list)
    confianca: float = 0.0


@dataclass
class GrupoEconomico:
    cnpj_matriz: str = ""
    cnpjs_filiais: list[str] = field(default_factory=list)
    cnpjs_coligadas: list[str] = field(default_factory=list)
    total_empresas: int = 0
    controladores: list[str] = field(default_factory=list)
    holding_controladora: str = ""
    confianca: float = 0.0


@dataclass
class IntelMercado:
    noticias_recentes: list[dict] = field(default_factory=list)
    concorrentes: list[str] = field(default_factory=list)
    tendencias_setor: list[str] = field(default_factory=list)
    dores_identificadas: list[str] = field(default_factory=list)
    oportunidades: list[str] = field(default_factory=list)
    sinais_compra: list[str] = field(default_factory=list)
    riscos: list[str] = field(default_factory=list)
    confianca: float = 0.0


# =============================================================================
# SCORE
# =============================================================================

@dataclass
class SASBreakdown:
    musculo: int = 0
    complexidade: int = 0
    gente: int = 0
    momento: int = 0

    @property
    def total(self) -> int:
        return self.musculo + self.complexidade + self.gente + self.momento

    def to_dict(self) -> dict:
        return {
            "Músculo (Porte)": self.musculo,
            "Complexidade": self.complexidade,
            "Gente (Gestão)": self.gente,
            "Momento (Tec/Gov)": self.momento,
        }


@dataclass
class SASResult:
    score: int = 0
    tier: Tier = Tier.BRONZE
    breakdown: SASBreakdown = field(default_factory=SASBreakdown)
    dados_inferidos: bool = False
    justificativas: list[str] = field(default_factory=list)


@dataclass
class QualityCheck:
    criterio: str = ""
    passou: bool = False
    nota: str = ""
    peso: float = 1.0


@dataclass
class QualityReport:
    nivel: QualityLevel = QualityLevel.INSUFICIENTE
    score_qualidade: float = 0.0
    checks: list[QualityCheck] = field(default_factory=list)
    recomendacoes: list[str] = field(default_factory=list)
    audit_ia: Optional[dict] = None
    timestamp: str = ""


@dataclass
class SecaoAnalise:
    titulo: str = ""
    conteudo: str = ""
    icone: str = "📄"


@dataclass
class PipelineStepResult:
    """Resultado visual de cada etapa do pipeline para exibir ao usuário."""
    step_number: int = 0
    step_name: str = ""
    icon: str = ""
    status: str = "pending"    # pending, running, success, warning, error
    resumo: str = ""
    detalhes: list[str] = field(default_factory=list)
    dados_encontrados: dict = field(default_factory=dict)
    confianca: float = 0.0
    tempo_segundos: float = 0.0


@dataclass
class DossieCompleto:
    empresa_alvo: str = ""
    cnpj: str = ""
    dados_cnpj: Optional[DadosCNPJ] = None
    dados_operacionais: DadosOperacionais = field(default_factory=DadosOperacionais)
    dados_financeiros: DadosFinanceiros = field(default_factory=DadosFinanceiros)
    cadeia_valor: CadeiaValor = field(default_factory=CadeiaValor)
    grupo_economico: GrupoEconomico = field(default_factory=GrupoEconomico)
    intel_mercado: IntelMercado = field(default_factory=IntelMercado)
    decisores: dict = field(default_factory=dict)
    tech_stack: dict = field(default_factory=dict)
    sas_result: SASResult = field(default_factory=SASResult)
    secoes_analise: list[SecaoAnalise] = field(default_factory=list)
    analise_bruta: str = ""
    quality_report: Optional[QualityReport] = None
    pipeline_steps: list[PipelineStepResult] = field(default_factory=list)
    modelo_usado: str = ""
    timestamp_geracao: str = ""
    tempo_total_segundos: float = 0.0
    pipeline_log: list[str] = field(default_factory=list)

    def merge_dados(self) -> dict:
        m = {}
        if self.dados_cnpj:
            m['capital_social'] = self.dados_cnpj.capital_social
            m['cnae_principal'] = self.dados_cnpj.cnae_principal
            m['cnae_descricao'] = self.dados_cnpj.cnae_descricao
            m['uf'] = self.dados_cnpj.uf
            m['municipio'] = self.dados_cnpj.municipio
            m['natureza_juridica'] = self.dados_cnpj.natureza_juridica
            m['qsa_count'] = len(self.dados_cnpj.qsa)
        m['nome_grupo'] = self.dados_operacionais.nome_grupo or self.empresa_alvo
        m['hectares_total'] = self.dados_operacionais.hectares_total
        m['culturas'] = self.dados_operacionais.culturas
        m['verticalizacao'] = self.dados_operacionais.verticalizacao
        m['regioes_atuacao'] = self.dados_operacionais.regioes_atuacao
        m['numero_fazendas'] = self.dados_operacionais.numero_fazendas
        m['tecnologias'] = self.dados_operacionais.tecnologias_identificadas
        m['cabecas_gado'] = self.dados_operacionais.cabecas_gado
        m['cabecas_aves'] = self.dados_operacionais.cabecas_aves
        m['cabecas_suinos'] = self.dados_operacionais.cabecas_suinos
        m['area_florestal_ha'] = self.dados_operacionais.area_florestal_ha
        m['area_irrigada_ha'] = self.dados_operacionais.area_irrigada_ha
        m['capital_social_estimado'] = self.dados_financeiros.capital_social_estimado
        m['funcionarios_estimados'] = self.dados_financeiros.funcionarios_estimados
        m['faturamento_estimado'] = self.dados_financeiros.faturamento_estimado
        m['movimentos_financeiros'] = self.dados_financeiros.movimentos_financeiros
        m['fiagros'] = self.dados_financeiros.fiagros_relacionados
        m['cras'] = self.dados_financeiros.cras_emitidos
        m['governanca'] = self.dados_financeiros.governanca_corporativa
        m['parceiros_financeiros'] = self.dados_financeiros.parceiros_financeiros
        m['cadeia_valor'] = {
            'posicao': self.cadeia_valor.posicao_cadeia,
            'integracao': self.cadeia_valor.integracao_vertical_nivel,
            'exporta': self.cadeia_valor.exporta,
            'certificacoes': self.cadeia_valor.certificacoes,
        }
        m['grupo_economico'] = {
            'total_empresas': self.grupo_economico.total_empresas,
            'controladores': self.grupo_economico.controladores,
        }
        return m
