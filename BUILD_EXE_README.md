# Como Gerar o Executável SimpleNFE.exe

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dependências do projeto** instaladas:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Método 1: Usar o Script Automático (Recomendado)

Execute o script que faz tudo automaticamente:

```bash
python build_exe.py
```

O script irá:
- ✓ Verificar e instalar PyInstaller se necessário
- ✓ Limpar builds anteriores
- ✓ Gerar o executável
- ✓ Criar SimpleNFE.exe na pasta `dist/`

## 🛠️ Método 2: Usar PyInstaller Manualmente

### Passo 1: Instalar PyInstaller
```bash
pip install pyinstaller
```

### Passo 2: Gerar executável usando o arquivo .spec
```bash
pyinstaller SimpleNFE.spec
```

**OU** usando comando direto:
```bash
pyinstaller --name=SimpleNFE --windowed --onefile --noconsole app.py
```

## 📦 Resultado

Após a execução bem-sucedida, você encontrará:

```
SimpleNFE/
├── dist/
│   └── SimpleNFE.exe  ← SEU EXECUTÁVEL AQUI!
├── build/             (pode deletar)
└── SimpleNFE.spec     (arquivo de configuração)
```

## 📤 Distribuição

### O que distribuir:
- ✓ `SimpleNFE.exe` (arquivo único standalone)
- ✓ Opcional: `config.json` pré-configurado (sem senha!)
- ✓ Opcional: `README.md` com instruções para usuário final

### O executável:
- ✅ Não precisa de Python instalado no computador destino
- ✅ Inclui todas as bibliotecas necessárias
- ✅ Tamanho aproximado: 50-100 MB
- ✅ Funciona em qualquer Windows 10/11

## ⚙️ Configuração Inicial (Usuário Final)

Na primeira execução, o usuário deve:

1. Abrir o programa (pode demorar alguns segundos na primeira vez)
2. Ir para aba "Configurações"
3. Preencher:
   - Servidor IMAP: `imap.gmail.com`
   - Porta: `993`
   - Email: `seu_email@gmail.com`
   - Senha de App: (gerar em https://myaccount.google.com/apppasswords)
   - URL do LM Studio: `http://localhost:1234` (se usar IA local)
4. Clicar em "Salvar Configurações"

O arquivo `config.json` será criado automaticamente no mesmo diretório do executável.

## 🐛 Solução de Problemas

### Erro: "Failed to execute script"
- Execute com console para ver erro: remova `--noconsole` do comando

### Executável muito grande
- Normal! Inclui Python completo e bibliotecas
- Para reduzir: use `--onedir` ao invés de `--onefile`

### Antivírus bloqueia o executável
- Normal com executáveis PyInstaller
- Adicione exceção no antivírus
- Ou assine digitalmente o executável (requer certificado)

### "ModuleNotFoundError" ao executar
- Adicione o módulo faltante em `hiddenimports` no arquivo `.spec`
- Ou use: `--hidden-import=nome_do_modulo`

## 🔧 Personalização

### Adicionar Ícone
1. Crie/obtenha um arquivo `.ico` (256x256 ou 512x512)
2. No arquivo `SimpleNFE.spec`, altere:
   ```python
   icon='caminho/para/icon.ico'
   ```
3. Ou no comando direto:
   ```bash
   pyinstaller --icon=icon.ico ...
   ```

### Reduzir Tamanho
Edite `SimpleNFE.spec` e adicione em `excludes`:
```python
excludes=[
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    # Adicione bibliotecas não usadas
]
```

### Versão com Console (para debug)
No arquivo `.spec`, mude:
```python
console=True  # Mostra janela de console
```

## 📊 Comparação de Métodos

| Método | Tamanho | Velocidade Inicialização | Facilidade Distribuição |
|--------|---------|-------------------------|------------------------|
| `--onefile` | ~50-100MB | Mais lento | ⭐⭐⭐⭐⭐ Arquivo único |
| `--onedir` | ~150-200MB | Mais rápido | ⭐⭐⭐ Pasta com vários arquivos |

## 🎯 Recomendação

Para distribuição: **Use `--onefile`** (método padrão)
- Mais fácil para o usuário (um arquivo só)
- Mais lento na inicialização (~5-10 segundos)
- Ideal para distribuição

Para desenvolvimento: **Use `--onedir`**
- Mais rápido para testar builds
- Inicialização instantânea
- Ocupa mais espaço

## 📝 Notas Importantes

1. **LM Studio**: O executável NÃO inclui o LM Studio. Para usar análise de PDF, o usuário deve:
   - Instalar LM Studio separadamente
   - Iniciar o servidor local na porta 1234
   - Configurar a URL no programa

2. **Config.json**: Criado automaticamente na mesma pasta do .exe

3. **Temp folder**: O programa cria pasta `temp/` para arquivos temporários

4. **Primeira execução**: Pode demorar 5-15 segundos (descompactando bibliotecas)

5. **Atualizações**: Para atualizar, gere novo .exe e distribua

## 🆘 Suporte

Se encontrar problemas:
1. Execute `python app.py` diretamente para verificar se funciona
2. Verifique se todas as dependências estão instaladas
3. Leia os erros no console (use `console=True` no build)
4. Verifique os logs em `build/SimpleNFE/warn-SimpleNFE.txt`
