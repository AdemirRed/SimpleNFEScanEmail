"""
Script para gerar executável do SimpleNFE
Usa PyInstaller para criar um .exe standalone
"""
import os
import subprocess
import sys
from pathlib import Path

def install_pyinstaller():
    """Instala PyInstaller se necessário"""
    try:
        import PyInstaller
        print("✓ PyInstaller já está instalado")
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller instalado com sucesso")

def build_executable():
    """Gera o executável"""
    print("\n" + "="*60)
    print("Gerando executável SimpleNFE.exe")
    print("="*60 + "\n")
    
    # Diretório base
    base_dir = Path(__file__).parent
    
    # Comando PyInstaller
    cmd = [
        "pyinstaller",
        "--name=SimpleNFE",
        "--windowed",  # Sem console (aplicação GUI)
        "--onefile",   # Arquivo único
        "--icon=NONE", # Sem ícone (pode adicionar depois)
        "--add-data", f"{base_dir}/ui;ui",  # Inclui módulo ui
        "--add-data", f"{base_dir}/modules;modules",  # Inclui módulo modules
        "--hidden-import", "tkinter",
        "--hidden-import", "email",
        "--hidden-import", "imaplib",
        "--hidden-import", "xml.etree.ElementTree",
        "--hidden-import", "PyPDF2",
        "--hidden-import", "pdfminer",
        "--hidden-import", "pdfminer.high_level",
        "--hidden-import", "requests",
        "--collect-all", "tkinter",
        "--noconsole",  # Sem janela de console
        f"{base_dir}/app.py"
    ]
    
    print("Comando:", " ".join(cmd))
    print("\nExecutando PyInstaller...\n")
    
    try:
        # Remove builds anteriores
        import shutil
        if (base_dir / "build").exists():
            shutil.rmtree(base_dir / "build")
            print("✓ Diretório build anterior removido")
        if (base_dir / "dist").exists():
            shutil.rmtree(base_dir / "dist")
            print("✓ Diretório dist anterior removido")
        if (base_dir / "SimpleNFE.spec").exists():
            (base_dir / "SimpleNFE.spec").unlink()
            print("✓ Arquivo .spec anterior removido")
        
        print("\nCriando novo executável...\n")
        
        # Executa PyInstaller
        result = subprocess.run(cmd, cwd=base_dir, check=True)
        
        print("\n" + "="*60)
        print("✓ EXECUTÁVEL GERADO COM SUCESSO!")
        print("="*60)
        print(f"\nLocalização: {base_dir / 'dist' / 'SimpleNFE.exe'}")
        print("\nPara distribuir:")
        print("1. Copie o arquivo SimpleNFE.exe da pasta 'dist'")
        print("2. O executável é standalone (não precisa de Python instalado)")
        print("3. Na primeira execução, crie o config.json com suas credenciais")
        print("\nObservação: O executável pode ser grande (~50-100MB) pois")
        print("inclui o Python e todas as bibliotecas necessárias.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Erro ao gerar executável: {e}")
        print("\nTente instalar as dependências manualmente:")
        print("  pip install pyinstaller PyPDF2 pdfminer.six requests")
        return False
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        return False
    
    return True

def main():
    print("="*60)
    print("GERADOR DE EXECUTÁVEL - SimpleNFE")
    print("="*60)
    
    # Verifica Python
    print(f"\nVersão do Python: {sys.version}")
    
    # Instala PyInstaller
    install_pyinstaller()
    
    # Gera executável
    success = build_executable()
    
    if success:
        print("\n✓ Processo concluído!")
    else:
        print("\n✗ Processo falhou. Verifique os erros acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
