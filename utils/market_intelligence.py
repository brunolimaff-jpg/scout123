“””
utils/market_intelligence.py — Base de Conhecimento Completa do Agro Brasileiro
25+ CNAEs, 27 UFs, argumentos contra 6 concorrentes.
“””

DORES_POR_CNAE = {
# === GRÃOS ===
“0111”: {
“setor”: “Grãos (Soja, Milho, Trigo)”,
“dores”: [
“Gestão de múltiplas safras simultâneas (safra/safrinha/inverno)”,
“Controle de insumos com custos voláteis em dólar”,
“Rastreabilidade exigida por tradings (Cargill, Bunge, ADM, Dreyfus)”,
“Gestão de armazenagem, classificação e frete de escoamento”,
“Compliance Renovabio, créditos de carbono, EUDR”,
“Conciliação de contratos de hedge, barter e CPR”,
“Agricultura de precisão: mapas de produtividade, VRA, zonas de manejo”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “WMS”, “Financeiro”, “BI”, “Contratos”],
},
# === CANA-DE-AÇÚCAR ===
“0113”: {
“setor”: “Cana-de-Açúcar / Sucroenergético”,
“dores”: [
“CTT (Corte, Transporte, Transbordo) — 40%+ do custo operacional”,
“Gestão de moagem, mix açúcar/etanol/energia, CONSECANA”,
“RenovaBio: controle de CBIOs obrigatório e negociação em bolsa”,
“Manutenção pesada: colhedoras, treminhões, caldeiras, moendas”,
“Gestão de gente: safra emprega 3x mais que entressafra”,
“Cogeração de energia: venda de excedente à rede (CCEE)”,
“Controle de insumos de indústria (cal, enxofre, ácido sulfúrico)”,
],
“modulos_senior”: [“ERP Industrial”, “Manutenção de Ativos”, “RH/DP”, “Gestão Agrícola”, “Energia”],
},
# === ALGODÃO ===
“0115”: {
“setor”: “Algodão / Fibras”,
“dores”: [
“Beneficiamento: controle de algodoeira (pluma, caroço, línter)”,
“Rastreabilidade ABR (Algodão Brasileiro Responsável) e BCI”,
“Classificação HVI por fardo — integração com laboratório”,
“Logística: containers, portos, contratos de exportação”,
“Irrigação por pivôs centrais — custo energético e hídrico”,
“Manejo fitossanitário intensivo (bicudo, ramulária)”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “WMS”, “Qualidade”, “Manutenção”, “Exportação”],
},
# === HF / CULTURAS ESPECIAIS ===
“0119”: {
“setor”: “Hortifruticultura / Culturas Especiais”,
“dores”: [
“Perecibilidade: janela de colheita/venda curtíssima”,
“Rastreabilidade de alimentos exigida por GPA, Carrefour, Walmart”,
“MIP (Manejo Integrado de Pragas) intensivo e caderno de campo”,
“Gestão de câmaras frias, packing houses, classificação”,
“Mão de obra sazonal massiva — compliance trabalhista eSocial”,
“Certificações: GlobalGAP, Rainforest, orgânico”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “RH/DP”, “WMS”, “Qualidade”, “Rastreabilidade”],
},
# === CAFÉ ===
“0134”: {
“setor”: “Café (Arábica e Conilon)”,
“dores”: [
“Classificação por peneira, defeitos, tipo de bebida, lote”,
“Gestão de terreiros/secadores — qualidade depende da pós-colheita”,
“Rastreabilidade de origem para cafés especiais (UTZ, Fair Trade, 4C)”,
“Gestão de colheita mecanizada vs manual (topografia)”,
“Controle de pragas: broca, ferrugem, cercosporiose”,
“Irrigação por gotejamento em áreas de Cerrado”,
“Cupping e lotes de qualidade — precificação diferenciada”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “Qualidade”, “WMS”, “Rastreabilidade”, “Financeiro”],
},
# === CITRUS ===
“0131”: {
“setor”: “Citricultura (Laranja, Limão)”,
“dores”: [
“Controle de Greening (HLB) — maior ameaça fitossanitária do setor”,
“Gestão de pomares com ciclo de 15+ anos”,
“Integração com indústria de suco (Citrosuco, Cutrale)”,
“Logística de colheita manual — gestão de turmas”,
“Monitoramento de pragas: psilídeo, ácaro, leprose”,
“Irrigação e fertirrigação”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “RH/DP”, “Manutenção”, “Qualidade”],
},
# === ARROZ ===
“0112”: {
“setor”: “Arroz Irrigado”,
“dores”: [
“Gestão de lâmina d’água e bombeamento — custo energético altíssimo”,
“Beneficiamento: parboilização, polimento, classificação”,
“Gestão de barragens e outorgas de uso de água”,
“Logística de escoamento (RS, TO, MT)”,
“Controle de arroz vermelho e plantas daninhas resistentes”,
“Integração lavoura-pecuária em terras baixas”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “Industrial”, “Manutenção”, “Ambiental”],
},
# === FUMO ===
“0114”: {
“setor”: “Fumo / Tabaco”,
“dores”: [
“Integração com indústrias (Souza Cruz/BAT, Philip Morris, JTI)”,
“Classificação de folhas por qualidade, posição e cura”,
“Compliance com regulação sanitária e rastreabilidade”,
“Gestão de estufas de cura (energia)”,
“Mão de obra familiar — gestão de contratos de integração”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “Qualidade”, “Contratos”, “Rastreabilidade”],
},
# === PECUÁRIA CORTE ===
“0151”: {
“setor”: “Pecuária de Corte”,
“dores”: [
“Rastreabilidade individual (GTA, SISBOV, exportação EU/China)”,
“Gestão nutricional: confinamento, suplementação, dieta de terminação”,
“Controle reprodutivo: IATF, estação de monta, DEPs genéticos”,
“Gestão de pastagens: reforma, adubação, lotação, rotação”,
“Integração ILP/ILPF (lavoura-pecuária-floresta)”,
“Frigorífico: abate, rendimento de carcaça, tipificação, SIF/SIE”,
“Exportação: habilitação de plantas, cotas Hilton/USDA”,
],
“modulos_senior”: [“ERP Pecuária”, “Gestão de Rebanho”, “Manutenção”, “Financeiro”, “Exportação”],
},
# === PECUÁRIA LEITE ===
“0152”: {
“setor”: “Pecuária Leiteira”,
“dores”: [
“Gestão de qualidade do leite: CCS, CBT, gordura, proteína”,
“Controle reprodutivo e genético do rebanho”,
“Gestão de ordenha mecânica/robótica e manutenção”,
“Rastreabilidade de tanques de resfriamento”,
“Integração com laticínios e cooperativas”,
“Custo de nutrição: silagem, ração concentrada, volumoso”,
“IN77/IN76 — compliance de qualidade obrigatório”,
],
“modulos_senior”: [“ERP Pecuária”, “Gestão de Rebanho”, “Qualidade”, “Manutenção”],
},
# === AVICULTURA ===
“0155”: {
“setor”: “Avicultura (Frango de Corte / Postura)”,
“dores”: [
“Integração com abatedouros (BRF, Seara/JBS, Aurora, C.Vale)”,
“Gestão de lotes: conversão alimentar, mortalidade, GPD”,
“Ambiência: controle de temperatura/umidade dos aviários”,
“Biosseguridade: controle de Newcastle, Influenza, Salmonella”,
“Gestão de ração: formulação, fábrica, entrega nos integrados”,
“Logística de carregamento e apanha”,
],
“modulos_senior”: [“ERP Integração”, “Gestão de Lotes”, “Fábrica de Ração”, “Manutenção”],
},
# === SUINOCULTURA ===
“0154”: {
“setor”: “Suinocultura”,
“dores”: [
“Integração vertical: genética → UPL → terminação → abate”,
“Gestão de dejetos e compliance ambiental (outorgas)”,
“Biodigestores e geração de energia (biogás/biometano)”,
“Controle sanitário: PSC, PRRS, circovírus”,
“Gestão de ração e conversão alimentar por lote”,
“Rastreabilidade de granja a gôndola”,
],
“modulos_senior”: [“ERP Integração”, “Gestão de Lotes”, “Ambiental”, “Energia”, “Rastreabilidade”],
},
# === AQUICULTURA ===
“0322”: {
“setor”: “Aquicultura / Piscicultura”,
“dores”: [
“Gestão de tanques/viveiros: qualidade de água, biometria”,
“Controle de ração e conversão alimentar por tanque”,
“Rastreabilidade para exportação (tilápia, camarão)”,
“Compliance ambiental: outorgas, licenças IBAMA”,
“Logística de pescado fresco (cadeia fria)”,
“Sanidade: controle de patógenos (Streptococcus, vírus)”,
],
“modulos_senior”: [“ERP Aquicultura”, “Qualidade”, “Rastreabilidade”, “Ambiental”],
},
# === FLORESTAL / CELULOSE ===
“0210”: {
“setor”: “Silvicultura / Florestal / Celulose”,
“dores”: [
“Gestão de ciclo longo: 6-7 anos eucalipto, 15+ anos pinus”,
“Inventário florestal, cubagem, IMA, produtividade por clone”,
“Logística pesada: colheita mecanizada (Harvester/Forwarder)”,
“Compliance ambiental: APP, reserva legal, FSC/PEFC”,
“Manutenção de máquinas florestais pesadas”,
“Integração com fábricas de celulose, MDF, carvão”,
“Controle de incêndios florestais”,
],
“modulos_senior”: [“ERP Florestal”, “Manutenção Pesada”, “Ambiental”, “Logística”, “Industrial”],
},
# === BIOENERGIA ===
“3511”: {
“setor”: “Bioenergia / Biomassa / Etanol de Milho”,
“dores”: [
“Gestão de plantas industriais complexas (destilaria, caldeira, turbina)”,
“Controle de CBIOs (RenovaBio) e créditos de carbono”,
“Gestão de biomassa: bagaço, palha, cavaco, capim-elefante”,
“Manutenção de ativos industriais pesados”,
“Comercialização de energia: CCEE, contratos de longo prazo”,
“Etanol de milho: gestão de matéria-prima e DDG”,
],
“modulos_senior”: [“ERP Industrial”, “Manutenção”, “Energia”, “Ambiental”, “Comercialização”],
},
# === COOPERATIVAS ===
“generico_coop”: {
“setor”: “Cooperativa Agropecuária”,
“dores”: [
“Gestão cooperado-cooperativa: cotas, sobras, integralização”,
“Recebimento de grãos de milhares de cooperados”,
“Múltiplas unidades: armazéns, lojas, postos, agroindústria”,
“Compliance tributário cooperativista (ato cooperativo vs ato não-cooperativo)”,
“Gestão de insumos/revenda para cooperados”,
“Assembleia e governança cooperativista”,
],
“modulos_senior”: [“ERP Cooperativa”, “WMS”, “Varejo”, “Financeiro”, “RH/DP”, “BI”],
},
# === TRADING / ORIGINAÇÃO ===
“generico_trading”: {
“setor”: “Trading / Originação de Grãos”,
“dores”: [
“Gestão de contratos de compra e venda (CPR, forward, hedge)”,
“Logística multimodal: rodovia, ferrovia, hidrovia”,
“Controle de estoques em múltiplos armazéns/terminais”,
“Compliance cambial e documentação de exportação”,
“Gestão de risco: posição de estoque vs contratos futuros”,
“Classificação de grãos no recebimento”,
],
“modulos_senior”: [“ERP Contratos”, “WMS”, “Logística”, “Financeiro”, “Exportação”],
},
# === INSUMOS AGRÍCOLAS ===
“generico_insumos”: {
“setor”: “Revenda / Distribuição de Insumos Agrícolas”,
“dores”: [
“Gestão de crédito rural: CPR, Barter, troca-troca”,
“Estoque de defensivos: controle de validade, lote, receituário”,
“Logística de entrega na fazenda (last mile rural)”,
“Assistência técnica: RTVs (Representantes Técnicos de Vendas)”,
“Compliance: receituário agronômico, MAPA, IBAMA”,
“Sazonalidade extrema de vendas (pré-plantio)”,
],
“modulos_senior”: [“ERP Varejo”, “WMS”, “CRM”, “Financeiro”, “Logística”],
},
# === GENÉRICO ===
“generico_agro”: {
“setor”: “Agronegócio Geral”,
“dores”: [
“Integrar operações de campo com administrativo”,
“Planilhas substituindo ERP → risco operacional e fiscal”,
“Gestão de frota própria e manutenção de máquinas”,
“Compliance fiscal rural: Funrural, ICMS diferido, REINF, eSocial”,
“Falta de visibilidade de custos reais por talhão/safra/lote”,
“Gestão de contratos de parceria agrícola e arrendamento”,
“Gestão de gente no campo: turnos, sazonalidade, NRs”,
],
“modulos_senior”: [“ERP Gestão Agrícola”, “Financeiro”, “RH/DP”, “BI”, “Manutenção”],
},
}

# =============================================================================

# CONTEXTO REGIONAL — TODOS OS 27 UFs

# =============================================================================

CONTEXTO_REGIONAL = {
“MT”: {“nome”: “Mato Grosso”, “perfil”: “Maior produtor de grãos (soja, milho, algodão). Mega-operações 10k-100k+ ha. Alta mecanização.”, “desafios”: “Logística BR-163, armazenagem, distância dos portos. Expansão para Araguaia.”, “concorrentes_erp”: [“TOTVS Agro”, “SAP Rural”, “Datacoper”, “Siagri”]},
“PR”: {“nome”: “Paraná”, “perfil”: “Diversificado: grãos, frango, suínos, café. Cooperativismo fortíssimo (Coamo, C.Vale, Cocamar, Lar).”, “desafios”: “Integração cooperativa-cooperado, gestão multisite, Paranaguá.”, “concorrentes_erp”: [“TOTVS”, “Cooperativas com sistema próprio”, “Datacoper”]},
“RS”: {“nome”: “Rio Grande do Sul”, “perfil”: “Arroz irrigado, soja, pecuária, vinicultura. Cooperativismo forte.”, “desafios”: “Eventos climáticos extremos, irrigação, compliance cooperativo.”, “concorrentes_erp”: [“TOTVS”, “Cooperativas com ERP próprio”]},
“GO”: {“nome”: “Goiás”, “perfil”: “Grãos, cana, pecuária, etanol de milho. Muitas usinas.”, “desafios”: “Diversificação, irrigação por pivô, gestão de usinas.”, “concorrentes_erp”: [“TOTVS”, “Siagri”, “Datacoper”]},
“SP”: {“nome”: “São Paulo”, “perfil”: “Capital sucroenergético. HF, citricultura, café. Agroindústria forte.”, “desafios”: “Custo de terra alto, pressão urbana, compliance ambiental rigoroso.”, “concorrentes_erp”: [“SAP”, “TOTVS”, “Oracle”]},
“MS”: {“nome”: “Mato Grosso do Sul”, “perfil”: “Pecuária forte + grãos + celulose (Suzano, Eldorado). ILP em crescimento.”, “desafios”: “Fronteira agrícola, gestão pecuária + lavoura integrada, florestal.”, “concorrentes_erp”: [“TOTVS”, “Siagri”]},
“MG”: {“nome”: “Minas Gerais”, “perfil”: “Café (maior produtor), leite (maior bacia), grãos no Triângulo. Diversificado.”, “desafios”: “Topografia, muitas PMEs, gestão de qualidade de café, irrigação Cerrado.”, “concorrentes_erp”: [“TOTVS”, “Siagri”, “sistemas locais”]},
“BA”: {“nome”: “Bahia”, “perfil”: “MATOPIBA: algodão e soja no Oeste Baiano. Cacau no sul. Irrigação no São Francisco.”, “desafios”: “Irrigação Cerrado baiano, logística, regularização fundiária.”, “concorrentes_erp”: [“Siagri”, “TOTVS”]},
“TO”: {“nome”: “Tocantins”, “perfil”: “MATOPIBA: fronteira em expansão. Soja, arroz irrigado, pecuária.”, “desafios”: “Infraestrutura nascente, regularização, logística ferroviária (Norte-Sul).”, “concorrentes_erp”: [“Siagri”, “TOTVS”]},
“PI”: {“nome”: “Piauí”, “perfil”: “MATOPIBA: soja no Cerrado piauiense (Uruçuí, Bom Jesus). Crescimento acelerado.”, “desafios”: “Infraestrutura precária, distância de centros, regularização fundiária.”, “concorrentes_erp”: [“Siagri”]},
“MA”: {“nome”: “Maranhão”, “perfil”: “MATOPIBA: soja no Sul do Maranhão (Balsas). Terminal de grãos (São Luís).”, “desafios”: “Logística Norte-Sul, terminal portuário Itaqui, infraestrutura.”, “concorrentes_erp”: [“Siagri”, “TOTVS”]},
“SC”: {“nome”: “Santa Catarina”, “perfil”: “Suínos e aves (maior produtor). Cooperativismo forte (Aurora, Cooperalfa).”, “desafios”: “Integração avícola/suinícola, gestão de dejetos, biodigestores.”, “concorrentes_erp”: [“TOTVS”, “Cooperativas com ERP próprio”]},
“PA”: {“nome”: “Pará”, “perfil”: “Pecuária extensiva, dendê/palma, cacau, soja no Sul do Pará.”, “desafios”: “Compliance ambiental (desmatamento zero), regularização fundiária, rastreabilidade.”, “concorrentes_erp”: [“Siagri”]},
“RO”: {“nome”: “Rondônia”, “perfil”: “Pecuária (Vilhena, Ji-Paraná), café conilon, soja.”, “desafios”: “Logística, compliance ambiental, rastreabilidade de pecuária.”, “concorrentes_erp”: [“Siagri”]},
“AC”: {“nome”: “Acre”, “perfil”: “Pecuária, extrativismo, castanha. Fronteira agrícola emergente.”, “desafios”: “Logística extrema, compliance ambiental, mercado de carbono florestal.”, “concorrentes_erp”: []},
“AM”: {“nome”: “Amazonas”, “perfil”: “Extrativismo, piscicultura, dendê. Zona Franca.”, “desafios”: “Logística fluvial, compliance ambiental rigoroso.”, “concorrentes_erp”: []},
“AP”: {“nome”: “Amapá”, “perfil”: “Soja em expansão, extrativismo, piscicultura.”, “desafios”: “Infraestrutura mínima, compliance ambiental.”, “concorrentes_erp”: []},
“RR”: {“nome”: “Roraima”, “perfil”: “Pecuária, soja em lavrado (Cerrado). Fronteira novíssima.”, “desafios”: “Distância, infraestrutura, compliance ambiental.”, “concorrentes_erp”: []},
“CE”: {“nome”: “Ceará”, “perfil”: “Fruticultura irrigada (melão, banana, caju). Aquicultura (camarão).”, “desafios”: “Gestão hídrica, exportação de frutas, cadeia fria.”, “concorrentes_erp”: [“TOTVS”]},
“RN”: {“nome”: “Rio Grande do Norte”, “perfil”: “Fruticultura irrigada (melão, manga). Carcinicultura (camarão).”, “desafios”: “Gestão hídrica, exportação, certificação.”, “concorrentes_erp”: []},
“PB”: {“nome”: “Paraíba”, “perfil”: “Cana-de-açúcar, caprinocultura, sisal.”, “desafios”: “Pequena escala, associativismo, irrigação.”, “concorrentes_erp”: []},
“PE”: {“nome”: “Pernambuco”, “perfil”: “Cana-de-açúcar (Zona da Mata), fruticultura irrigada (Vale do São Francisco).”, “desafios”: “Gestão de usinas pequenas, irrigação, exportação de uva/manga.”, “concorrentes_erp”: [“TOTVS”]},
“AL”: {“nome”: “Alagoas”, “perfil”: “Cana-de-açúcar e pecuária leiteira.”, “desafios”: “Usinas em consolidação, gestão de CTT.”, “concorrentes_erp”: []},
“SE”: {“nome”: “Sergipe”, “perfil”: “Cana, citricultura, pecuária leiteira.”, “desafios”: “Pequena escala, diversificação.”, “concorrentes_erp”: []},
“RJ”: {“nome”: “Rio de Janeiro”, “perfil”: “Pecuária leiteira, HF (região serrana), aquicultura.”, “desafios”: “Custo de terra, pressão urbana, nichos de mercado.”, “concorrentes_erp”: [“TOTVS”]},
“ES”: {“nome”: “Espírito Santo”, “perfil”: “Café conilon (maior produtor), fruticultura (mamão, maracujá).”, “desafios”: “Topografia, manejo de café conilon, exportação via Vitória.”, “concorrentes_erp”: [“Siagri”]},
“DF”: {“nome”: “Distrito Federal”, “perfil”: “Horticultura periurbana, pesquisa (Embrapa).”, “desafios”: “Pequena escala, mercado local.”, “concorrentes_erp”: []},
}

# =============================================================================

# CONCORRENTES (6 principais)

# =============================================================================

ARGUMENTOS_CONCORRENCIA = {
“totvs”: {
“nome”: “TOTVS Agro (Protheus/RM/AgriManager)”,
“fraquezas”: [
“Customização cara e lenta — depende de fábrica de software”,
“Módulo agrícola é adaptação do ERP industrial, não nativo”,
“Interface defasada — produtores reclamam da usabilidade”,
“TCO alto com licenças perpétuas + consultoria + infra”,
“Suporte genérico — analistas não conhecem agro a fundo”,
],
“senior_vantagem”: [“Módulo agrícola nativo”, “Cloud-first”, “UX moderna”, “Especialistas agro no suporte”],
},
“sap”: {
“nome”: “SAP (S/4HANA / Business One)”,
“fraquezas”: [
“Complexidade absurda para operações agro”,
“Implementação: R$2M+ e 12-24 meses”,
“Poucos consultores SAP que entendem agro no Brasil”,
“Business One não escala para operações grandes”,
],
“senior_vantagem”: [“Deploy 3-6 meses”, “Custo 60-70% menor”, “Suporte local em português”],
},
“siagri”: {
“nome”: “Siagri (Agrowin)”,
“fraquezas”: [
“Focado em financeiro — módulos operacionais fracos”,
“Sem RH/DP robusto para 200+ funcionários”,
“Escalabilidade limitada para grupos multi-CNPJ”,
“Sem manutenção de ativos nativa”,
],
“senior_vantagem”: [“Suite completa: ERP+RH+Manutenção+BI”, “Multi-empresa nativo”, “eSocial robusto”],
},
“datacoper”: {
“nome”: “Datacoper (ERP Cooperativo)”,
“fraquezas”: [
“Focado em cooperativas — limitado para grupos privados”,
“Interface legada, modernização lenta”,
“Pouca presença fora do PR/SC”,
“Módulo industrial limitado”,
],
“senior_vantagem”: [“Atende cooperativas E grupos privados”, “Nacional”, “Industrial forte”],
},
“oracle”: {
“nome”: “Oracle (JD Edwards / NetSuite)”,
“fraquezas”: [
“JDE é legado — poucas consultorias no Brasil”,
“NetSuite não tem módulo agro nativo”,
“Custo alto de licenciamento e nuvem”,
“Suporte em inglês — barreira para operação de campo”,
],
“senior_vantagem”: [“Módulo agro nativo”, “Suporte 100% PT-BR”, “Custo acessível”],
},
“agrosmart”: {
“nome”: “Soluções pontuais (Agrosmart, Aegro, Solinftec)”,
“fraquezas”: [
“Resolvem só o campo — sem ERP, sem RH, sem financeiro”,
“Criam silos de dados que não se integram”,
“Não atendem compliance fiscal (eSocial, REINF, SPED)”,
“Não escalam para gestão de grupo econômico”,
],
“senior_vantagem”: [“Plataforma completa campo-a-escritório”, “Compliance fiscal integrado”, “Gestão de grupo”],
},
}

# =============================================================================

# HELPERS

# =============================================================================

def get_contexto_cnae(cnae: str) -> dict:
c4 = str(cnae)[:4] if cnae else “”
return DORES_POR_CNAE.get(c4, DORES_POR_CNAE[“generico_agro”])

def get_contexto_regional(uf: str) -> dict:
return CONTEXTO_REGIONAL.get(str(uf).upper(), {
“nome”: uf or “N/I”, “perfil”: “Sem perfil.”, “desafios”: “A investigar.”, “concorrentes_erp”: []})

def enriquecer_prompt_com_contexto(cnae: str = “”, uf: str = “”) -> str:
cc = get_contexto_cnae(cnae)
cr = get_contexto_regional(uf)
return f”””
=== INTELIGÊNCIA DE MERCADO (Base Senior) ===
SETOR: {cc[‘setor’]}
DORES DO SETOR:
{chr(10).join(f’  - {d}’ for d in cc[‘dores’])}
MÓDULOS RECOMENDADOS: {’, ’.join(cc.get(‘modulos_senior’, []))}

REGIÃO: {cr.get(‘nome’, ‘N/D’)}
PERFIL: {cr.get(‘perfil’, ‘N/D’)}
DESAFIOS: {cr.get(‘desafios’, ‘N/D’)}
CONCORRENTES ERP: {’, ’.join(cr.get(‘concorrentes_erp’, []))}
“””