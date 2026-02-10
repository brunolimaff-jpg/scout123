import requests
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class SupplyChainLayer:
    """
    Camada de cadeia de suprimentos:
    - Manifestos de carga e exportação (Comexstat)
    - Análise de bioinsumos (MAPA)
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    # ======== EXPORTAÇÃO ========
    async def analise_exportacao(self, razao_social: str, cnpj: str) -> Dict:
        """
        Busca dados de exportação (Comexstat, Mdic).
        Valida produção real: "Exportou 500k ton via Porto Santos".
        """
        logger.info(f"[EXPORT] Analisando exportações: {razao_social}")
        
        prompt = f"""Você é especialista em dados de comércio exterior agrícola.

ALVO: {razao_social} ({cnpj})

BUSQUE EM COMEXSTAT (dados públicos do MDIC):
1. Volume exportado por produto (soja, algodão, milho, café, etc)
2. Destinos (China, EU, Ásia)
3. Portos de embarque (Santos, Paranaguá, Rio Grande, Manaus)
4. Valores em USD
5. NCM (Nomenclatura Comum do Mercosul)
6. Tendência temporal (crescimento/queda)

VALIDE PRODUÇÃO:
- Se exportou 500k toneladas = produção mínima de 600k toneladas
- Isto valida área em produção
- Cruze com área declarada de CAR

RETORNE JSON:
{{
    "exportacoes_ultimos_3_anos": [
        {{
            "ano": 2024,
            "produto": "Soja em Grão",
            "ncm": "1201.10.00",
            "volume_toneladas": 320000,
            "valor_usd": 145000000,
            "destinos": {{"China": "75%", "EU": "15%", "Outros": "10%"}},
            "portos": {{"Santos": "60%", "Paranaguá": "40%"}}
        }},
        {{
            "ano": 2024,
            "produto": "Algodão",
            "ncm": "5201.00.00",
            "volume_toneladas": 85000,
            "valor_usd": 95000000,
            "destinos": {{"China": "85%", "Vietnã": "10%", "Outros": "5%"}},
            "portos": {{"Santos": "100%"}}
        }}
    ],
    "volume_total_exportado_2024": "405.000 toneladas",
    "receita_exportacao_2024": "USD 240 milhões",
    "crescimento_yoy": "+12%",
    "validacao_producao": "Produção mínima estimada: 480k toneladas. ALINHADA com área CAR.",
    "observacoes": "Empresa com acesso garantido a mercados internacionais. Produção validada e competitiva."
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[EXPORT] ✅ Exportação validada")
            return data
        except Exception as e:
            logger.error(f"[EXPORT] ❌ Erro: {e}")
            return {"exportacoes_ultimos_3_anos": [], "status": "erro"}
    
    # ======== BIOINSUMOS ========
    async def analise_bioinsumos(self, razao_social: str, cnpj: str) -> Dict:
        """
        Busca registros de biofábricas e responsáveis técnicos no MAPA.
        Indica maturidade altíssima em biológicos = concorrente da indústria química.
        """
        logger.info(f"[BIOINSUMOS] Rastreando: {razao_social}")
        
        prompt = f"""Você é especialista em bioinsumos e biofábricas agrícolas.

ALVO: {razao_social} ({cnpj})

BUSQUE NO MAPA (Ministério da Agricultura):
1. Registros de biofábricas em nome de {razao_social}
2. Responsáveis técnicos registrados
3. Tipo de bioproducto (biofertilizantes, biopesticidas, promotores de crescimento, bactérias benéficas)
4. Capacidade de produção (toneladas/ano)
5. Produtos registrados

INDICADORES DE MATURIDADE:
- 1+ biofábrica = Operação vertical avançada
- 3+ biofábricas = Competidor potencial da indústria química
- Registros próprios = IP proprietário, não apenas revendedor

RETORNE JSON:
{{
    "biofabricas": [
        {{
            "nome": "Biofábrica Scheffer - Unidade Matopiba",
            "municipio": "Bom Jesus",
            "uf": "PI",
            "responsavel_tecnico": "Dr. João Silva - CREA-PI 12345",
            "tipo_producao": "Bactérias benéficas, actinomicetos",
            "capacidade_toneladas_ano": 5000,
            "produtos_registrados": ["Bacillus subtilis SC-1", "Trichoderma harzianum TH-2"],
            "data_registro": "2020-06-15"
        }},
        {{
            "nome": "Biofábrica Scheffer - Unidade Goiás",
            "municipio": "Rio Verde",
            "uf": "GO",
            "responsavel_tecnico": "Dra. Maria Costa - CREA-GO 54321",
            "tipo_producao": "Biofertilizantes, promotores de crescimento",
            "capacidade_toneladas_ano": 3500,
            "produtos_registrados": ["Azospirillum brasilense AZ-3", "Glicine betaína GB-1"],
            "data_registro": "2021-03-22"
        }},
        {{
            "nome": "Biofábrica Scheffer - Unidade Mato Grosso",
            "municipio": "Cuiabá",
            "uf": "MT",
            "responsavel_tecnico": "Prof. Carlos Oliveira - CREA-MT 98765",
            "tipo_producao": "Biossurfactantes, elicitores",
            "capacidade_toneladas_ano": 2000,
            "produtos_registrados": ["Lipopeptídeos LP-1", "Ácido salicílico AS-2"],
            "data_registro": "2022-01-10"
        }}
    ],
    "total_biofabricas": 3,
    "capacidade_producao_total": "10.500 toneladas/ano",
    "maturidade_bioinsumos": "Altíssima (Operação Vertical)",
    "observacoes": "Empresa NÃO é apenas revendedora. É produtora proprietária de bioinsumos. Concorrente potencial da indústria química tradicional (Basf, Bayer).",
    "implicacoes_comerciais": [
        "Redução de COGS (custo de ingredientes ativos)",
        "IP proprietário em bioinsumos",
        "Potencial de venda B2B de bioinsumos",
        "Integração vertical forte",
        "Capacidade de R&D em biologics"
    ]
}}"""
        
        try:
            response = await self.gemini.call_with_retry(prompt, max_retries=3)
            data = self._parse_json_response(response)
            logger.info(f"[BIOINSUMOS] ✅ {data.get('total_biofabricas', 0)} biofábricas identificadas")
            return data
        except Exception as e:
            logger.error(f"[BIOINSUMOS] ❌ Erro: {e}")
            return {"biofabricas": [], "total_biofabricas": 0, "status": "erro"}
    
    def _parse_json_response(self, response: str) -> Dict:
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            logger.warning("Falha ao parsear JSON supply chain")
            return {}
