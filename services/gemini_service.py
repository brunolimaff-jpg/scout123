"""
services/gemini_service.py — RADAR Intelligence Engine ULTRA-PROFUNDO
Motor IA com 9 Agentes TURBINADOS + Classe GeminiService
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import json, re, time, logging, asyncio
from typing import Optional, Any, Dict
from enum import Enum
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

MODEL = "gemini-2.0-flash"
SEARCH = types.Tool(google_search=types.GoogleSearch())

# ========== CACHE SIMPLES ==========
class SimpleCache:
    def __init__(self):
        self._cache = {}
    
    def get(self, namespace: str, key: dict) -> Optional[Any]:
        cache_key = f"{namespace}:{json.dumps(key, sort_keys=True)}"
        return self._cache.get(cache_key)
    
    def set(self, namespace: str, key: dict, value: Any, ttl: int = 3600):
        cache_key = f"{namespace}:{json.dumps(key, sort_keys=True)}"
        self._cache[cache_key] = value

cache = SimpleCache()

# ========== PRIORITY ==========
class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

# ========== IDENTIDADES ==========
RADAR_IDENTITY = """VOCE E O SISTEMA RADAR (PROTOCOLO FOX-3) — Inteligencia de Mercado Tatica ULTRA-PROFUNDA.
SUA MISSAO: VARREDURA COMPLETA E EXAUSTIVA. ZERO LIMITES. PRECISAO > CUSTO.

DIRETRIZES DE COMBATE (MODO AGRESSIVO):
1. BUSQUE EM MÚLTIPLAS FONTES: Sites oficiais, notícias, LinkedIn, vagas de emprego, relatórios públicos, CVM, B3.
2. NÃO LIMITE A BUSCA: Se encontrou 5 notícias, busque mais 10. Se achou 3 decisores, procure mais 7.
3. CRUZE INFORMAÇÕES: Valide dados em múltiplas fontes. Se houver discordância, reporte ambas.
4. SEJA ESPECÍFICO: Não diga "grande produtor". Diga "230.000 hectares em MT e MA".
5. INCLUA FONTES: Sempre que possível, mencione de onde veio a informação.
6. VÁ FUNDO: Procure balanços, DRE, relatórios de sustentabilidade, apresentações institucionais em PDF.

TOM DE VOZ: Militar, Objetivo, Preciso, Sem enrolacao.
"""

PORTFOLIO_SENIOR = """
=== ARSENAL SENIOR SISTEMAS + GATEC ===
A Senior Sistemas oferece a suite completa "Farm-to-Fork" via parceria GAtec:

1. GATEC (OPERACIONAL / CAMPO):
- SimpleFarm: O "ERP do Campo". Planejamento de safra, custos por talhão, gestão de insumos.
- SimpleViewer: Cockpit de BI Agrícola.
- Operis: Gestão de Pátios e Armazens (Silos).
- Mapfy: Agricultura de precisão e mapas.

2. SENIOR ERP (BACKOFFICE / CORPORATIVO):
- ERP Gestão Empresarial: O Core. Financeiro, Contábil, Fiscal (Compliance nativo Brasil).
- Diferencial: Compliance fiscal nativo (SPED, Funrural, LCDPR) vs SAP/Oracle (que precisam de localização).

3. SENIOR HCM (PESSOAS):
- Folha, Ponto (com regras rurais NR-31), SST.
- Diferencial: eSocial nativo e gestão de safra/turnos.

4. SENIOR LOGÍSTICA & CRM:
- WMS (Armazém), TMS (Transporte).
- CRM Senior X: Pipeline de vendas e relacionamento.

ARGUMENTOS DE ATAQUE (FOX-3):
- "A única plataforma que conecta o Talhão (GAtec) ao Balanço (Senior) sem gambiarras."
- "SAP é caro e rígido. Senior é flexível e compliance Brasil nativo."
- "Totvs é colcha de retalhos (sistemas comprados que não se falam). Senior + GAtec é integração nativa."
"""


# ==============================================================================
# CLASSE GEMINI SERVICE (PRINCIPAL)
# ==============================================================================
class GeminiService:
    """
    Serviço central para chamadas ao Gemini com retry e cache.
    """
    
    def __init__(self, api_key: str):
        """Inicializa o cliente Gemini."""
        self.client = genai.Client(api_key=api_key)
        logger.info("[GeminiService] Inicializado com sucesso")
    
    async def call_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3,
        use_search: bool = False,
        temperature: float = 0.1
    ) -> str:
        """
        Chama o Gemini com retry automático.
        
        Args:
            prompt: Prompt para o modelo
            max_retries: Número máximo de tentativas
            use_search: Se deve usar Google Search
            temperature: Temperatura do modelo
        
        Returns:
            Resposta do modelo como string
        """
        tools = [SEARCH] if use_search else None
        config = types.GenerateContentConfig(tools=tools, temperature=temperature)
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=config
                )
                return response.text
            
            except Exception as e:
                logger.warning(f"[GeminiService] Tentativa {attempt + 1}/{max_retries} falhou: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    logger.error(f"[GeminiService] Todas as tentativas falharam: {e}")
                    raise
        
        return ""
    
    def call_sync(self, prompt: str, use_search: bool = False, temperature: float = 0.1) -> str:
        """
        Versão síncrona da chamada (para compatibilidade).
        """
        tools = [SEARCH] if use_search else None
        config = types.GenerateContentConfig(tools=tools, temperature=temperature)
        
        try:
            response = self.client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"[GeminiService] Erro na chamada síncrona: {e}")
            return ""


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def _clean_json(text):
    """Limpa o output do Gemini para garantir JSON válido."""
    if not text: return None
    try:
        m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if m: return json.loads(m.group(1))
    except: pass
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m: return json.loads(m.group(0))
    except: pass
    try: return json.loads(text.replace('```json','').replace('```','').strip())
    except: return None

def _call(client, prompt, config, prio=Priority.NORMAL):
    """Executa a chamada ao Gemini (direto)."""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
        return response.text
    except Exception as e:
        logger.error(f"❌ ERRO GEMINI: {e}")
        return None


# ==============================================================================
# AGENTES (Versões simplificadas para compatibilidade)
# ==============================================================================
def agent_recon_operacional(client, empresa):
    ck = {"a":"recon_v5","e":empresa}
    c = cache.get("recon", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO OPERACIONAL ULTRA-PROFUNDO.
ALVO: "{empresa}"
RETORNE JSON com: nome_grupo, hectares_total, culturas, verticalizacao, regioes_atuacao, fazendas_detalhadas, tecnologias_identificadas, etc.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg)) or {"nome_grupo":empresa,"confianca":0.0}
    cache.set("recon", ck, r)
    return r


def agent_sniper_financeiro(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"fin_v5","e":alvo}
    c = cache.get("fin", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RASTREAMENTO FINANCEIRO E GOVERNANCA.
ALVO: "{alvo}"
RETORNE JSON com: capital_social_estimado, faturamento_estimado, funcionarios_estimados, cras_emitidos, parceiros_financeiros, etc.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg)) or {"confianca":0.0}
    cache.set("fin", ck, r)
    return r


def agent_grupo_economico(client, empresa, cnpj_matriz=""):
    ck = {"a":"grupo_v5","e":empresa}
    c = cache.get("grupo", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: MAPEAR TEIA CORPORATIVA COMPLETA.
ALVO: "{empresa}"
RETORNE JSON com: cnpj_matriz, holding_controladora, cnpjs_filiais, cnpjs_coligadas, controladores, etc.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg)) or {"confianca":0.0}
    cache.set("grupo", ck, r)
    return r


def agent_cadeia_valor(client, empresa, dados_ops):
    ck = {"a":"cadeia_v5","e":empresa}
    c = cache.get("cadeia", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: POSICIONAMENTO COMPLETO NA CADEIA DE VALOR.
ALVO: "{empresa}"
RETORNE JSON com: posicao_cadeia, clientes_principais, fornecedores_principais, parcerias_estrategicas, certificacoes, etc.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg)) or {"confianca":0.0}
    cache.set("cadeia", ck, r)
    return r


def agent_intel_mercado(client, empresa, setor_info=""):
    ck = {"a":"intel_v5","e":empresa}
    c = cache.get("intel", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: SIGINT - ÚLTIMOS 24 MESES.
ALVO: "{empresa}"
RETORNE JSON com: noticias_recentes, sinais_compra, riscos, oportunidades, dores_identificadas, concorrentes, etc.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.2)
    r = _clean_json(_call(client, prompt, cfg)) or {"confianca":0.0}
    cache.set("intel", ck, r)
    return r


def agent_profiler_decisores(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"decisores_v5","e":alvo}
    c = cache.get("decisores", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: HUMINT - MAPEAMENTO COMPLETO DE DECISORES.
ALVO: "{alvo}"
RETORNE JSON com: decisores (array), estrutura_decisao, influenciadores.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg)) or {"decisores":[],"confianca":0.0}
    cache.set("decisores", ck, r)
    return r


def agent_tech_stack(client, empresa, nome_grupo=""):
    alvo = nome_grupo or empresa
    ck = {"a":"tech_v5","e":alvo}
    c = cache.get("tech", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: RECONHECIMENTO COMPLETO DE SISTEMAS.
ALVO: "{alvo}"
RETORNE JSON com: erp_principal, outros_sistemas, vagas_ti_abertas, nivel_maturidade_ti, gaps_identificados.
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.1)
    r = _clean_json(_call(client, prompt, cfg)) or {"confianca":0.0}
    cache.set("tech", ck, r)
    return r


def agent_analise_estrategica(client, dados, sas, contexto=""):
    prompt = f"""{RADAR_IDENTITY}
VOCÊ É O OFICIAL DE INTELIGÊNCIA DO PROJETO RADAR.

DADOS DO ALVO:
{json.dumps(dados, indent=2, ensure_ascii=False, default=str)[:15000]}

SCORE SAS: {sas.get('score',0)} — Tier: {sas.get('tier','N/D')}

{PORTFOLIO_SENIOR}

GERE RELATÓRIO DE MISSÃO (Markdown).
"""
    cfg = types.GenerateContentConfig(temperature=0.4)
    return _call(client, prompt, cfg) or "FALHA NA GERAÇÃO."


def agent_auditor_qualidade(client, texto, dados):
    prompt = f"""{RADAR_IDENTITY}
MISSAO: DEBRIEFING E CONTROLE DE QUALIDADE.
Avalie (0-10): PRECISÃO, TÁTICA, FIT SENIOR.
Retorne JSON: {{"scores":{{...}},"nota_final":0,"nivel":"..."}}
"""
    cfg = types.GenerateContentConfig(temperature=0.2)
    return _clean_json(_call(client, prompt, cfg)) or {"nota_final":0,"nivel":"INSUFICIENTE"}


def buscar_cnpj_por_nome(client, nome):
    ck = {"b":nome}
    c = cache.get("bcnpj", ck)
    if c: return c
    
    prompt = f"""{RADAR_IDENTITY}
MISSAO: LOCALIZAR CNPJ MATRIZ. ALVO: "{nome}".
Retorne APENAS CNPJ ou "NAO_ENCONTRADO".
"""
    cfg = types.GenerateContentConfig(tools=[SEARCH], temperature=0.0)
    text = _call(client, prompt, cfg)
    if text:
        m = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', text)
        if m:
            cnpj = m.group(0)
            cache.set("bcnpj", ck, cnpj)
            return cnpj
    return None
