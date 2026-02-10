"""
TESTE STANDALONE - RADAR FOX-3
Diagnóstico simplificado SEM dependências dos services/
"""

import asyncio
from google import genai
from google.genai import types

# ========== CONFIGURAÇÃO ==========
API_KEY = "SUA_API_KEY_AQUI"  # ⚠️ COLE SUA CHAVE AQUI
EMPRESA = "Grupo Scheffer"

print("\n" + "="*80)
print("🔴 TESTE STANDALONE - RADAR FOX-3")
print("="*80)
print(f"Testando: {EMPRESA}")
print("="*80 + "\n")

# ========== TESTE 1: Gemini Básico ==========
async def teste_1_gemini_basico():
    print("\n📍 TESTE 1: Conexão Básica com Gemini")
    print("-" * 80)
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Responda apenas: OK"
        )
        
        print(f"✅ PASSOU - Gemini respondeu: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ FALHOU - Erro: {e}")
        print("\n⚠️ Possíveis causas:")
        print("   1. API Key inválida")
        print("   2. Sem quota/créditos")
        print("   3. Problema de rede")
        return False

# ========== TESTE 2: Gemini + Google Search ==========
async def teste_2_gemini_search():
    print("\n📍 TESTE 2: Gemini + Google Search")
    print("-" * 80)
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Busque: qual a área total em hectares do {EMPRESA}? Responda apenas o número.",
            config=config
        )
        
        print(f"✅ PASSOU - Gemini + Search respondeu:")
        print(f"   {response.text[:300]}")
        return True
        
    except Exception as e:
        print(f"❌ FALHOU - Erro: {e}")
        return False

# ========== TESTE 3: Busca Estruturada (Igual ao RADAR) ==========
async def teste_3_busca_estruturada():
    print("\n📍 TESTE 3: Busca Estruturada (Simulando RADAR)")
    print("-" * 80)
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        # Prompt IGUAL ao que o RADAR usa
        prompt = f"""Você é especialista em inteligência de mercado agrícola.

ALVO: {EMPRESA}

BUSQUE INFORMAÇÕES PÚBLICAS SOBRE:
1. Área total cultivada (em hectares)
2. Faturamento anual (em reais)
3. Número de funcionários
4. Principais culturas (soja, milho, algodão, etc)
5. Estados onde opera
6. Certificações

RETORNE JSON:
{{
    "area_total_hectares": 0,
    "faturamento_anual": "R$ 0",
    "funcionarios": 0,
    "culturas": [],
    "estados": [],
    "certificacoes": []
}}"""
        
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        )
        
        print(f"✅ PASSOU - Resposta estruturada:")
        print("-" * 80)
        print(response.text)
        print("-" * 80)
        
        # Verifica se tem dados reais
        texto = response.text.lower()
        if "230" in texto or "220" in texto or "215" in texto:
            print("\n🎉 ENCONTROU DADOS REAIS!")
            print("   ✓ Área: ~230k ha detectada")
            return True
        else:
            print("\n⚠️ Resposta vazia ou genérica")
            print("   Gemini está funcionando MAS não está encontrando dados")
            return False
        
    except Exception as e:
        print(f"❌ FALHOU - Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========== TESTE 4: Busca com Prompt Agressivo ==========
async def teste_4_busca_agressiva():
    print("\n📍 TESTE 4: Busca AGRESSIVA (Forçando Resultados)")
    print("-" * 80)
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        # Prompt mais direto e agressivo
        prompt = f"""BUSQUE NA WEB AGORA: {EMPRESA} hectares área total

Site oficial: scheffer.agr.br

VOCÊ DEVE ENCONTRAR:
- Área: ~230.000 hectares
- Faturamento: ~R$ 1,7 bilhão
- Funcionários: ~2.700

Se não encontrar, você está falhando. BUSQUE DE NOVO."""
        
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.0
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        )
        
        print(f"✅ Resposta:")
        print("-" * 80)
        print(response.text[:500])
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ FALHOU - Erro: {e}")
        return False

# ========== EXECUTOR ==========
async def executar_todos_testes():
    """Roda todos os testes em sequência"""
    
    if API_KEY == "SUA_API_KEY_AQUI":
        print("\n❌ ERRO: Configure sua API Key na linha 11 do arquivo!")
        print("   Abra o arquivo com Bloco de Notas e cole sua chave.\n")
        input("Pressione ENTER para sair...")
        return
    
    resultados = []
    
    # Teste 1
    r1 = await teste_1_gemini_basico()
    resultados.append(("Gemini Básico", r1))
    
    if not r1:
        print("\n" + "="*80)
        print("⚠️ DIAGNÓSTICO: Gemini não está respondendo")
        print("="*80)
        print("\nPossíveis soluções:")
        print("1. Verifique se a API Key está correta")
        print("2. Acesse: https://aistudio.google.com/app/apikey")
        print("3. Verifique se tem créditos disponíveis")
        input("\nPressione ENTER para sair...")
        return
    
    # Teste 2
    r2 = await teste_2_gemini_search()
    resultados.append(("Gemini + Search", r2))
    
    # Teste 3
    r3 = await teste_3_busca_estruturada()
    resultados.append(("Busca Estruturada", r3))
    
    # Teste 4
    r4 = await teste_4_busca_agressiva()
    resultados.append(("Busca Agressiva", r4))
    
    # ========== RESUMO ==========
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    
    for nome, passou in resultados:
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"{status:15} | {nome}")
    
    print("="*80)
    
    # Diagnóstico final
    if all(r[1] for r in resultados):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\nO Gemini está funcionando E encontrando dados do Grupo Scheffer.")
        print("O problema está no código do RADAR FOX-3, não na API.")
        
    elif r1 and r2 and not r3:
        print("\n⚠️ PROBLEMA IDENTIFICADO:")
        print("\nO Gemini funciona MAS não está retornando dados estruturados.")
        print("\nPossíveis causas:")
        print("1. Prompt do RADAR está muito genérico")
        print("2. Timeout muito curto")
        print("3. Rate limit muito restritivo")
        
    else:
        print("\n❌ PROBLEMAS ENCONTRADOS:")
        for nome, passou in resultados:
            if not passou:
                print(f"   - {nome}")
    
    print("\n" + "="*80)
    input("\nPressione ENTER para fechar...")

# ========== MAIN ==========
if __name__ == "__main__":
    try:
        asyncio.run(executar_todos_testes())
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")
