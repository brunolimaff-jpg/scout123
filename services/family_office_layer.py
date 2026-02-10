import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class FamilyOfficeLayer:
    """
    Mapeia holdings patrimoniais dos sócios.
    O dinheiro para TI muitas vezes sai do Family Office, não da operação agrícola.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    async def mapear_family_office(self, cpfs_socios: List[str], nomes_socios: List[str]) -> Dict:
        """
        Busca holdings patrimoniais e pessoas jurídicas dos sócios.
        Exemplo: Elizeu Scheffer Participações, Scheffer Holdings, etc.
        """
        logger.info(f"[FAMILY OFFICE] Mapeando holdings de {len(nomes_socios)} sócios")
        
        nomes_str = ", ".join(nomes_socios)
        cpfs_str = ", ".join(cpfs_socios)
        
        prompt = f"""Você é especialista em estruturas societárias e family offices brasileiros.

SÓCIOS ALVO:
{nomes_str}

CPFs:
{cpfs_str}

BUSQUE:
1. Holding patrimonial (ex: "Elizeu Scheffer Holding Ltda")
2. Pessoas jurídicas de investimento (ex: "Scheffer Participações S.A.")
3. Fundos de investimento (se houver)
4. Propriedades imobiliárias (pessoa física ou jurídica)
5. Participações em outras empresas (concorrentes, complementares)
6. Estruturas de planejamento patrimonial

IMPORTANTE:
- O dinheiro para grandes investimentos (ERP, plataformas, TI) pode sair do Family Office
- Não apenas da operação agrícola
- Isto afeta capacidade de investimento

RETORNE JSON:
{{
    "socios_estrutura": [
        {{
            "nome": "Elizeu Scheffer",
            "cpf": "XXX.XXX.XXX-XX",
            "holdings_patrimoniais": [
                {{
                    "razao_social": "Elizeu Scheffer Holding Ltda",
                    "cnpj": "XX.XXX.XXX/0001-XX",
                    "participacoes": [
                        {{"empresa": "Scheffer Agro S.A.", "percentual": "45%"}},
                        {{"empresa": "Scheffer Biofábricas", "percentual": "100%"}},
                        {{"empresa": "Scheffer Agtech", "percentual": "70%"}}
                    ]
                }}
            ],
            "imoveis": [
                {{"tipo": "Fazenda", "localizacao": "Bom Despacho, MG", "area": "5.000ha", "valor_estimado": "R$ 250M"}}
            ]
        }},
        {{
            "nome": "Joaquim Scheffer",
            "cpf": "YYY.YYY.YYY-YY",
            "holdings_patrimoniais": [
                {{
                    "razao_social": "J. Scheffer Participações",
                    "cnpj": "YY.YYY.YYY/0001-YY",
                    "participacoes": [
                        {{"empresa": "Scheffer Agro S.A.", "percentual": "35%"}},
                        {{"empresa": "Porto do Scheffer", "percentual": "100%"}}
                    ]
                }}
            ]
        }}
    ],
    "patrimonio_total_estimado": "R$ 1.2 bilhões",
    "capacidade_investimento_family_office": "R$ 150-300M/ano",
    "recomendacao": "Investimentos em TI podem ser viabilizados via Family Office sem comprometer EBITDA da operação agrícola."
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[FAMILY OFFICE] ✅ Patrimônio mapeado")
            return data
        except Exception as e:
            logger.error(f"[FAMILY OFFICE] ❌ Erro: {e}")
            return {"socios_estrutura": [], "status": "erro"}
    
    def _parse_json_response(self, response: str) -> Dict:
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            logger.warning("Falha ao parsear JSON family office")
            return {}
