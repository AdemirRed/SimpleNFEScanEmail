# 🚀 Guia Rápido - Gerar Executável SimpleNFE

## Método Mais Fácil (Windows)

### Opção 1: Duplo-clique no arquivo .bat
1. Localize o arquivo `build_exe.bat`
2. Clique duas vezes nele
3. Aguarde o processo terminar
4. Executável estará em `dist/SimpleNFE.exe`

### Opção 2: PowerShell/CMD
```bash
# Abra o PowerShell ou CMD na pasta do projeto
python build_exe.py
```

### Opção 3: Manual com PyInstaller
```bash
# Instalar PyInstaller
pip install pyinstaller

# Gerar executável
pyinstaller SimpleNFE.spec
```

## ⏱️ Tempo Estimado
- Primeira vez: 5-10 minutos (download de dependências)
- Próximas vezes: 2-3 minutos

## 📦 Resultado
```
dist/
└── SimpleNFE.exe  ← Seu executável standalone!
                     (50-100 MB)
```

## ✅ Pronto para Distribuir!
- Copie `SimpleNFE.exe` da pasta `dist/`
- Envie para qualquer PC Windows (10/11)
- Não precisa de Python instalado
- Funciona direto!

## 🎯 Teste Antes de Distribuir
1. Vá para pasta `dist/`
2. Execute `SimpleNFE.exe`
3. Configure na aba "Configurações"
4. Teste todas as funcionalidades

## ❓ Problemas?
Veja o arquivo `BUILD_EXE_README.md` para solução detalhada.

---

**Criado por:** Sistema SimpleNFE  
**Última atualização:** 17/11/2025
