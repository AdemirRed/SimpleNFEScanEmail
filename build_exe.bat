@echo off
chcp 65001 >nul
echo ================================================================
echo           GERADOR DE EXECUTÁVEL - SimpleNFE
echo ================================================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado!
    echo Instale Python 3.8+ de: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verifica se pip está disponível
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pip não encontrado!
    pause
    exit /b 1
)

echo [OK] pip encontrado
echo.

REM Instala PyInstaller se necessário
echo Verificando PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller não encontrado. Instalando...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
    echo [OK] PyInstaller instalado
) else (
    echo [OK] PyInstaller já instalado
)
echo.

REM Remove builds anteriores
echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SimpleNFE.spec del /q SimpleNFE.spec
echo [OK] Builds anteriores removidos
echo.

REM Cria icone se nao existir
if not exist icon.ico (
    echo Criando icone...
    python create_icon.py
    if errorlevel 1 (
        echo [AVISO] Falha ao criar icone. Continuando sem icone.
    ) else (
        echo [OK] Icone criado
    )
) else (
    echo [OK] Icone ja existe
)
echo.

REM Gera o executável
echo ================================================================
echo Gerando executavel (isso pode demorar alguns minutos)...
echo ================================================================
echo.

echo Gerando versao SEM console (para usuarios finais)...

REM Define parametro do icone
set ICON_PARAM=
if exist icon.ico (
    set ICON_PARAM=--icon=icon.ico
    echo Usando icone: icon.ico
)

pyinstaller --name=SimpleNFE ^
    --windowed ^
    --onefile ^
    --noconsole ^
    %ICON_PARAM% ^
    --add-data "ui;ui" ^
    --add-data "modules;modules" ^
    --hidden-import=tkinter ^
    --hidden-import=email ^
    --hidden-import=imaplib ^
    --hidden-import=xml.etree.ElementTree ^
    --hidden-import=PyPDF2 ^
    --hidden-import=pdfminer ^
    --hidden-import=requests ^
    --hidden-import=cryptography ^
    --hidden-import=PIL ^
    app.py

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar executavel!
    echo Verifique os erros acima.
    pause
    exit /b 1
)

echo.
echo Gerando versao COM console (para debug)...
pyinstaller --name=SimpleNFE-Debug ^
    --onefile ^
    --console ^
    %ICON_PARAM% ^
    --add-data "ui;ui" ^
    --add-data "modules;modules" ^
    --hidden-import=tkinter ^
    --hidden-import=email ^
    --hidden-import=imaplib ^
    --hidden-import=xml.etree.ElementTree ^
    --hidden-import=PyPDF2 ^
    --hidden-import=pdfminer ^
    --hidden-import=requests ^
    --hidden-import=cryptography ^
    --hidden-import=PIL ^
    app.py

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar executável!
    echo Verifique os erros acima.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo           EXECUTAVEIS GERADOS COM SUCESSO!
echo ================================================================
echo.
echo Localizacao: %CD%\dist\
echo.
echo Arquivos gerados:
echo   1. SimpleNFE.exe - Versao final (SEM console)
echo   2. SimpleNFE-Debug.exe - Versao debug (COM console para ver erros)
echo.
echo Para testar: va para a pasta 'dist' e execute SimpleNFE.exe
echo Se encontrar erros: use SimpleNFE-Debug.exe para ver as mensagens
echo.
echo Observacoes:
echo - O executavel pode ser grande (50-100 MB)
echo - Inclui Python e todas as bibliotecas
echo - Nao precisa de Python instalado no computador destino
echo - Na primeira execucao, pode demorar alguns segundos
echo.
echo Para distribuir: use SimpleNFE.exe (sem console)
echo Para debug: use SimpleNFE-Debug.exe (mostra erros no console)
echo.
echo ================================================================

pause
