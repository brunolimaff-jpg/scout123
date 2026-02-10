"""
services/cnpj_service.py — BrasilAPI + ReceitaWS com retry
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import re, requests, time, json
from typing import Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from scout_types import DadosCNPJ

# ========== CACHE SIMPLES INLINE ==========
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


def limpar_cnpj(c: str) -> str:
    return re.sub(r'\D', '', c.strip())

def formatar_cnpj(c: str) -> str:
    c = limpar_cnpj(c)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}" if len(c) == 14 else c

def validar_cnpj(c: str) -> bool:
    c = limpar_cnpj(c)
    return len(c) == 14 and c != c[0] * 14


class CNPJError(Exception):
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10),
       retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)))
def _brasilapi(cnpj: str) -> dict:
    r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=15)
    if r.status_code == 200:
        return r.json()
    if r.status_code == 429:
        time.sleep(5)
        raise requests.ConnectionError("rate limited")
    raise CNPJError(f"HTTP {r.status_code}")


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=8),
       retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)))
def _receitaws(cnpj: str) -> dict:
    r = requests.get(f"https://receitaws.com.br/v1/cnpj/{cnpj}", timeout=15, headers={"Accept": "application/json"})
    if r.status_code == 200:
        d = r.json()
        if d.get("status") == "ERROR":
            raise CNPJError(d.get("message", ""))
        return d
    raise CNPJError(f"HTTP {r.status_code}")


def _parse_brasil(d: dict) -> DadosCNPJ:
    qsa = [{"nome": s.get("nome_socio", ""), "qualificacao": s.get("qualificacao_socio", ""),
             "data_entrada": s.get("data_entrada_sociedade", "")} for s in d.get("qsa", [])]
    cnaes = [f"{c['codigo']} - {c.get('descricao', '')}" for c in d.get("cnaes_secundarios", []) if c.get("codigo")]
    return DadosCNPJ(
        cnpj=d.get("cnpj", ""), razao_social=d.get("razao_social", ""),
        nome_fantasia=d.get("nome_fantasia", ""), situacao_cadastral=d.get("descricao_situacao_cadastral", ""),
        data_abertura=d.get("data_inicio_atividade", ""), natureza_juridica=d.get("descricao_natureza_juridica", ""),
        capital_social=float(d.get("capital_social", 0)), porte=d.get("descricao_porte", ""),
        cnae_principal=str(d.get("cnae_fiscal", "")), cnae_descricao=d.get("cnae_fiscal_descricao", ""),
        cnaes_secundarios=cnaes, municipio=d.get("municipio", ""), uf=d.get("uf", ""),
        cep=d.get("cep", ""), logradouro=d.get("logradouro", ""), numero=d.get("numero", ""),
        complemento=d.get("complemento", ""), bairro=d.get("bairro", ""),
        telefone=d.get("ddd_telefone_1", ""), email=d.get("email", ""),
        qsa=qsa, fonte="brasilapi", timestamp=str(time.time()),
    )


def consultar_cnpj(cnpj: str) -> Optional[DadosCNPJ]:
    c = limpar_cnpj(cnpj)
    if not validar_cnpj(c):
        return None
    cached = cache.get("cnpj", {"c": c})
    if cached:
        return cached
    try:
        r = _parse_brasil(_brasilapi(c))
        cache.set("cnpj", {"c": c}, r, ttl=86400)
        return r
    except Exception:
        pass
    try:
        raw = _receitaws(c)
        r = DadosCNPJ(cnpj=c, razao_social=raw.get("nome", ""), nome_fantasia=raw.get("fantasia", ""),
                       situacao_cadastral=raw.get("situacao", ""),
                       capital_social=float(str(raw.get("capital_social", "0")).replace(".", "").replace(",", ".")),
                       cnae_principal=raw.get("atividade_principal", [{}])[0].get("code", ""),
                       cnae_descricao=raw.get("atividade_principal", [{}])[0].get("text", ""),
                       municipio=raw.get("municipio", ""), uf=raw.get("uf", ""),
                       fonte="receitaws", timestamp=str(time.time()))
        cache.set("cnpj", {"c": c}, r, ttl=86400)
        return r
    except Exception:
        return None
