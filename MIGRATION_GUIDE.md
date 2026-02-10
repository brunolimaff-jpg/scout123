# 🔄 Guia de Migração: v1.0 → v2.0

## ⚡ Mudanças Principais

### 1. Sistema de Validação Robusto

**ANTES (v1.0)**
```python
# Podia falhar com erro:
# "could not convert string to float: 'Não encontrado...'"
hectares = float(dados.get('hectares_total', 0))
```

**AGORA (v2.0)**
```python
from services.data_validator import safe_float

# NUNCA falha, sempre retorna valor seguro
hectares = safe_float(dados.get('hectares_total'), default=0.0)
```

### 2. Market Estimator

**ANTES**
```python
from services.market_estimator import calcular_sas
```

**AGORA**
```python
from services.market_estimator_v2 import calcular_sas
# Mesma assinatura, mas com validação interna robusta
```

### 3. Múltiplas Fontes de Dados

**NOVO em v2.0**
```python
from services.data_sources import data_sources

# Consulta múltiplas fontes governamentais
dados = data_sources.agregar_dados_empresa(
    cnpj=cnpj,
    nome=nome_empresa,
    municipio=municipio,
    uf=uf
)
```

### 4. Interface com Status em Tempo Real

**v1.0**: Loading com mensagens estáticas  
**v2.0**: 4 abas + progress bars + status cards

## 🛠️ Como Migrar Seus Scripts

### Se Você Usa Apenas a Interface

**Opção A: Trocar completamente**
```bash
# Renomear app antigo
mv app.py app_v1_backup.py

# Usar novo como principal
mv app_v2.py app.py

# Executar
streamlit run app.py
```

**Opção B: Rodar em paralelo**
```bash
# Terminal 1 - Versão antiga (porta 8501)
streamlit run app.py

# Terminal 2 - Versão nova (porta 8502)
streamlit run app_v2.py --server.port 8502
```

### Se Você Tem Integrações Customizadas

#### Passo 1: Atualizar Imports

```python
# ANTES
from services.market_estimator import calcular_sas

# DEPOIS
from services.market_estimator_v2 import calcular_sas
from services.data_validator import safe_float, safe_int, safe_str
```

#### Passo 2: Envolver Conversões com Validadores

```python
# ANTES (PODE FALHAR)
valor = float(raw_data.get('campo'))
quantidade = int(raw_data.get('qtd'))

# DEPOIS (NUNCA FALHA)
valor = safe_float(raw_data.get('campo'), default=0.0)
quantidade = safe_int(raw_data.get('qtd'), default=0)
```

#### Passo 3: Adicionar Tratamento de Confiança

```python
from services.data_validator import validator

# Validar confiança (0-1)
conf = validator.validate_confidence(dados.get('confianca', 0))

if conf < 0.5:
    print(f"⚠️ Dados com baixa confiança: {conf*100:.0f}%")
```

## 🔍 Checklist de Migração

- [ ] Backup do código atual
- [ ] Atualizar imports para usar `_v2` dos módulos
- [ ] Trocar `float()` direto por `safe_float()`
- [ ] Trocar `int()` direto por `safe_int()`
- [ ] Adicionar validação de confiança nos dados críticos
- [ ] Testar com casos que antes falhavam
- [ ] Atualizar documentação interna

## 🐛 Problemas Comuns

### Erro: Módulo não encontrado

```bash
# Certifique-se de estar no diretório correto
pwd  # Deve mostrar o caminho do projeto

# Reinstale dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: Ainda falha em conversão

```python
# Verifique se está usando a versão correta
import services.market_estimator_v2
print(services.market_estimator_v2.__file__)

# Se apontar para market_estimator.py (sem _v2),
# há problema de import
```

### Performance mais lenta

v2.0 prioriza **precisão sobre velocidade**. Se precisar de velocidade:

```python
# Em services/gemini_service.py
MODEL_NAME = "models/gemini-2.5-flash"  # Mais rápido
# Em vez de
MODEL_NAME = "models/gemini-2.5-pro"    # Mais preciso
```

## ➕ Funcionalidades Novas (Aproveite!)

### 1. Data Sources Manager

```python
from services.data_sources import data_sources

# Buscar no CAR/SICAR
car_data = data_sources.buscar_car_semas(cnpj, nome)

# Buscar no INCRA
incra_data = data_sources.buscar_imoveis_rurais_incra(cnpj)

# Buscar exportações
export_data = data_sources.buscar_exportacoes_comexstat(cnpj, nome)
```

### 2. Badges de Confiança na UI

```python
# Agora cada dado mostra nível de confiança visual
st.markdown(format_confidence(0.85), unsafe_allow_html=True)
# Exibe: [ALTA (85%)]
```

### 3. Pipeline Status Detalhado

Acesse a aba "PIPELINE STATUS" para ver:
- Tempo de cada etapa
- Status (success/warning/error)
- Detalhes específicos

## 🔙 Reverter para v1.0

Se precisar voltar:

```bash
# Restaurar app antigo
mv app.py app_v2_backup.py
mv app_v1_backup.py app.py

# Executar versão antiga
streamlit run app.py
```

## 📞 Suporte

Problemas na migração?

1. **Revise o README_V2.md**: Documentação completa
2. **Consulte issues**: https://github.com/brunolimaff-jpg/scout123/issues
3. **Abra nova issue**: Com template de bug report

---

**✅ Após migração bem-sucedida**

```bash
# Teste com caso que antes falhava
python -c "
from services.data_validator import safe_float
print(safe_float('Não encontrado'))  # Deve imprimir: 0.0
print('Migração OK!')
"
```

**Bem-vindo à v2.0! 🎉**
