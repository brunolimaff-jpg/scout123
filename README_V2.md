# 📡 RADAR FOX-3 v2.0 | Intelligence System

> **Sistema de inteligência para prospecção de grandes produtores rurais no agronegócio**

## ⚡ O que há de novo na v2.0

### 🛡️ Correções Críticas
- **✅ FIX:** Resolvido erro `could not convert string to float` que causava crashes
- **✅ Sistema de validação defensiva**: NUNCA mais falhará em conversões de tipo
- **✅ Tratamento robusto**: Todos os campos numéricos com fallback seguro

### 🎯 Qualidade de Dados
- **🌐 Múltiplas fontes governamentais**: CAR/SICAR, INCRA, CVM, B3, ComexStat, MAPA, IBGE
- **🔍 Validação cruzada**: Dados só são aceitos após confirmação
- **⛔ Zero estimações**: Preferência por "N/D" em vez de valores inventados
- **📊 Indicadores de confiança**: Cada dado possui score de confiabilidade

### 🧠 Modelo de IA Aprimorado
- **Gemini 2.5 Pro** (1M tokens + thinking mode)
- Análise mais profunda e contextual
- Raciocínio avançado para insights estratégicos

### 👀 UX Completamente Renovado
- **Status em tempo real**: Cada etapa do pipeline é visível
- **Progress bar detalhado**: Acompanhe o progresso passo a passo
- **4 abas organizadas**: Radar Display, Pipeline Status, Raw Intel, Data Sources
- **Cards de status**: Visual claro do que foi encontrado
- **Badges de confiança**: Identifique rapidamente a qualidade dos dados

## 🚀 Instalação

### Pré-requisitos
```bash
Python 3.9+
Gemini API Key (gratuita em https://aistudio.google.com/app/apikey)
```

### 1. Clone o repositório
```bash
git clone https://github.com/brunolimaff-jpg/scout123.git
cd scout123
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure a API Key

**Opção A: Via arquivo de secrets (recomendado para Streamlit Cloud)**
```bash
mkdir .streamlit
echo '[secrets]' > .streamlit/secrets.toml
echo 'GEMINI_API_KEY = "sua-chave-aqui"' >> .streamlit/secrets.toml
```

**Opção B: Via interface** (insira durante o uso)

### 4. Execute a aplicação

**Versão 2.0 (Recomendada)**
```bash
streamlit run app_v2.py
```

**Versão Original**
```bash
streamlit run app.py
```

## 📚 Como Usar

### 1️⃣ Acesse a interface
Abra o navegador em `http://localhost:8501`

### 2️⃣ Insira as coordenadas do alvo
- **Nome da Empresa**: Ex: "GRUPO SCHEFFER", "SLC AGRÍCOLA"
- **CNPJ (opcional)**: Para busca mais precisa

### 3️⃣ Dispare o FOX-3
Clique no botão **🦊 FOX-3 DISPARAR**

### 4️⃣ Acompanhe o progresso
O sistema executa 10 etapas:

1. **📋 Consulta CNPJ** - Validação na Receita Federal
2. **🛰️ Recon Operacional** - Hectares, culturas, fazendas
3. **💰 Sniper Financeiro** - Capital, movimentações, CRAs
4. **🔗 Cadeia de Valor** - Clientes, fornecedores, exportação
5. **🏛️ Grupo Econômico** - Estrutura corporativa
6. **📡 Intel de Mercado** - Notícias, concorrentes, oportunidades
7. **👔 Profiler de Decisores** - Quem toma as decisões
8. **💻 Tech Stack** - ERPs, nível de maturidade TI
9. **🧠 Análise Estratégica** - Insights profundos com IA
10. **✅ Quality Gate** - Validação final da qualidade

### 5️⃣ Analise os resultados

**Aba RADAR DISPLAY**
- Score SAS (0-1000 pontos)
- Tier de classificação (Hunter-Killer, High-Value, Medium, Low-Priority)
- Métricas operacionais e financeiras
- Análise estratégica formatada

**Aba PIPELINE STATUS**
- Status detalhado de cada etapa
- Tempo de execução
- Badges de confiança

**Aba RAW INTEL**
- JSON completo com todos os dados extraídos

**Aba DATA SOURCES**
- Lista de fontes consultadas
- Status de cada integração

### 6️⃣ Exporte o relatório
Clique em **📥 BAIXAR RELATÓRIO (CSV)** para download

## 📊 Sistema de Pontuação SAS

### Score Total: 0-1000 pontos

| Categoria | Peso | Critérios |
|-----------|------|----------|
| **Tamanho & Complexidade** | 300 pts | Hectares, funcionários, número de fazendas |
| **Sofisticação Operacional** | 250 pts | Diversificação, verticalização, expansão geográfica |
| **Saúde Financeira** | 200 pts | Capital social, faturamento, FIAGROs, CRAs |
| **Posicionamento de Mercado** | 150 pts | Exportação, certificações, grupo econômico |
| **Maturidade Organizacional** | 100 pts | Estrutura de decisão, TI, natureza jurídica |

### Tiers de Classificação

- **🎯 HUNTER-KILLER (750-1000)**: Alvo prioritário - Operação de grande porte com alta sofisticação
- **🔵 HIGH-VALUE (500-749)**: Alto valor - Estrutura robusta com potencial significativo
- **🟡 MEDIUM (300-499)**: Médio porte - Operação estabelecida
- **⚪ LOW-PRIORITY (0-299)**: Baixa prioridade - Pequeno porte ou dados insuficientes

## 🛠️ Arquitetura Técnica

### Módulos Principais

```
scout123/
├── app_v2.py                    # Interface principal (v2.0)
├── app.py                       # Interface original
├── scout_types.py               # Tipos e estruturas de dados
├── services/
│   ├── data_validator.py        # ✨ Validação defensiva (NOVO)
│   ├── market_estimator_v2.py   # ✨ Score SAS robusto (NOVO)
│   ├── data_sources.py          # ✨ Integrações gov (NOVO)
│   ├── dossier_orchestrator.py  # Pipeline principal
│   ├── gemini_service.py        # Agents de IA
│   ├── cnpj_service.py          # Consulta Receita Federal
│   ├── cache_service.py         # Cache de requisições
│   └── quality_gate.py          # Validação de qualidade
└── utils/
    ├── market_intelligence.py   # Contexto de mercado
    └── pdf_export.py            # Exportação PDF
```

### Novos Módulos v2.0

#### `data_validator.py`
```python
# Conversão segura NUNCA falha
from services.data_validator import safe_float, safe_int, safe_str

# Exemplo
valor = safe_float("Não encontrado", default=0.0)  # Retorna 0.0
valor = safe_float("R$ 1.500.000,00")  # Retorna 1500000.0
```

#### `market_estimator_v2.py`
```python
# Cálculo do SAS Score com validação
from services.market_estimator_v2 import calcular_sas

sas_result = calcular_sas(dados_empresa)
print(f"Score: {sas_result.score}")
print(f"Tier: {sas_result.tier.value}")
```

#### `data_sources.py`
```python
# Agrega dados de múltiplas fontes
from services.data_sources import data_sources

dados = data_sources.agregar_dados_empresa(
    cnpj="12345678000190",
    nome="Empresa Exemplo",
    municipio="Cuiabá",
    uf="MT"
)
```

## 🌐 Fontes de Dados Integradas

### Fontes Governamentais

| Fonte | Tipo | Status | Dados |
|-------|------|--------|-------|
| **CAR/SICAR** | Oficial | ⚠️ Requer credenciais | Áreas rurais, coordenadas geográficas |
| **INCRA SNCR** | Oficial | ⚠️ Requer autenticação gov.br | Imóveis rurais cadastrados |
| **Receita Federal** | Oficial | ✅ Implementado | CNPJ, QSA, capital social |
| **CVM** | Oficial | 🔄 Em desenvolvimento | Dados de empresas de capital aberto |
| **B3/CETIP** | Oficial | 🔄 Em desenvolvimento | CRAs emitidos |
| **ComexStat** | Oficial | 🔄 Planejado | Exportações |
| **MAPA** | Oficial | 🔄 Planejado | Certificações sanitárias |
| **IBGE** | Oficial | ✅ Implementado | Contexto regional |

### APIs de Inteligência

- **Gemini 2.5 Pro**: Análise de linguagem natural
- **Google News RSS**: Notícias recentes
- **LinkedIn API**: Estrutura organizacional (requer chave oficial)

## 🔧 Configuração Avançada

### Trocar Modelo de IA

Edite `services/gemini_service.py`:

```python
# Opções disponíveis:
MODEL_NAME = "models/gemini-2.5-pro"           # Recomendado (1M tokens, thinking)
MODEL_NAME = "models/gemini-2.5-flash"        # Mais rápido
MODEL_NAME = "models/gemini-3-pro-preview"    # Experimental
```

### Ajustar Timeouts

```python
# services/request_queue.py
DEFAULT_TIMEOUT = 30  # segundos
MAX_RETRIES = 3
```

### Habilitar Cache

```python
# services/cache_service.py
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1 hora
```

## ⚠️ Avisos Importantes

### Limitações Atuais

1. **APIs Governamentais**: Algumas fontes (CAR, INCRA) requerem credenciais oficiais não disponíveis publicamente
2. **Rate Limits**: Gemini API tem limite de requisições por minuto
3. **Dados Históricos**: Sistema foca em dados atuais, não mantém histórico

### Privacidade e Ética

- ⛔ Use apenas para fins legítimos de prospecção comercial
- ⛔ Respeite a LGPD ao manusear dados de pessoas físicas
- ⛔ Não compartilhe relatórios sem consentimento

## 🐛 Relatar Problemas

Encontrou um bug? Abra uma issue em:
https://github.com/brunolimaff-jpg/scout123/issues

### Template de Issue
```markdown
**Descrição do problema**
O que aconteceu?

**Para reproduzir**
1. Passo 1
2. Passo 2
3...

**Comportamento esperado**
O que deveria acontecer?

**Screenshots**
Se aplicável

**Ambiente**
- Versão: v2.0 ou v1.0
- Python: 3.x
- SO: Windows/Mac/Linux
```

## 🛣️ Roadmap

### v2.1 (Planejado)
- [ ] Integração completa com CAR/SICAR
- [ ] Integração completa com INCRA SNCR
- [ ] API REST para uso programático
- [ ] Exportação em PDF com gráficos

### v2.2 (Futuro)
- [ ] Módulo de comparação (side-by-side)
- [ ] Dashboard executivo
- [ ] Análise de séries temporais
- [ ] Alertas de mudanças (monitoramento)

## 👥 Créditos

**Desenvolvido por**: Bruno Lima  
**Especialização**: Soluções ERP/Gestão de Campo para Agronegócio  
**Localização**: Cuiabá, MT

## 📜 Licença

Uso interno e educacional. Para uso comercial, entre em contato.

---

**📡 RADAR FOX-3 v2.0** | Intelligence System  
*"Precision over Speed. Data over Estimates."*
