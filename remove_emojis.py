"""
remove_emojis.py
Remove todos os emojis dos arquivos .py no diretório services/

USO:
1. Salve este script na raiz do projeto
2. Execute: python remove_emojis.py
3. Commit e push as mudanças
"""
import re
import os
from pathlib import Path

def remove_emojis(text):
    """Remove todos os emojis de um texto."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # símbolos & pictogramas
        u"\U0001F680-\U0001F6FF"  # transporte & símbolos
        u"\U0001F1E0-\U0001F1FF"  # bandeiras
        u"\U00002700-\U000027BF"  # dingbats
        u"\U0001F900-\U0001F9FF"  # suplementos
        u"\U00002600-\U000026FF"  # símbolos diversos
        u"\U00002B50"              # estrela
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

def clean_file(filepath):
    """Remove emojis de um arquivo Python."""
    print(f"Processando: {filepath}")
    
    try:
        # Lê arquivo
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove emojis
        cleaned = remove_emojis(content)
        
        # Verifica se houve mudança
        if content != cleaned:
            # Salva arquivo limpo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            print(f"  ✓ Emojis removidos!")
            return True
        else:
            print(f"  - Nenhum emoji encontrado")
            return False
            
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        return False

def main():
    """Processa todos os arquivos .py no projeto."""
    print("=" * 60)
    print("REMOVEDOR DE EMOJIS - RADAR FOX-3")
    print("=" * 60)
    print()
    
    # Diretórios a processar
    directories = ['services', 'utils', '.']
    
    files_processed = 0
    files_modified = 0
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        print(f"\n📁 Processando diretório: {directory}/")
        print("-" * 60)
        
        # Procura arquivos .py
        if directory == '.':
            files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'remove_emojis.py']
        else:
            files = [f for f in os.listdir(directory) if f.endswith('.py')]
        
        for filename in files:
            filepath = os.path.join(directory, filename) if directory != '.' else filename
            files_processed += 1
            
            if clean_file(filepath):
                files_modified += 1
    
    print()
    print("=" * 60)
    print(f"RESUMO:")
    print(f"  - Arquivos processados: {files_processed}")
    print(f"  - Arquivos modificados: {files_modified}")
    print("=" * 60)
    print()
    
    if files_modified > 0:
        print("✅ PRÓXIMOS PASSOS:")
        print("   1. git add .")
        print("   2. git commit -m 'fix: remove emojis para compatibilidade Streamlit Cloud'")
        print("   3. git push")
    else:
        print("✅ Nenhum emoji encontrado! Projeto já está limpo.")

if __name__ == "__main__":
    main()
